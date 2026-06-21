from __future__ import annotations

import hashlib
import json
from math import isfinite

from shapely.geometry.base import BaseGeometry

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.board_state import map_packet_digest
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.movement import (
    MovementEndpointDiagnostic,
    MovementMode,
    MovementReachPayload,
    coerce_movement_mode,
)
from warhammer_companion.domain.overlays import MapOverlayLayer, ToolkitAssumption, ToolkitWarning
from warhammer_companion.los.movement import (
    dense_movement_collision_regions,
    movement_endpoint_diagnostic,
    movement_envelope,
    swept_base_path,
)

MOVEMENT_REACH_TOOLKIT_SCHEMA_VERSION = "movement-reach-toolkit/v0"


def build_movement_reach_toolkit_result(
    packet: MapPacket,
    *,
    start_center: tuple[float, float],
    target_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    mode: str,
) -> ToolkitResult[MovementReachPayload]:
    movement_mode = coerce_movement_mode(mode)
    input_hash = _movement_reach_hash(
        packet=packet,
        start_center=start_center,
        target_center=target_center,
        base_diameter=base_diameter,
        move_distance=move_distance,
        mode=movement_mode,
    )
    suffix = input_hash.removeprefix("sha256:")[:12]
    block_reasons = _input_block_reasons(
        start_center=start_center,
        target_center=target_center,
        base_diameter=base_diameter,
        move_distance=move_distance,
    )
    if block_reasons:
        return ToolkitResult(
            result_id=f"{packet.id}:movement-reach:{suffix}",
            tool_id="movement_reach",
            input_hash=input_hash,
            readiness="blocked",
            payload=MovementReachPayload(
                packet=packet,
                mode=movement_mode,
                start_center=start_center,
                target_center=target_center,
                base_diameter=base_diameter,
                move_distance=move_distance,
                movement_envelope=_empty_geometry(),
                swept_path=_empty_geometry(),
                endpoint=_blocked_endpoint(),
                dense_collision_regions=_empty_geometry(),
            ),
            warnings=(
                ToolkitWarning(
                    warning_id="invalid-movement-input",
                    detail=(
                        "Movement reach cannot be calculated until manual geometry inputs "
                        "are valid."
                    ),
                ),
            ),
            block_reasons=block_reasons,
        )

    envelope = movement_envelope(
        packet,
        start_center=start_center,
        base_diameter=base_diameter,
        move_distance=move_distance,
    )
    endpoint = movement_endpoint_diagnostic(
        packet,
        start_center=start_center,
        target_center=target_center,
        base_diameter=base_diameter,
        move_distance=move_distance,
    )
    swept_path = swept_base_path(
        start_center=start_center,
        target_center=target_center,
        base_diameter=base_diameter,
    )
    dense_collision_regions = dense_movement_collision_regions(packet, base_diameter / 2.0)
    payload = MovementReachPayload(
        packet=packet,
        mode=movement_mode,
        start_center=start_center,
        target_center=target_center,
        base_diameter=base_diameter,
        move_distance=move_distance,
        movement_envelope=envelope,
        swept_path=swept_path,
        endpoint=endpoint,
        dense_collision_regions=dense_collision_regions,
    )
    return ToolkitResult(
        result_id=f"{packet.id}:movement-reach:{suffix}",
        tool_id="movement_reach",
        input_hash=input_hash,
        readiness="estimated",
        payload=payload,
        overlays=(
            MapOverlayLayer(
                layer_id=f"{packet.id}:movement-envelope:{suffix}",
                layer_kind="movement_envelope",
                geometry=envelope,
                units="inches",
                style_token="movement-envelope",
                label="Estimated 2D movement envelope",
                readiness="estimated",
            ),
        ),
        assumptions=(
            ToolkitAssumption(
                assumption_id="single-model-round-base",
                detail="Movement reach uses one manual circular base and one selected endpoint.",
            ),
            ToolkitAssumption(
                assumption_id="straight-corridor-diagnostic",
                detail="Endpoint diagnostics use a straight swept circular base corridor.",
            ),
        ),
        warnings=(
            ToolkitWarning(
                warning_id="estimated-2d-geometry",
                detail=(
                    "Estimated 2D geometry uses manual circular-base inputs and source-pending "
                    "terrain hints."
                ),
            ),
            ToolkitWarning(
                warning_id="movement-rules-pending",
                detail=(
                    "Vertical movement, coherency, other models, and mode-specific restrictions "
                    "are not included."
                ),
            ),
        ),
    )


def _input_block_reasons(
    *,
    start_center: tuple[float, float],
    target_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
) -> tuple[BlockReason, ...]:
    reasons: list[BlockReason] = []
    if not _finite_point(start_center):
        reasons.append(
            BlockReason(
                reason_id="invalid-start-center",
                detail="Start center coordinates must be finite.",
            )
        )
    if not _finite_point(target_center):
        reasons.append(
            BlockReason(
                reason_id="invalid-target-center",
                detail="Target center coordinates must be finite.",
            )
        )
    if not isfinite(base_diameter) or base_diameter <= 0:
        reasons.append(
            BlockReason(
                reason_id="invalid-base-diameter",
                detail="Base diameter must be a positive finite number.",
            )
        )
    if not isfinite(move_distance) or move_distance <= 0:
        reasons.append(
            BlockReason(
                reason_id="invalid-move-distance",
                detail="Movement distance must be a positive finite number.",
            )
        )
    return tuple(reasons)


def _movement_reach_hash(
    *,
    packet: MapPacket,
    start_center: tuple[float, float],
    target_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    mode: MovementMode,
) -> str:
    payload = {
        "base_diameter": _canonical_float(base_diameter),
        "mode": mode,
        "move_distance": _canonical_float(move_distance),
        "packet_digest": map_packet_digest(packet),
        "schema_version": MOVEMENT_REACH_TOOLKIT_SCHEMA_VERSION,
        "start_center": [_canonical_float(value) for value in start_center],
        "target_center": [_canonical_float(value) for value in target_center],
        "tool_id": "movement_reach",
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _canonical_float(value: float) -> str:
    if isfinite(value):
        return f"{value:.6f}"
    if value != value:
        return "nan"
    if value > 0:
        return "inf"
    return "-inf"


def _finite_point(point: tuple[float, float]) -> bool:
    return len(point) == 2 and all(isfinite(value) for value in point)


def _empty_geometry() -> BaseGeometry:
    from shapely.geometry import Polygon

    return Polygon()


def _blocked_endpoint() -> MovementEndpointDiagnostic:
    return MovementEndpointDiagnostic(
        distance=0.0,
        within_distance=False,
        within_board=False,
        clear_of_dense_features=False,
        estimated_reachable=False,
    )
