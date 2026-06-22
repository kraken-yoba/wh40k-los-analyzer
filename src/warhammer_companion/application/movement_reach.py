from __future__ import annotations

import hashlib
import json
from math import isfinite

from shapely.geometry.base import BaseGeometry

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.board_state import map_packet_digest
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.movement import (
    MOVEMENT_ROUTING_ALGORITHM_VERSION,
    MOVEMENT_ROUTING_TOLERANCE_INCHES,
    MovementDiagnosticReason,
    MovementEndpointDiagnostic,
    MovementMode,
    MovementProfileId,
    MovementReachPayload,
    MovementRoutingMetadata,
    coerce_movement_mode,
    coerce_movement_profile_id,
    effective_move_distance,
    movement_profile_for_id,
)
from warhammer_companion.domain.overlays import MapOverlayLayer, ToolkitAssumption, ToolkitWarning
from warhammer_companion.los.movement import (
    MovementRoutingBudgetExceeded,
    dense_movement_collision_regions,
    movement_endpoint_diagnostic,
    movement_envelope,
    swept_route_path,
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
    movement_profile_id: str = "ground-non-mobile",
) -> ToolkitResult[MovementReachPayload]:
    movement_mode = coerce_movement_mode(mode)
    movement_profile = movement_profile_for_id(movement_profile_id)
    coerced_profile_id = movement_profile.profile_id
    effective_move = effective_move_distance(move_distance, coerced_profile_id)
    input_hash = _movement_reach_hash(
        packet=packet,
        start_center=start_center,
        target_center=target_center,
        base_diameter=base_diameter,
        move_distance=move_distance,
        mode=movement_mode,
        movement_profile_id=coerced_profile_id,
        effective_move_distance=effective_move,
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
                movement_profile_id=coerced_profile_id,
                movement_profile_label=movement_profile.label,
                effective_move_distance=effective_move,
                routing_metadata=_routing_metadata_for_hash(coerced_profile_id),
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

    try:
        envelope = movement_envelope(
            packet,
            start_center=start_center,
            base_diameter=base_diameter,
            move_distance=move_distance,
            movement_profile_id=coerced_profile_id,
        )
        endpoint = movement_endpoint_diagnostic(
            packet,
            start_center=start_center,
            target_center=target_center,
            base_diameter=base_diameter,
            move_distance=move_distance,
            movement_profile_id=coerced_profile_id,
        )
    except MovementRoutingBudgetExceeded as exc:
        return _routing_budget_blocked_result(
            packet=packet,
            input_hash=input_hash,
            suffix=suffix,
            movement_mode=movement_mode,
            start_center=start_center,
            target_center=target_center,
            base_diameter=base_diameter,
            move_distance=move_distance,
            movement_profile_id=coerced_profile_id,
            movement_profile_label=movement_profile.label,
            effective_move=effective_move,
            routing_metadata=_routing_metadata_for_hash(coerced_profile_id),
            node_count=exc.node_count,
            node_limit=exc.node_limit,
        )
    swept_path = swept_route_path(
        route_points=endpoint.route_points or (start_center, target_center),
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
        movement_profile_id=coerced_profile_id,
        movement_profile_label=movement_profile.label,
        effective_move_distance=effective_move,
        routing_metadata=endpoint.routing_metadata,
        route_path=swept_path,
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
                detail=(
                    "Endpoint diagnostics report route-connected status under selected "
                    "movement assumptions."
                ),
            ),
            ToolkitAssumption(
                assumption_id="selected-movement-profile",
                detail=f"Selected movement assumptions: {movement_profile.label}.",
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
    movement_profile_id: MovementProfileId,
    effective_move_distance: float,
) -> str:
    profile = movement_profile_for_id(movement_profile_id)
    payload = {
        "base_diameter": _canonical_float(base_diameter),
        "effective_move_distance": _canonical_float(effective_move_distance),
        "endpoint_occupancy_policy": profile.endpoint_occupancy_policy,
        "mode": mode,
        "move_distance": _canonical_float(move_distance),
        "movement_profile_id": movement_profile_id,
        "packet_digest": map_packet_digest(packet),
        "routing_algorithm_version": MOVEMENT_ROUTING_ALGORITHM_VERSION,
        "routing_resolution_inches": _canonical_float(1.0),
        "routing_tolerance_inches": _canonical_float(MOVEMENT_ROUTING_TOLERANCE_INCHES),
        "schema_version": MOVEMENT_REACH_TOOLKIT_SCHEMA_VERSION,
        "start_center": [_canonical_float(value) for value in start_center],
        "target_center": [_canonical_float(value) for value in target_center],
        "tool_id": "movement_reach",
        "traversal_policy": profile.traversal_policy,
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


def _routing_budget_blocked_result(
    *,
    packet: MapPacket,
    input_hash: str,
    suffix: str,
    movement_mode: MovementMode,
    start_center: tuple[float, float],
    target_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    movement_profile_id: MovementProfileId,
    movement_profile_label: str,
    effective_move: float,
    routing_metadata: MovementRoutingMetadata,
    node_count: int,
    node_limit: int,
) -> ToolkitResult[MovementReachPayload]:
    detail = (
        "Movement routing grid is too large for the bounded estimator "
        f"({node_count} nodes exceeds the {node_limit} node limit)."
    )
    endpoint = MovementEndpointDiagnostic(
        distance=0.0,
        within_distance=False,
        within_board=False,
        clear_of_dense_features=False,
        estimated_reachable=False,
        reasons=(
            MovementDiagnosticReason(
                reason_id="movement-routing-node-budget-exceeded",
                detail=detail,
            ),
        ),
        effective_move_distance=effective_move,
        routing_metadata=routing_metadata,
    )
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
            endpoint=endpoint,
            dense_collision_regions=_empty_geometry(),
            movement_profile_id=movement_profile_id,
            movement_profile_label=movement_profile_label,
            effective_move_distance=effective_move,
            routing_metadata=routing_metadata,
        ),
        warnings=(
            ToolkitWarning(
                warning_id="movement-routing-node-budget-exceeded",
                detail=detail,
            ),
        ),
        block_reasons=(
            BlockReason(
                reason_id="movement-routing-node-budget-exceeded",
                detail=detail,
            ),
        ),
    )


def _routing_metadata_for_hash(movement_profile_id: str) -> MovementRoutingMetadata:
    profile = movement_profile_for_id(coerce_movement_profile_id(movement_profile_id))
    return MovementRoutingMetadata(
        traversal_policy=profile.traversal_policy,
        endpoint_occupancy_policy=profile.endpoint_occupancy_policy,
    )
