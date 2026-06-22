from __future__ import annotations

import hashlib
import json
from math import isfinite

from shapely.geometry import Point, Polygon

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.board_state import map_packet_digest
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.movement import (
    MOVEMENT_ROUTING_ALGORITHM_VERSION,
    MOVEMENT_ROUTING_TOLERANCE_INCHES,
    MovementProfileId,
    MovementRoutingMetadata,
    coerce_movement_profile_id,
    effective_move_distance,
    movement_profile_for_id,
)
from warhammer_companion.domain.overlays import MapOverlayLayer, ToolkitAssumption, ToolkitWarning
from warhammer_companion.domain.threat import (
    THREAT_MEASUREMENT_CONVENTION,
    THREAT_MODES,
    ThreatDiceOutcome,
    ThreatMode,
    ThreatRangePayload,
    coerce_threat_mode,
)
from warhammer_companion.los.movement import MovementRoutingBudgetExceeded, base_center_region
from warhammer_companion.los.threat import (
    target_threat_probability,
    threat_distribution,
    threat_projection,
    threat_projection_regions,
)

THREAT_RANGE_TOOLKIT_SCHEMA_VERSION = "threat-range-toolkit/v0"


def build_threat_range_toolkit_result(
    packet: MapPacket,
    *,
    source_center: tuple[float, float],
    target_point: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    threat_range: float,
    mode: str,
    movement_profile_id: str = "ground-non-mobile",
) -> ToolkitResult[ThreatRangePayload]:
    threat_mode = coerce_threat_mode(mode)
    movement_profile = movement_profile_for_id(movement_profile_id)
    coerced_profile_id = movement_profile.profile_id
    effective_move = (
        0.0
        if threat_mode == "raw-range"
        else effective_move_distance(move_distance, coerced_profile_id)
    )
    input_hash = _threat_range_hash(
        packet=packet,
        source_center=source_center,
        target_point=target_point,
        base_diameter=base_diameter,
        move_distance=move_distance,
        threat_range=threat_range,
        mode=mode,
        movement_profile_id=coerced_profile_id,
        effective_move_distance=effective_move,
    )
    suffix = input_hash.removeprefix("sha256:")[:12]
    block_reasons = _input_block_reasons(
        packet=packet,
        source_center=source_center,
        target_point=target_point,
        base_diameter=base_diameter,
        move_distance=move_distance,
        threat_range=threat_range,
        mode=mode,
    )
    if block_reasons:
        payload = ThreatRangePayload(
            packet=packet,
            mode=threat_mode,
            source_center=source_center,
            target_point=target_point,
            base_diameter=base_diameter,
            move_distance=move_distance,
            threat_range=threat_range,
            measurement_convention=THREAT_MEASUREMENT_CONVENTION,
            distribution=(),
            threat_regions=(),
            max_threat_region=Polygon(),
            target_probability=0.0,
            movement_profile_id=coerced_profile_id,
            movement_profile_label=movement_profile.label,
            effective_move_distance=effective_move,
            routing_metadata=_routing_metadata_for_hash(coerced_profile_id),
        )
        return ToolkitResult(
            result_id=f"{packet.id}:threat-range:{suffix}",
            tool_id="threat_range",
            input_hash=input_hash,
            readiness="blocked",
            payload=payload,
            warnings=(
                ToolkitWarning(
                    warning_id="invalid-threat-input",
                    detail="Threat range cannot be calculated until manual inputs are valid.",
                ),
            ),
            block_reasons=block_reasons,
        )

    distribution = threat_distribution(
        mode=threat_mode,
        move_distance=move_distance,
        threat_range=threat_range,
        base_diameter=base_diameter,
        movement_profile_id=coerced_profile_id,
    )
    try:
        regions = threat_projection_regions(
            packet,
            source_center=source_center,
            base_diameter=base_diameter,
            move_distance=move_distance,
            threat_range=threat_range,
            mode=threat_mode,
            movement_profile_id=coerced_profile_id,
        )
        max_region = threat_projection(
            packet,
            source_center=source_center,
            base_diameter=base_diameter,
            move_distance=move_distance,
            threat_range=threat_range,
            mode=threat_mode,
            movement_profile_id=coerced_profile_id,
        )
    except MovementRoutingBudgetExceeded as exc:
        return _routing_budget_blocked_result(
            packet=packet,
            input_hash=input_hash,
            suffix=suffix,
            threat_mode=threat_mode,
            source_center=source_center,
            target_point=target_point,
            base_diameter=base_diameter,
            move_distance=move_distance,
            threat_range=threat_range,
            distribution=distribution,
            movement_profile_id=coerced_profile_id,
            movement_profile_label=movement_profile.label,
            effective_move=effective_move,
            routing_metadata=_routing_metadata_for_hash(coerced_profile_id),
            node_count=exc.node_count,
            node_limit=exc.node_limit,
        )
    target_probability = target_threat_probability(regions, target_point=target_point)
    payload = ThreatRangePayload(
        packet=packet,
        mode=threat_mode,
        source_center=source_center,
        target_point=target_point,
        base_diameter=base_diameter,
        move_distance=move_distance,
        threat_range=threat_range,
        measurement_convention=THREAT_MEASUREMENT_CONVENTION,
        distribution=distribution,
        threat_regions=regions,
        max_threat_region=max_region,
        target_probability=target_probability,
        movement_profile_id=coerced_profile_id,
        movement_profile_label=movement_profile.label,
        effective_move_distance=effective_move,
        routing_metadata=_routing_metadata_for_hash(coerced_profile_id),
    )
    return ToolkitResult(
        result_id=f"{packet.id}:threat-range:{suffix}",
        tool_id="threat_range",
        input_hash=input_hash,
        readiness="estimated",
        payload=payload,
        overlays=(
            MapOverlayLayer(
                layer_id=f"{packet.id}:threat-projection:{suffix}",
                layer_kind="threat_projection",
                geometry=max_region,
                units="battlefield_inches",
                style_token="threat-projection-estimated",
                label="Estimated 2D threat projection",
                readiness="estimated",
            ),
        ),
        assumptions=(
            ToolkitAssumption(
                assumption_id="manual-threat-inputs",
                detail="Threat projection uses manual source, base, movement, and range inputs.",
            ),
            ToolkitAssumption(
                assumption_id="target-point-convention",
                detail="Range is measured from source base edge to target point.",
            ),
            ToolkitAssumption(
                assumption_id="exact-manual-dice",
                detail="Variable reach uses exact D6 or 2D6 math with no added rules.",
            ),
            ToolkitAssumption(
                assumption_id="selected-movement-profile",
                detail=f"Selected movement assumptions: {movement_profile.label}.",
            ),
        ),
        warnings=(
            ToolkitWarning(
                warning_id="estimated-2d-threat-projection",
                detail=(
                    "Estimated 2D threat projection uses source base edge to target point "
                    "manual geometry."
                ),
            ),
            ToolkitWarning(
                warning_id="unsupported-threat-modifiers-disabled",
                detail=(
                    "Rerolls, modifiers, CP, stratagems, transports, reserves, actions, "
                    "target bases, line of sight, and damage are not modeled."
                ),
            ),
            ToolkitWarning(
                warning_id="source-backed-rules-pending",
                detail="Source-backed rules pending; this result remains estimated.",
            ),
            ToolkitWarning(
                warning_id="no-recommendations",
                detail="No recommendations are generated from estimated threat projections.",
            ),
        ),
    )


