from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping

from warhammer_companion.application.toolkit import ToolkitResult
from warhammer_companion.domain.missions import (
    MISSION_PACK_SCHEMA_VERSION,
    MissionPack,
    MissionPackPayload,
    MissionRecord,
    MissionSourceAnchor,
    MissionSourceRef,
)
from warhammer_companion.domain.models import OfficialLayoutMetadata
from warhammer_companion.domain.overlays import ToolkitAssumption, ToolkitWarning
from warhammer_companion.ingestion.official_layout_metadata import OFFICIAL_LAYOUT_PAGE_METADATA

MISSION_PACK_TOOLKIT_SCHEMA_VERSION = "mission-pack-toolkit/v0"
OFFICIAL_LAYOUT_SOURCE_REF_ID = "event-companion-layout-metadata"
PUBLIC_MISSION_SHEET_SOURCE_REF_ID = "public-mission-sheet-candidate"
PUBLIC_MISSION_SHEET_ID = "1vlRuvuiy6YOOPLmYyLEUfcGVpGL56aWWMA4iWh18Yuw"
PUBLIC_MISSION_SHEET_GID = "1565185881"
PUBLIC_MISSION_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    f"{PUBLIC_MISSION_SHEET_ID}/edit?gid={PUBLIC_MISSION_SHEET_GID}"
    f"#gid={PUBLIC_MISSION_SHEET_GID}"
)


def build_mission_pack_toolkit_result(
    metadata: Mapping[int, OfficialLayoutMetadata] = OFFICIAL_LAYOUT_PAGE_METADATA,
) -> ToolkitResult[MissionPackPayload]:
    source_refs = (_official_layout_source_ref(), _public_sheet_source_ref())
    primary_missions = _primary_missions_from_layout_metadata(metadata)
    warnings = (
        "Mission mechanics, scoring, action timing, and objective-control behavior are "
        "source-pending.",
        "The public mission sheet candidate is recorded as provenance only; it is not fetched, "
        "not parsed, and not ingested.",
    )
    source_ref_ids = tuple(source.source_ref_id for source in source_refs)
    pack = MissionPack(
        pack_id="mission-pack-pariah-nexus-skeleton",
        label="Mission Pack Skeleton",
        schema_version=MISSION_PACK_SCHEMA_VERSION,
        readiness="estimated",
        source_ref_ids=source_ref_ids,
        primary_missions=primary_missions,
        warnings=warnings,
    )
    input_hash = _mission_pack_hash(metadata)
    suffix = input_hash.removeprefix("sha256:")[:12]
    return ToolkitResult(
        result_id=f"estimated:mission-pack:{suffix}",
        tool_id="mission_pack",
        input_hash=input_hash,
        readiness="estimated",
        payload=MissionPackPayload(source_refs=source_refs, pack=pack),
        assumptions=(
            ToolkitAssumption(
                assumption_id="layout-labels-only",
                detail=(
                    "Primary mission records are derived only from existing short layout "
                    "metadata labels."
                ),
                source_ref_ids=(OFFICIAL_LAYOUT_SOURCE_REF_ID,),
            ),
        ),
        warnings=(
            ToolkitWarning(
                warning_id="mission-mechanics-source-pending",
                detail=warnings[0],
                source_ref_ids=source_ref_ids,
            ),
            ToolkitWarning(
                warning_id="public-sheet-not-ingested",
                detail=warnings[1],
                source_ref_ids=(PUBLIC_MISSION_SHEET_SOURCE_REF_ID,),
            ),
        ),
        source_ref_ids=source_ref_ids,
    )


def _primary_missions_from_layout_metadata(
    metadata: Mapping[int, OfficialLayoutMetadata],
) -> tuple[MissionRecord, ...]:
    anchors_by_label: dict[str, set[int]] = {}
    for page_number, record in sorted(metadata.items()):
        anchors_by_label.setdefault(record.first_player.primary_mission, set()).add(page_number)
        anchors_by_label.setdefault(record.second_player.primary_mission, set()).add(page_number)

    missions: list[MissionRecord] = []
    for label in sorted(anchors_by_label):
        anchors = tuple(
            MissionSourceAnchor(
                source_ref_id=OFFICIAL_LAYOUT_SOURCE_REF_ID,
                anchor_id=f"event-companion-page-{page_number}",
                label=f"Event Companion page {page_number}",
                page_number=page_number,
            )
            for page_number in sorted(anchors_by_label[label])
        )
        missions.append(
            MissionRecord(
                mission_id=f"primary-{_slugify(label)}",
                label=label,
                category="primary",
                readiness="estimated",
                source_ref_ids=(OFFICIAL_LAYOUT_SOURCE_REF_ID,),
                source_anchors=anchors,
                mechanics_readiness="source-pending",
                warnings=("Mission mechanics and scoring are source-pending.",),
            )
        )
    return tuple(missions)


def _official_layout_source_ref() -> MissionSourceRef:
    return MissionSourceRef(
        source_ref_id=OFFICIAL_LAYOUT_SOURCE_REF_ID,
        label="Event Companion layout metadata",
        source_kind="official_layout_metadata",
        trust="official_derived",
        retrieval_status="derived_local",
        warnings=(
            "Only short layout metadata labels and page anchors are represented in this slice.",
        ),
    )


def _public_sheet_source_ref() -> MissionSourceRef:
    return MissionSourceRef(
        source_ref_id=PUBLIC_MISSION_SHEET_SOURCE_REF_ID,
        label="Public mission sheet candidate",
        source_kind="public_sheet_candidate",
        trust="untrusted_candidate",
        retrieval_status="not_fetched",
        url=PUBLIC_MISSION_SHEET_URL,
        sheet_id=PUBLIC_MISSION_SHEET_ID,
        gid=PUBLIC_MISSION_SHEET_GID,
        content_hash=None,
        warnings=(
            "Public mission sheet metadata is recorded only as an untrusted candidate; it is "
            "not fetched and not ingested.",
        ),
    )


def _mission_pack_hash(metadata: Mapping[int, OfficialLayoutMetadata]) -> str:
    payload = {
        "metadata": [
            {
                "first_primary_mission": record.first_player.primary_mission,
                "layout_variant": record.layout_variant,
                "page_number": page_number,
                "second_primary_mission": record.second_player.primary_mission,
            }
            for page_number, record in sorted(metadata.items())
        ],
        "public_sheet": {
            "gid": PUBLIC_MISSION_SHEET_GID,
            "retrieval_status": "not_fetched",
            "sheet_id": PUBLIC_MISSION_SHEET_ID,
            "trust": "untrusted_candidate",
            "url": PUBLIC_MISSION_SHEET_URL,
        },
        "schema_version": MISSION_PACK_TOOLKIT_SCHEMA_VERSION,
        "tool_id": "mission_pack",
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _slugify(label: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return normalized or "unnamed"
