from __future__ import annotations

import hashlib
import json

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.semantics import SemanticsFreshnessState
from warhammer_companion.domain.terrain_semantics import TerrainSemanticsIndex

TERRAIN_SEMANTICS_TOOLKIT_SCHEMA_VERSION = "terrain-semantics-toolkit/v0"


def build_terrain_semantics_result(
    packet: MapPacket,
    *,
    source_ref_ids: tuple[str, ...] = (),
    source_pack_version: str = "source-pending",
    source_pack_compatible: bool = True,
    source_freshness: SemanticsFreshnessState = "unknown",
    require_vertical_profile: bool = False,
) -> ToolkitResult[TerrainSemanticsIndex]:
    index = TerrainSemanticsIndex.from_packet(
        packet,
        source_ref_ids=source_ref_ids,
        source_pack_version=source_pack_version,
    )
    report = index.readiness_report(
        source_pack_compatible=source_pack_compatible,
        source_freshness=source_freshness,
        require_vertical_profile=require_vertical_profile,
    )
    input_hash = _terrain_semantics_hash(
        packet_digest=index.packet_digest,
        source_ref_ids=source_ref_ids,
        source_pack_version=source_pack_version,
        source_pack_compatible=source_pack_compatible,
        source_freshness=source_freshness,
        require_vertical_profile=require_vertical_profile,
    )
    suffix = input_hash.removeprefix("sha256:")[:12]
    return ToolkitResult(
        result_id=f"{packet.id}:terrain-semantics:{suffix}",
        tool_id="terrain_semantics",
        input_hash=input_hash,
        readiness=report.readiness,
        payload=index,
        assumptions=report.assumptions,
        warnings=report.warnings,
        block_reasons=tuple(
            BlockReason(
                reason_id=reason.reason_id,
                detail=reason.detail,
                remediation=reason.remediation,
                source_ref_ids=reason.source_ref_ids,
            )
            for reason in report.block_reasons
        ),
        source_ref_ids=report.source_ref_ids,
    )


def _terrain_semantics_hash(
    *,
    packet_digest: str,
    source_ref_ids: tuple[str, ...],
    source_pack_version: str,
    source_pack_compatible: bool,
    source_freshness: SemanticsFreshnessState,
    require_vertical_profile: bool,
) -> str:
    payload = {
        "packet_digest": packet_digest,
        "require_vertical_profile": require_vertical_profile,
        "schema_version": TERRAIN_SEMANTICS_TOOLKIT_SCHEMA_VERSION,
        "source_freshness": source_freshness,
        "source_pack_compatible": source_pack_compatible,
        "source_pack_version": source_pack_version,
        "source_ref_ids": sorted(set(source_ref_ids)),
        "tool_id": "terrain_semantics",
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
