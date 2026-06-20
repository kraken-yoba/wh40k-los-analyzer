from __future__ import annotations

import hashlib
from dataclasses import dataclass

from shapely.geometry.base import BaseGeometry

from warhammer_companion.application.toolkit import ToolkitResult
from warhammer_companion.domain.board_state import BoardState
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.overlays import (
    MapOverlayLayer,
    ToolkitAssumption,
    ToolkitWarning,
)
from warhammer_companion.los.geometry import (
    VisibilityRay,
    visibility_polygon_from_base,
    visibility_rays_from_base,
)

LOS_CHECKER_TOOLKIT_SCHEMA_VERSION = "los-checker-toolkit/v0"


@dataclass(frozen=True)
class LosCheckerToolkitPayload:
    board_state: BoardState
    packet: MapPacket
    center: tuple[float, float]
    base_diameter: float
    coverage_polygon: BaseGeometry
    rays: tuple[VisibilityRay, ...]


def build_los_checker_toolkit_result(
    packet: MapPacket,
    *,
    center: tuple[float, float],
    base_diameter: float,
) -> ToolkitResult[LosCheckerToolkitPayload]:
    coverage_polygon = visibility_polygon_from_base(
        packet,
        center=center,
        base_diameter=base_diameter,
    )
    rays = tuple(visibility_rays_from_base(packet, center=center, base_diameter=base_diameter))
    board_state = BoardState.from_packet(
        packet,
        state_id=f"{packet.id}:los-checker",
        assumptions=(
            ToolkitAssumption(
                assumption_id="two-dimensional-los",
                detail="LOS uses current two-dimensional dense terrain geometry.",
            ),
        ),
    )
    input_hash = _toolkit_input_hash(
        tool_id="los_checker",
        packet_digest=board_state.packet_digest,
        center=center,
        base_diameter=base_diameter,
    )
    result_suffix = input_hash.removeprefix("sha256:")[:12]
    return ToolkitResult(
        result_id=f"{packet.id}:los-checker:{result_suffix}",
        tool_id="los_checker",
        input_hash=input_hash,
        readiness="estimated",
        payload=LosCheckerToolkitPayload(
            board_state=board_state,
            packet=packet,
            center=center,
            base_diameter=base_diameter,
            coverage_polygon=coverage_polygon,
            rays=rays,
        ),
        overlays=(
            MapOverlayLayer(
                layer_id=f"{packet.id}:los-coverage:{result_suffix}",
                layer_kind="line_of_sight_coverage",
                geometry=coverage_polygon,
                units="battlefield_inches",
                style_token="los-coverage-estimated",
                label="Estimated LOS coverage",
                readiness="estimated",
            ),
        ),
        assumptions=board_state.assumptions,
        warnings=(
            *board_state.warnings,
            ToolkitWarning(
                warning_id="source-backed-los-mechanics-pending",
                detail=("LOS output is diagnostic until source-backed visibility mechanics exist."),
            ),
        ),
    )


def _toolkit_input_hash(
    tool_id: str,
    packet_digest: str,
    center: tuple[float, float],
    base_diameter: float,
) -> str:
    payload = (
        f"{LOS_CHECKER_TOOLKIT_SCHEMA_VERSION}|{tool_id}|{packet_digest}|"
        f"{center[0]:.6f}|{center[1]:.6f}|{base_diameter:.6f}"
    )
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
