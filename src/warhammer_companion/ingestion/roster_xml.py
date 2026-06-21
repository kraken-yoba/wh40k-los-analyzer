from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from io import BytesIO

from warhammer_companion.domain.rosters import (
    CanonicalArmy,
    RosterCost,
    RosterImportBlockReason,
    RosterSelection,
)

DISALLOWED_XML_TOKENS = (
    b"<!DOCTYPE",
    b"<!doctype",
    b"<!ENTITY",
    b"<!entity",
    b"SYSTEM",
    b"PUBLIC",
    b"xi:include",
    b"XInclude",
    b"http://",
    b"https://",
    b"&xxe;",
    b"<![CDATA[",
)


@dataclass(frozen=True, slots=True)
class RosterXmlLimits:
    max_xml_bytes: int = 1024 * 512
    max_depth: int = 32


DEFAULT_XML_LIMITS = RosterXmlLimits()


@dataclass(frozen=True, slots=True)
class RosterXmlParseResult:
    army: CanonicalArmy | None
    block_reasons: tuple[RosterImportBlockReason, ...] = ()

    @property
    def is_blocked(self) -> bool:
        return bool(self.block_reasons)


def parse_roster_xml(
    xml_bytes: bytes,
    *,
    limits: RosterXmlLimits = DEFAULT_XML_LIMITS,
) -> RosterXmlParseResult:
    safety_reason = _unsafe_xml_reason(xml_bytes, limits=limits)
    if safety_reason is not None:
        return RosterXmlParseResult(None, (safety_reason,))
    namespace_safety_reason = _unsafe_namespace_reason(xml_bytes)
    if namespace_safety_reason is not None:
        return RosterXmlParseResult(None, (namespace_safety_reason,))
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        return RosterXmlParseResult(
            None,
            (
                RosterImportBlockReason(
                    reason_id="malformed-roster-xml",
                    detail=f"Roster XML is malformed: {exc}",
                ),
            ),
        )
    decoded_safety_reason = _unsafe_decoded_xml_reason(root)
    if decoded_safety_reason is not None:
        return RosterXmlParseResult(None, (decoded_safety_reason,))
    if _local_name(root.tag) != "roster":
        return RosterXmlParseResult(
            None,
            (
                RosterImportBlockReason(
                    reason_id="unexpected-roster-root",
                    detail="Roster XML root element must be roster.",
                ),
            ),
        )
    if _selection_depth_exceeds_limit(root, max_depth=limits.max_depth):
        return RosterXmlParseResult(
            None,
            (
                RosterImportBlockReason(
                    reason_id="roster-xml-too-deep",
                    detail="Roster XML selection nesting exceeds the maximum admitted depth.",
                ),
            ),
        )
    army = _canonical_army_from_root(root)
    return RosterXmlParseResult(army)


def _unsafe_xml_reason(
    xml_bytes: bytes,
    *,
    limits: RosterXmlLimits,
) -> RosterImportBlockReason | None:
    if len(xml_bytes) > limits.max_xml_bytes:
        return RosterImportBlockReason(
            reason_id="roster-xml-too-large",
            detail="Roster XML exceeds the maximum admitted byte size.",
        )
    if not _is_admitted_xml_encoding(xml_bytes):
        return RosterImportBlockReason(
            reason_id="unsupported-roster-xml-encoding",
            detail="Roster XML must be UTF-8 or ASCII for the Phase 4A safety gate.",
        )
    for token in DISALLOWED_XML_TOKENS:
        if token in xml_bytes:
            return RosterImportBlockReason(
                reason_id="unsafe-roster-xml",
                detail="Roster XML contains a disallowed DTD, entity, include, or URL token.",
            )
    if b"<!--" in xml_bytes or _contains_disallowed_processing_instruction(xml_bytes):
        return RosterImportBlockReason(
            reason_id="unsafe-roster-xml",
            detail="Roster XML contains comments or processing instructions.",
        )
    return None


def _unsafe_decoded_xml_reason(root: ET.Element) -> RosterImportBlockReason | None:
    for element in root.iter():
        values = (
            str(element.tag),
            *element.attrib.keys(),
            *element.attrib.values(),
            element.text or "",
            element.tail or "",
        )
        if any(_contains_url_scheme(value) for value in values):
            return RosterImportBlockReason(
                reason_id="unsafe-roster-xml",
                detail="Roster XML contains a decoded URL reference.",
            )
    return None


