from __future__ import annotations

import hashlib
import json
from math import isfinite

from shapely.geometry import Point, Polygon
from shapely.geometry.base import BaseGeometry

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.board_state import map_packet_digest
from warhammer_companion.domain.exposure import (
    EXPOSURE_MODES,
    DeploymentExposurePayload,
    ExposureDiagnosticReason,
    ExposurePlacementDiagnostic,
    coerce_exposure_mode,
)
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.overlays import MapOverlayLayer, ToolkitAssumption, ToolkitWarning
from warhammer_companion.domain.threat import THREAT_MODES, coerce_threat_mode
from warhammer_companion.los.exposure import (
    allowed_deployment_center_region,
    candidate_staging_center_region,
    exposure_risk_region,
)
from warhammer_companion.los.geometry import circular_base, visibility_polygon_from_base
from warhammer_companion.los.movement import (
    base_center_region,
    dense_movement_collision_regions,
)
from warhammer_companion.los.threat import (
    target_threat_probability,
    threat_projection,
    threat_projection_regions,
)

DEPLOYMENT_EXPOSURE_TOOLKIT_SCHEMA_VERSION = "deployment-exposure-toolkit/v0"


def build_deployment_exposure_toolkit_result(
    packet: MapPacket,
    *,
    deployment_zone_id: str,
    friendly_center: tuple[float, float],
    friendly_base_diameter: float,
    enemy_source_center: tuple[float, float],
    enemy_base_diameter: float,
    enemy_move_distance: float,
    enemy_threat_range: float,
    enemy_threat_mode: str,
    exposure_mode: str,
) -> ToolkitResult[DeploymentExposurePayload]:
    coerced_threat_mode = coerce_threat_mode(enemy_threat_mode)
    coerced_exposure_mode = coerce_exposure_mode(exposure_mode)
    input_hash = _deployment_exposure_hash(
        packet=packet,
        deployment_zone_id=deployment_zone_id,
        friendly_center=friendly_center,
        friendly_base_diameter=friendly_base_diameter,
        enemy_source_center=enemy_source_center,
        enemy_base_diameter=enemy_base_diameter,
        enemy_move_distance=enemy_move_distance,
        enemy_threat_range=enemy_threat_range,
        enemy_threat_mode=enemy_threat_mode,
        exposure_mode=exposure_mode,
    )
    suffix = input_hash.removeprefix("sha256:")[:12]
    block_reasons = _input_block_reasons(
        packet=packet,
        deployment_zone_id=deployment_zone_id,
        friendly_center=friendly_center,
        friendly_base_diameter=friendly_base_diameter,
        enemy_source_center=enemy_source_center,
        enemy_base_diameter=enemy_base_diameter,
        enemy_move_distance=enemy_move_distance,
        enemy_threat_range=enemy_threat_range,
        enemy_threat_mode=enemy_threat_mode,
        exposure_mode=exposure_mode,
    )
    if block_reasons:
        return ToolkitResult(
            result_id=f"{packet.id}:deployment-exposure:{suffix}",
            tool_id="deployment_exposure",
            input_hash=input_hash,
            readiness="blocked",
            payload=DeploymentExposurePayload(
                packet=packet,
                deployment_zone_id=deployment_zone_id,
                friendly_center=friendly_center,
                friendly_base_diameter=friendly_base_diameter,
                enemy_source_center=enemy_source_center,
                enemy_base_diameter=enemy_base_diameter,
                enemy_move_distance=enemy_move_distance,
                enemy_threat_range=enemy_threat_range,
                enemy_threat_mode=coerced_threat_mode,
                exposure_mode=coerced_exposure_mode,
                enemy_threat_regions=(),
                enemy_los_region=Polygon(),
                allowed_center_region=Polygon(),
                risk_region=Polygon(),
                candidate_center_region=Polygon(),
                placement=_blocked_placement(),
                threat_probability_at_center=0.0,
            ),
            warnings=(
                ToolkitWarning(
                    warning_id="invalid-deployment-exposure-input",
                    detail=(
                        "Deployment exposure cannot be calculated until manual inputs are valid."
                    ),
                ),
            ),
            block_reasons=block_reasons,
        )

    friendly_radius = friendly_base_diameter / 2.0
    friendly_base = circular_base(friendly_center, friendly_base_diameter)
    threat_regions = threat_projection_regions(
        packet,
        source_center=enemy_source_center,
        base_diameter=enemy_base_diameter,
        move_distance=enemy_move_distance,
        threat_range=enemy_threat_range,
        mode=coerced_threat_mode,
    )
    max_threat_region = threat_projection(
        packet,
        source_center=enemy_source_center,
        base_diameter=enemy_base_diameter,
        move_distance=enemy_move_distance,
        threat_range=enemy_threat_range,
        mode=coerced_threat_mode,
    )
    enemy_los_region = visibility_polygon_from_base(
        packet,
        center=enemy_source_center,
        base_diameter=enemy_base_diameter,
    )
    risk_region = exposure_risk_region(
        threat_region=max_threat_region,
        los_region=enemy_los_region,
        exposure_mode=coerced_exposure_mode,
    )
    allowed_center_region = allowed_deployment_center_region(
        packet,
        deployment_zone_id=deployment_zone_id,
        base_radius=friendly_radius,
    )
    candidate_center_region = candidate_staging_center_region(
        packet,
        deployment_zone_id=deployment_zone_id,
        base_radius=friendly_radius,
        risk_region=risk_region,
    )
    placement = _placement_diagnostic(
        packet=packet,
        friendly_center=friendly_center,
        friendly_base=friendly_base,
        friendly_radius=friendly_radius,
        enemy_los_region=enemy_los_region,
        max_threat_region=max_threat_region,
        risk_region=risk_region,
        allowed_center_region=allowed_center_region,
        candidate_center_region=candidate_center_region,
        exposure_mode=coerced_exposure_mode,
    )
    threat_probability = target_threat_probability(threat_regions, target_point=friendly_center)
    payload = DeploymentExposurePayload(
        packet=packet,
        deployment_zone_id=deployment_zone_id,
        friendly_center=friendly_center,
        friendly_base_diameter=friendly_base_diameter,
        enemy_source_center=enemy_source_center,
        enemy_base_diameter=enemy_base_diameter,
        enemy_move_distance=enemy_move_distance,
        enemy_threat_range=enemy_threat_range,
        enemy_threat_mode=coerced_threat_mode,
        exposure_mode=coerced_exposure_mode,
        enemy_threat_regions=threat_regions,
        enemy_los_region=enemy_los_region,
        allowed_center_region=allowed_center_region,
        risk_region=risk_region,
        candidate_center_region=candidate_center_region,
        placement=placement,
        threat_probability_at_center=threat_probability,
    )
    return ToolkitResult(
        result_id=f"{packet.id}:deployment-exposure:{suffix}",
        tool_id="deployment_exposure",
        input_hash=input_hash,
        readiness="estimated",
        payload=payload,
        overlays=(
            MapOverlayLayer(
                layer_id=f"{packet.id}:deployment-candidate-staging:{suffix}",
                layer_kind="deployment_candidate_staging",
                geometry=candidate_center_region,
                units="battlefield_inches",
                style_token="candidate-staging-centers",
                label="Candidate staging centers under selected assumptions",
                readiness="estimated",
            ),
            MapOverlayLayer(
                layer_id=f"{packet.id}:deployment-enemy-threat:{suffix}",
                layer_kind="enemy_threat_projection",
                geometry=max_threat_region,
                units="battlefield_inches",
                style_token="threat-projection-estimated",
                label="Enemy threat projection",
                readiness="estimated",
            ),
            MapOverlayLayer(
                layer_id=f"{packet.id}:deployment-enemy-los:{suffix}",
                layer_kind="enemy_los_projection",
                geometry=enemy_los_region,
                units="battlefield_inches",
                style_token="coverage-estimated",
                label="Enemy line of sight projection",
                readiness="estimated",
            ),
        ),
        assumptions=(
            ToolkitAssumption(
                assumption_id="manual-deployment-exposure-inputs",
                detail="Deployment exposure uses manual circular-base and enemy threat inputs.",
            ),
            ToolkitAssumption(
                assumption_id="selected-risk-assumption",
                detail="Candidate staging centers depend on the selected threat/LOS mode.",
            ),
        ),
        warnings=(
            ToolkitWarning(
                warning_id="estimated-deployment-exposure-diagnostic",
                detail="Estimated deployment exposure diagnostic uses manual 2D geometry.",
            ),
            ToolkitWarning(
                warning_id="not-a-placement-planner",
                detail=(
                    "This is not a placement planner; roster base sizes, coherency, terrain "
                    "traversal, mission constraints, objectives, opponent intent, and "
                    "optimization are not modeled."
                ),
            ),
        ),
    )


