from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from warhammer_companion.domain.overlays import ToolkitReadiness

MISSION_PACK_SCHEMA_VERSION = "mission-pack/v0"

MissionCategory = Literal["primary"]
MissionMechanicsReadiness = Literal["source-pending"]
MissionSourceKind = Literal["official_layout_metadata", "public_sheet_candidate"]
MissionSourceRetrievalStatus = Literal["derived_local", "not_fetched"]
MissionSourceTrust = Literal["official_derived", "untrusted_candidate"]


@dataclass(frozen=True, slots=True)
class MissionSourceAnchor:
    source_ref_id: str
    anchor_id: str
    label: str
    page_number: int | None = None
    sheet_gid: str | None = None


@dataclass(frozen=True, slots=True)
class MissionSourceRef:
    source_ref_id: str
    label: str
    source_kind: MissionSourceKind
    trust: MissionSourceTrust
    retrieval_status: MissionSourceRetrievalStatus
    url: str | None = None
    sheet_id: str | None = None
    gid: str | None = None
    content_hash: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MissionRecord:
    mission_id: str
    label: str
    category: MissionCategory
    readiness: ToolkitReadiness
    source_ref_ids: tuple[str, ...]
    source_anchors: tuple[MissionSourceAnchor, ...]
    mechanics_readiness: MissionMechanicsReadiness
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MissionPack:
    pack_id: str
    label: str
    schema_version: str
    readiness: ToolkitReadiness
    source_ref_ids: tuple[str, ...]
    primary_missions: tuple[MissionRecord, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MissionPackPayload:
    source_refs: tuple[MissionSourceRef, ...]
    pack: MissionPack
