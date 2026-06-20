from __future__ import annotations

import hashlib

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.terrain_semantics import TerrainSemanticsIndex

TERRAIN_SEMANTICS_TOOLKIT_SCHEMA_VERSION = "terrain-semantics-toolkit/v0"


def build_terrain_semantics_result(
    packet: MapPacket,
    *,
    source_ref_ids: tuple[str, ...] = (),
    source_pack_version: str = "source-pending",
    source_pack_compatible: bool = True,
    require_vertical_profile: bool = False,
) -> ToolkitResult[TerrainSemanticsIndex]:
    index = TerrainSemanticsIndex.from_packet(
        packet,
        source_ref_ids=source_ref_ids,
        source_pack_version=source_pack_version,
    )
    report = index.readiness_report(
        source_pack_compatible=source_pack_compatible,
        require_vertical_profile=require_vertical_profile,
    )
    input_hash = _terrain_semantics_hash(
        packet_digest=index.packet_digest,
        source_pack_version=source_pack_version,
        source_pack_compatible=source_pack_compatible,
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
    source_pack_version: str,
    source_pack_compatible: bool,
    require_vertical_profile: bool,
) -> str:
    payload = (
        f"{TERRAIN_SEMANTICS_TOOLKIT_SCHEMA_VERSION}|terrain_semantics|"
        f"{packet_digest}|{source_pack_version}|{source_pack_compatible}|"
        f"{require_vertical_profile}"
    )
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