def _input_block_reasons(
    *,
    packet: MapPacket,
    deployment_zone_id: str,
    friendly_center: tuple[float, float],
    friendly_base_diameter: float,
    enemy_source_center: tuple[float, float],
    enemy_base_diameter: float,
    enemy_move_distance: float,
    enemy_threat_range: float,
    enemy_threat_mode: str,
    exposure_mode: str,
) -> tuple[BlockReason, ...]:
    reasons: list[BlockReason] = []
    if deployment_zone_id not in {zone.id for zone in packet.deployment_zones}:
        reasons.append(
            BlockReason(
                "invalid-deployment-zone",
                "Deployment zone must exist in the selected map packet.",
            )
        )
    if not _finite_point(friendly_center):
        reasons.append(
            BlockReason("invalid-friendly-center", "Friendly coordinates must be finite.")
        )
    if not _finite_point(enemy_source_center):
        reasons.append(BlockReason("invalid-enemy-center", "Enemy coordinates must be finite."))
    if not isfinite(friendly_base_diameter) or friendly_base_diameter <= 0:
        reasons.append(
            BlockReason(
                "invalid-friendly-base-diameter",
                "Friendly base diameter must be a positive finite number.",
            )
        )
    if not isfinite(enemy_base_diameter) or enemy_base_diameter <= 0:
        reasons.append(
            BlockReason(
                "invalid-enemy-base-diameter",
                "Enemy base diameter must be a positive finite number.",
            )
        )
    elif _finite_point(enemy_source_center) and not base_center_region(
        packet,
        enemy_base_diameter / 2.0,
    ).covers(Point(enemy_source_center)):
        reasons.append(
            BlockReason(
                "enemy-base-outside-board",
                "Enemy source center cannot keep the circular base fully inside the board.",
            )
        )
    if not isfinite(enemy_move_distance) or enemy_move_distance < 0:
        reasons.append(
            BlockReason(
                "invalid-enemy-move-distance",
                "Enemy movement distance must be a non-negative finite number.",
            )
        )
    if not isfinite(enemy_threat_range) or enemy_threat_range < 0:
        reasons.append(
            BlockReason(
                "invalid-enemy-threat-range",
                "Enemy threat range must be a non-negative finite number.",
            )
        )
    if enemy_threat_mode not in THREAT_MODES:
        reasons.append(
            BlockReason("invalid-enemy-threat-mode", "Enemy threat mode is not supported.")
        )
    if exposure_mode not in EXPOSURE_MODES:
        reasons.append(BlockReason("invalid-exposure-mode", "Exposure mode is not supported."))
    return tuple(reasons)