def _unsafe_namespace_reason(xml_bytes: bytes) -> RosterImportBlockReason | None:
    try:
        namespace_events = ET.iterparse(BytesIO(xml_bytes), events=("start-ns",))
        for _event, namespace_data in namespace_events:
            prefix, uri = namespace_data
            _prefix = str(prefix)
            namespace_uri = str(uri)
            if _contains_url_scheme(namespace_uri):
                return RosterImportBlockReason(
                    reason_id="unsafe-roster-xml",
                    detail="Roster XML contains a decoded URL namespace reference.",
                )
    except ET.ParseError as exc:
        return RosterImportBlockReason(
            reason_id="malformed-roster-xml",
            detail=f"Roster XML is malformed: {exc}",
        )
    return None


def _contains_url_scheme(value: str) -> bool:
    lowered = value.lower()
    return "http://" in lowered or "https://" in lowered


def _contains_disallowed_processing_instruction(xml_bytes: bytes) -> bool:
    stripped = xml_bytes.lstrip()
    first_pi = stripped.find(b"<?")
    if first_pi < 0:
        return False
    if first_pi > 0:
        return True
    lowered = stripped[:16].lower()
    if not lowered.startswith(b"<?xml"):
        return True
    if len(stripped) > 5 and stripped[5:6] not in (b" ", b"\t", b"\r", b"\n"):
        return True
    declaration_end = stripped.find(b"?>")
    if declaration_end < 0:
        return True
    return b"<?" in stripped[declaration_end + 2 :]


def _is_admitted_xml_encoding(xml_bytes: bytes) -> bool:
    if b"\x00" in xml_bytes:
        return False
    if xml_bytes.startswith((b"\xff\xfe", b"\xfe\xff")):
        return False
    head = xml_bytes[:256].lower()
    if b"encoding" not in head:
        return True
    return b'encoding="utf-8"' in head or b"encoding='utf-8'" in head


def _canonical_army_from_root(root: ET.Element) -> CanonicalArmy:
    first_force = _first_descendant(root, "force")
    roster_costs = _costs(root)
    selections_parent = _first_child(first_force, "selections") if first_force is not None else None
    selections = _child_selections(
        selections_parent,
        parent_path=f"roster/{_attr(first_force, 'id')}",
    )
    return CanonicalArmy(
        roster_id=_attr(root, "id"),
        name=_attr(root, "name"),
        game_system_id=_optional_attr(root, "gameSystemId"),
        game_system_name=_optional_attr(root, "gameSystemName"),
        catalogue_id=_optional_attr(first_force, "catalogueId"),
        catalogue_name=_optional_attr(first_force, "catalogueName"),
        source_format="battlescribe_ros_v0",
        selections=selections,
        costs=roster_costs,
    )


def _selection_depth_exceeds_limit(element: ET.Element, *, max_depth: int) -> bool:
    stack: list[tuple[ET.Element, int]] = [(element, 0)]
    while stack:
        current, depth = stack.pop()
        next_depth = depth + 1 if _local_name(current.tag) == "selection" else depth
        if next_depth > max_depth:
            return True
        stack.extend((child, next_depth) for child in current)
    return False


def _child_selections(
    parent: ET.Element | None,
    *,
    parent_path: str,
) -> tuple[RosterSelection, ...]:
    if parent is None:
        return ()
    selections: list[RosterSelection] = []
    for child in parent:
        if _local_name(child.tag) != "selection":
            continue
        raw_id = _attr(child, "id")
        source_path = f"{parent_path}/{raw_id}"
        child_selections_parent = _first_child(child, "selections")
        selections.append(
            RosterSelection(
                raw_id=raw_id,
                name=_attr(child, "name"),
                selection_type=_attr(child, "type"),
                source_path=source_path,
                costs=_costs(child),
                children=_child_selections(child_selections_parent, parent_path=source_path),
            )
        )
    return tuple(selections)


def _costs(element: ET.Element) -> tuple[RosterCost, ...]:
    costs_parent = _first_child(element, "costs")
    if costs_parent is None:
        return ()
    costs: list[RosterCost] = []
    for child in costs_parent:
        if _local_name(child.tag) != "cost":
            continue
        costs.append(
            RosterCost(
                raw_id=_attr(child, "id"),
                name=_attr(child, "name"),
                type_id=_attr(child, "typeId"),
                value=_attr(child, "value"),
            )
        )
    return tuple(costs)


def _first_descendant(element: ET.Element, local_name: str) -> ET.Element | None:
    for descendant in element.iter():
        if _local_name(descendant.tag) == local_name:
            return descendant
    return None


def _first_child(element: ET.Element | None, local_name: str) -> ET.Element | None:
    if element is None:
        return None
    for child in element:
        if _local_name(child.tag) == local_name:
            return child
    return None


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", maxsplit=1)[-1]
    return tag


def _attr(element: ET.Element | None, name: str) -> str:
    if element is None:
        return ""
    return element.attrib.get(name, "")


def _optional_attr(element: ET.Element | None, name: str) -> str | None:
    value = _attr(element, name)
    return value if value else None
