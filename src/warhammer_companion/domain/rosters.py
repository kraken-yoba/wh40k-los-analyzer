from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from warhammer_companion.domain.overlays import ToolkitWarning

RosterSourceKind = Literal["ros_xml", "rosz_archive"]
RosterImportFormat = Literal["battlescribe_ros_v0"]
RosterQuarantineStatus = Literal["accepted", "blocked"]

ROSTER_IMPORT_PARSER_VERSION = "roster-import/v0"
ROSTER_IMPORT_SOURCE_SCHEMA_VERSION = "roster-import-source/v0"


@dataclass(frozen=True, slots=True)
class RosterImportBlockReason:
    reason_id: str
    detail: str
    remediation: str | None = None
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RosterArchiveMember:
    path: str
    compressed_size: int
    uncompressed_size: int
    decompression_ratio: float


@dataclass(frozen=True, slots=True)
class RosterImportSource:
    filename: str
    source_kind: RosterSourceKind
    byte_size: int
    sha256: str
    parser_version: str = ROSTER_IMPORT_PARSER_VERSION
    schema_version: str = ROSTER_IMPORT_SOURCE_SCHEMA_VERSION
    quarantine_status: RosterQuarantineStatus = "accepted"
    selected_xml_member_path: str | None = None
    selected_xml_sha256: str | None = None
    archive_members: tuple[RosterArchiveMember, ...] = ()
    warnings: tuple[ToolkitWarning, ...] = ()
    block_reasons: tuple[RosterImportBlockReason, ...] = ()


@dataclass(frozen=True, slots=True)
class RosterCost:
    raw_id: str
    name: str
    type_id: str
    value: str


@dataclass(frozen=True, slots=True)
class RosterSelection:
    raw_id: str
    name: str
    selection_type: str
    source_path: str
    costs: tuple[RosterCost, ...] = ()
    children: tuple[RosterSelection, ...] = ()

    def flattened(self) -> tuple[RosterSelection, ...]:
        flattened: list[RosterSelection] = [self]
        for child in self.children:
            flattened.extend(child.flattened())
        return tuple(flattened)


@dataclass(frozen=True, slots=True)
class CanonicalArmy:
    roster_id: str
    name: str
    game_system_id: str | None
    game_system_name: str | None
    catalogue_id: str | None
    catalogue_name: str | None
    source_format: RosterImportFormat
    selections: tuple[RosterSelection, ...]
    costs: tuple[RosterCost, ...] = ()
    source_ref_ids: tuple[str, ...] = ()

    def flattened_selections(self) -> tuple[RosterSelection, ...]:
        flattened: list[RosterSelection] = []
        for selection in self.selections:
            flattened.extend(selection.flattened())
        return tuple(flattened)


@dataclass(frozen=True, slots=True)
class RosterImportPayload:
    source: RosterImportSource
    army: CanonicalArmy | None