def _placement_diagnostic(
    *,
    packet: MapPacket,
    friendly_center: tuple[float, float],
    friendly_base: BaseGeometry,
    friendly_radius: float,
    enemy_los_region: BaseGeometry,
    max_threat_region: BaseGeometry,
    risk_region: BaseGeometry,
    allowed_center_region: BaseGeometry,
    candidate_center_region: BaseGeometry,
    exposure_mode: str,
) -> ExposurePlacementDiagnostic:
    board_center = base_center_region(packet, friendly_radius)
    dense_collision = dense_movement_collision_regions(packet, friendly_radius)
    point = Point(friendly_center)
    within_board = board_center.covers(point)
    within_zone = allowed_center_region.covers(point)
    clear_dense = not dense_collision.intersects(point)
    exposed_los = friendly_base.intersects(enemy_los_region)
    exposed_threat = friendly_base.intersects(max_threat_region)
    selected_exposed = friendly_base.intersects(risk_region) if not risk_region.is_empty else False

    reasons: list[ExposureDiagnosticReason] = []
    if not within_board:
        reasons.append(
            ExposureDiagnosticReason(
                "friendly-base-outside-board",
                "Friendly base cannot remain fully inside the board.",
            )
        )
    if not within_zone:
        reasons.append(
            ExposureDiagnosticReason(
                "friendly-base-outside-deployment-zone",
                "Friendly base is not fully inside the selected deployment zone.",
            )
        )
    if not clear_dense:
        reasons.append(
            ExposureDiagnosticReason(
                "friendly-base-overlaps-dense-feature",
                "Friendly base overlaps a dense feature in the 2D estimate.",
            )
        )
    if _mode_includes_los(exposure_mode) and exposed_los:
        reasons.append(
            ExposureDiagnosticReason(
                "intersects-los-component",
                "Friendly base intersects the enemy LOS component estimate.",
            )
        )
    if _mode_includes_threat(exposure_mode) and exposed_threat:
        reasons.append(
            ExposureDiagnosticReason(
                "intersects-threat-component",
                "Friendly base intersects the enemy threat component estimate.",
            )
        )
    if selected_exposed:
        reasons.append(
            ExposureDiagnosticReason(
                "exposed-under-selected-assumptions",
                "Friendly base intersects the selected exposure region.",
            )
        )
    return ExposurePlacementDiagnostic(
        within_board=within_board,
        within_deployment_zone=within_zone,
        clear_of_dense_features=clear_dense,
        exposed_to_los=exposed_los,
        exposed_to_threat=exposed_threat,
        not_exposed_under_assumptions=candidate_center_region.covers(point),
        reasons=tuple(reasons),
    )