def _input_block_reasons(
    *,
    packet: MapPacket,
    source_center: tuple[float, float],
    target_point: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    threat_range: float,
    mode: str,
) -> tuple[BlockReason, ...]:
    reasons: list[BlockReason] = []
    if not _finite_point(source_center):
        reasons.append(BlockReason("invalid-source-center", "Source coordinates must be finite."))
    if not _finite_point(target_point):
        reasons.append(BlockReason("invalid-target-point", "Target coordinates must be finite."))
    if not isfinite(base_diameter) or base_diameter <= 0:
        reasons.append(
            BlockReason("invalid-base-diameter", "Base diameter must be a positive finite number.")
        )
    elif _finite_point(source_center) and not base_center_region(
        packet,
        base_diameter / 2.0,
    ).covers(Point(source_center)):
        reasons.append(
            BlockReason(
                "source-base-outside-board",
                "Source center cannot keep the circular base fully inside the board.",
            )
        )
    if not isfinite(move_distance) or move_distance < 0:
        reasons.append(
            BlockReason(
                "invalid-move-distance",
                "Movement distance must be a non-negative finite number.",
            )
        )
    if not isfinite(threat_range) or threat_range < 0:
        reasons.append(
            BlockReason(
                "invalid-threat-range", "Threat range must be a non-negative finite number."
            )
        )
    if mode not in THREAT_MODES:
        reasons.append(BlockReason("invalid-threat-mode", "Threat mode is not supported."))
    return tuple(reasons)


