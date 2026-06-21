from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from io import BytesIO

from warhammer_companion.domain.rosters import (
    CanonicalArmy,
    RosterCost,
    RosterImportBlockReason,
    RosterSelection,
    RosterSnapshotCharacteristic,
    RosterSnapshotProfile,
    RosterSnapshotRule,
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
    max_element_count: int = 2048
    max_element_depth: int = 64
    max_attributes_per_element: int = 32
    max_text_characters: int = 2048
    max_profiles_per_selection: int = 64
    max_rules_per_selection: int = 128
    max_characteristics_per_profile: int = 64
    max_snapshot_value_chars: int = 64


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
    document_structure_reason = _document_structure_reason(root, limits=limits)
    if document_structure_reason is not None:
        return RosterXmlParseResult(None, (document_structure_reason,))
    force_shape_reason = _unsupported_force_shape_reason(root)
    if force_shape_reason is not None:
        return RosterXmlParseResult(None, (force_shape_reason,))
    snapshot_shape_reason = _snapshot_shape_reason(root, limits=limits)
    if snapshot_shape_reason is not None:
        return RosterXmlParseResult(None, (snapshot_shape_reason,))
    army = _canonical_army_from_root(root, limits=limits)
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


def _canonical_army_from_root(root: ET.Element, *, limits: RosterXmlLimits) -> CanonicalArmy:
    first_force = _roster_forces(root)[0]
    roster_costs = _costs(root)
    selections_parent = _first_child(first_force, "selections") if first_force is not None else None
    selections = _child_selections(
        selections_parent,
        parent_path=f"roster/{_attr(first_force, 'id')}",
        limits=limits,
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


def _document_structure_reason(
    root: ET.Element,
    *,
    limits: RosterXmlLimits,
) -> RosterImportBlockReason | None:
    stack: list[tuple[ET.Element, int]] = [(root, 0)]
    element_count = 0
    while stack:
        current, depth = stack.pop()
        element_count += 1
        if element_count > limits.max_element_count:
            return RosterImportBlockReason(
                reason_id="roster-xml-too-many-elements",
                detail="Roster XML exceeds the maximum admitted element count.",
            )
        if depth > limits.max_element_depth:
            return RosterImportBlockReason(
                reason_id="roster-xml-document-too-deep",
                detail="Roster XML document nesting exceeds the maximum admitted depth.",
            )
        if len(current.attrib) > limits.max_attributes_per_element:
            return RosterImportBlockReason(
                reason_id="roster-xml-too-many-attributes",
                detail="Roster XML contains an element with too many attributes.",
            )
        if any(
            len(str(name)) > limits.max_text_characters
            or len(str(value)) > limits.max_text_characters
            for name, value in current.attrib.items()
        ):
            return RosterImportBlockReason(
                reason_id="roster-xml-field-too-long",
                detail="Roster XML contains an attribute value that exceeds the admitted length.",
            )
        text_values = (current.text or "", current.tail or "")
        if any(len(value.strip()) > limits.max_text_characters for value in text_values):
            return RosterImportBlockReason(
                reason_id="roster-xml-field-too-long",
                detail="Roster XML contains text that exceeds the admitted length.",
            )
        stack.extend((child, depth + 1) for child in current)
    return None


def _unsupported_force_shape_reason(root: ET.Element) -> RosterImportBlockReason | None:
    forces = _roster_forces(root)
    if len(forces) == 1:
        return None
    return RosterImportBlockReason(
        reason_id="unsupported-roster-force-count",
        detail=(
            "Phase 4B roster indexing requires exactly one force; multi-force and zero-force "
            "rosters are blocked until force-aware indexing is implemented."
        ),
    )


def _snapshot_shape_reason(
    root: ET.Element,
    *,
    limits: RosterXmlLimits,
) -> RosterImportBlockReason | None:
    for selection in root.iter():
        if _local_name(selection.tag) != "selection":
            continue
        profiles = _direct_children(_first_child(selection, "profiles"), "profile")
        rules = _direct_children(_first_child(selection, "rules"), "rule")
        if len(profiles) > limits.max_profiles_per_selection:
            return RosterImportBlockReason(
                reason_id="roster-xml-too-many-profiles",
                detail="Roster XML contains too many embedded profiles in one selection.",
            )
        if len(rules) > limits.max_rules_per_selection:
            return RosterImportBlockReason(
                reason_id="roster-xml-too-many-rules",
                detail="Roster XML contains too many embedded rules in one selection.",
            )
        for rule in rules:
            if len(_description_text(rule)) > limits.max_text_characters:
                return RosterImportBlockReason(
                    reason_id="roster-xml-field-too-long",
                    detail=(
                        "Roster XML contains aggregate rule description text that exceeds the "
                        "admitted length."
                    ),
                )
        for profile in profiles:
            characteristics = _direct_children(
                _first_child(profile, "characteristics"),
                "characteristic",
            )
            if len(characteristics) > limits.max_characteristics_per_profile:
                return RosterImportBlockReason(
                    reason_id="roster-xml-too-many-characteristics",
                    detail="Roster XML contains too many embedded characteristics in one profile.",
                )
            for characteristic in characteristics:
                if len(_collapsed_text(characteristic)) > limits.max_text_characters:
                    return RosterImportBlockReason(
                        reason_id="roster-xml-field-too-long",
                        detail=(
                            "Roster XML contains aggregate characteristic text that exceeds the "
                            "admitted length."
                        ),
                    )
    return None


def _child_selections(
    parent: ET.Element | None,
    *,
    parent_path: str,
    limits: RosterXmlLimits,
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
                profiles=_profiles(child, selection_path=source_path, limits=limits),
                rules=_rules(child, selection_path=source_path),
                children=_child_selections(
                    child_selections_parent,
                    parent_path=source_path,
                    limits=limits,
                ),
            )
        )
    return tuple(selections)


def _profiles(
    selection: ET.Element,
    *,
    selection_path: str,
    limits: RosterXmlLimits,
) -> tuple[RosterSnapshotProfile, ...]:
    profiles_parent = _first_child(selection, "profiles")
    if profiles_parent is None:
        return ()
    profiles: list[RosterSnapshotProfile] = []
    for child in profiles_parent:
        if _local_name(child.tag) != "profile":
            continue
        raw_id = _attr(child, "id")
        source_path = f"{selection_path}/{raw_id}"
        profiles.append(
            RosterSnapshotProfile(
                raw_id=raw_id,
                name=_attr(child, "name"),
                type_id=_attr(child, "typeId"),
                type_name=_optional_attr(child, "typeName"),
                source_path=source_path,
                characteristics=_characteristics(
                    child,
                    profile_path=source_path,
                    limits=limits,
                ),
            )
        )
    return tuple(profiles)


def _characteristics(
    profile: ET.Element,
    *,
    profile_path: str,
    limits: RosterXmlLimits,
) -> tuple[RosterSnapshotCharacteristic, ...]:
    characteristics_parent = _first_child(profile, "characteristics")
    if characteristics_parent is None:
        return ()
    characteristics: list[RosterSnapshotCharacteristic] = []
    for child in characteristics_parent:
        if _local_name(child.tag) != "characteristic":
            continue
        raw_id = _attr(child, "id")
        value = _collapsed_text(child)
        stored_value = value if len(value) <= limits.max_snapshot_value_chars else None
        characteristics.append(
            RosterSnapshotCharacteristic(
                raw_id=raw_id,
                name=_attr(child, "name"),
                type_id=_attr(child, "typeId"),
                source_path=f"{profile_path}/{raw_id}",
                value=stored_value,
                value_sha256=_sha256_or_none(value),
                value_length=len(value),
            )
        )
    return tuple(characteristics)


def _rules(selection: ET.Element, *, selection_path: str) -> tuple[RosterSnapshotRule, ...]:
    rules_parent = _first_child(selection, "rules")
    if rules_parent is None:
        return ()
    rules: list[RosterSnapshotRule] = []
    for child in rules_parent:
        if _local_name(child.tag) != "rule":
            continue
        raw_id = _attr(child, "id")
        description = _description_text(child)
        rules.append(
            RosterSnapshotRule(
                raw_id=raw_id,
                name=_attr(child, "name"),
                source_path=f"{selection_path}/{raw_id}",
                description_sha256=_sha256_or_none(description),
                description_length=len(description),
            )
        )
    return tuple(rules)


def _roster_forces(root: ET.Element) -> tuple[ET.Element, ...]:
    return _direct_children(_first_child(root, "forces"), "force")


def _direct_children(element: ET.Element | None, local_name: str) -> tuple[ET.Element, ...]:
    if element is None:
        return ()
    return tuple(child for child in element if _local_name(child.tag) == local_name)


def _description_text(rule: ET.Element) -> str:
    description = _first_child(rule, "description")
    if description is None:
        return ""
    return _collapsed_text(description)


def _collapsed_text(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _sha256_or_none(value: str) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