def _mode_includes_los(exposure_mode: str) -> bool:
    return exposure_mode in {"los-only", "threat-or-los", "threat-and-los"}


def _mode_includes_threat(exposure_mode: str) -> bool:
    return exposure_mode in {"threat-only", "threat-or-los", "threat-and-los"}


def _deployment_exposure_hash(
    *,
    packet: MapPacket,
    deployment_zone_id: str,
    friendly_center: tuple[float, float],
    friendly_base_diameter: float,
    enemy_source_center: tuple[float, float],
    enemy_base_diameter: float,
    enemy_move_distance: float,
    enemy_threat_range: float,
    enemy_threat_mode: str,
    exposure_mode: str,
) -> str:
    payload = {
        "deployment_zone_id": deployment_zone_id,
        "enemy_base_diameter": _canonical_float(enemy_base_diameter),
        "enemy_move_distance": _canonical_float(enemy_move_distance),
        "enemy_source_center": [_canonical_float(value) for value in enemy_source_center],
        "enemy_threat_mode": enemy_threat_mode,
        "enemy_threat_range": _canonical_float(enemy_threat_range),
        "exposure_mode": exposure_mode,
        "friendly_base_diameter": _canonical_float(friendly_base_diameter),
        "friendly_center": [_canonical_float(value) for value in friendly_center],
        "packet_digest": map_packet_digest(packet),
        "schema_version": DEPLOYMENT_EXPOSURE_TOOLKIT_SCHEMA_VERSION,
        "tool_id": "deployment_exposure",
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _finite_point(point: tuple[float, float]) -> bool:
    return len(point) == 2 and all(isfinite(value) for value in point)


def _canonical_float(value: float) -> str:
    if isfinite(value):
        return f"{value:.6f}"
    if value != value:
        return "nan"
    if value > 0:
        return "inf"
    return "-inf"


def _blocked_placement() -> ExposurePlacementDiagnostic:
    return ExposurePlacementDiagnostic(
        within_board=False,
        within_deployment_zone=False,
        clear_of_dense_features=False,
        exposed_to_los=False,
        exposed_to_threat=False,
        not_exposed_under_assumptions=False,
    )
