from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from warhammer_companion.domain.overlays import ToolkitReadiness, ToolkitWarning

RosterSourceKind = Literal["ros_xml", "rosz_archive"]
RosterImportFormat = Literal["battlescribe_ros_v0"]
RosterQuarantineStatus = Literal["accepted", "blocked"]
ProfileResolutionStatus = Literal[
    "resolved_exact",
    "resolved_alias",
    "resolved_manual",
    "ambiguous",
    "unresolved",
    "unsupported",
]
RosterEvidencePolicy = Literal["local_evidence"]
RosterEvidenceAuthority = Literal["not_source_authority"]
RosterPointsAuthority = Literal["not_official_points"]
RosterMechanicsAuthority = Literal["not_profile_resolution"]

ROSTER_IMPORT_PARSER_VERSION = "roster-import/v0"
ROSTER_IMPORT_SOURCE_SCHEMA_VERSION = "roster-import-source/v0"
ROSTER_SNAPSHOT_PROFILE_SCHEMA_VERSION = "roster-snapshot-profile-candidate/v0"


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
class RosterSnapshotCharacteristic:
    raw_id: str
    name: str
    type_id: str
    source_path: str
    value: str | None
    value_sha256: str | None
    value_length: int
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RosterSnapshotProfile:
    raw_id: str
    name: str
    type_id: str
    type_name: str | None
    source_path: str
    characteristics: tuple[RosterSnapshotCharacteristic, ...] = ()
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RosterSnapshotRule:
    raw_id: str
    name: str
    source_path: str
    description_sha256: str | None
    description_length: int
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RosterSelection:
    raw_id: str
    name: str
    selection_type: str
    source_path: str
    costs: tuple[RosterCost, ...] = ()
    profiles: tuple[RosterSnapshotProfile, ...] = ()
    rules: tuple[RosterSnapshotRule, ...] = ()
    children: tuple[RosterSelection, ...] = ()

    def flattened(self) -> tuple[RosterSelection, ...]:
        flattened: list[RosterSelection] = [self]
        for child in self.children:
            flattened.extend(child.flattened())
        return tuple(flattened)


@dataclass(frozen=True, slots=True)
class RosterSnapshotProfileCandidatePack:
    roster_id: str
    source_format: RosterImportFormat
    selected_xml_sha256: str | None
    pack_hash: str
    profiles: tuple[RosterSnapshotProfile, ...]
    rules: tuple[RosterSnapshotRule, ...]
    source_ref_ids: tuple[str, ...] = ()
    readiness: ToolkitReadiness = "estimated"
    source_policy: RosterEvidencePolicy = "local_evidence"
    authority: RosterEvidenceAuthority = "not_source_authority"
    schema_version: str = ROSTER_SNAPSHOT_PROFILE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class RosterProfileCandidate:
    selection_key: str
    selection_id: str
    selection_name: str
    selection_type: str
    source_path: str
    resolution_status: ProfileResolutionStatus
    profile_ids: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    cost_ids: tuple[str, ...] = ()
    source_ref_ids: tuple[str, ...] = ()
    source_policy: RosterEvidencePolicy = "local_evidence"
    points_authority: RosterPointsAuthority = "not_official_points"
    mechanics_authority: RosterMechanicsAuthority = "not_profile_resolution"


@dataclass(frozen=True, slots=True)
class RosterSelectionIndexEntry:
    selection_key: str
    parent_selection_key: str | None
    selection_id: str
    selection_name: str
    selection_type: str
    source_path: str
    depth: int
    sibling_ordinal: int
    child_count: int
    cost_count: int
    profile_count: int
    rule_count: int


@dataclass(frozen=True, slots=True)
class RosterSelectionTypeCount:
    selection_type: str
    count: int


@dataclass(frozen=True, slots=True)
class CanonicalRosterIndex:
    roster_id: str
    roster_name: str
    selection_count: int
    top_level_selection_count: int
    selection_type_counts: tuple[RosterSelectionTypeCount, ...]
    entries: tuple[RosterSelectionIndexEntry, ...]
    profile_candidates: tuple[RosterProfileCandidate, ...]
    source_ref_ids: tuple[str, ...] = ()


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
    roster_index: CanonicalRosterIndex | None = None
    snapshot_profile_pack: RosterSnapshotProfileCandidatePack | None = None