def _threat_range_hash(
    *,
    packet: MapPacket,
    source_center: tuple[float, float],
    target_point: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    threat_range: float,
    mode: str,
    movement_profile_id: MovementProfileId,
    effective_move_distance: float,
) -> str:
    profile = movement_profile_for_id(movement_profile_id)
    payload = {
        "base_diameter": _canonical_float(base_diameter),
        "effective_move_distance": _canonical_float(effective_move_distance),
        "endpoint_occupancy_policy": profile.endpoint_occupancy_policy
        if mode != "raw-range"
        else "not-applicable",
        "measurement_convention": THREAT_MEASUREMENT_CONVENTION,
        "mode": mode,
        "move_distance": _canonical_float(move_distance),
        "movement_profile_id": movement_profile_id if mode != "raw-range" else "not-applicable",
        "packet_digest": map_packet_digest(packet),
        "routing_algorithm_version": MOVEMENT_ROUTING_ALGORITHM_VERSION
        if mode != "raw-range"
        else "not-applicable",
        "routing_resolution_inches": _canonical_float(1.0) if mode != "raw-range" else "0.000000",
        "routing_tolerance_inches": _canonical_float(MOVEMENT_ROUTING_TOLERANCE_INCHES)
        if mode != "raw-range"
        else "0.000000",
        "schema_version": THREAT_RANGE_TOOLKIT_SCHEMA_VERSION,
        "source_center": [_canonical_float(value) for value in source_center],
        "target_point": [_canonical_float(value) for value in target_point],
        "threat_range": _canonical_float(threat_range),
        "tool_id": "threat_range",
        "traversal_policy": profile.traversal_policy if mode != "raw-range" else "not-applicable",
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


def _routing_budget_blocked_result(
    *,
    packet: MapPacket,
    input_hash: str,
    suffix: str,
    threat_mode: ThreatMode,
    source_center: tuple[float, float],
    target_point: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    threat_range: float,
    distribution: tuple[ThreatDiceOutcome, ...],
    movement_profile_id: MovementProfileId,
    movement_profile_label: str,
    effective_move: float,
    routing_metadata: MovementRoutingMetadata,
    node_count: int,
    node_limit: int,
) -> ToolkitResult[ThreatRangePayload]:
    detail = (
        "Movement routing grid is too large for the bounded threat estimator "
        f"({node_count} nodes exceeds the {node_limit} node limit)."
    )
    return ToolkitResult(
        result_id=f"{packet.id}:threat-range:{suffix}",
        tool_id="threat_range",
        input_hash=input_hash,
        readiness="blocked",
        payload=ThreatRangePayload(
            packet=packet,
            mode=threat_mode,
            source_center=source_center,
            target_point=target_point,
            base_diameter=base_diameter,
            move_distance=move_distance,
            threat_range=threat_range,
            measurement_convention=THREAT_MEASUREMENT_CONVENTION,
            distribution=distribution,
            threat_regions=(),
            max_threat_region=Polygon(),
            target_probability=0.0,
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
