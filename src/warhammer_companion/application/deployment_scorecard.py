from __future__ import annotations

import hashlib
import json

from warhammer_companion.application.deployment_exposure import (
    build_deployment_exposure_toolkit_result,
)
from warhammer_companion.application.mission_pack import build_mission_pack_toolkit_result
from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.deployment_scorecard import (
    TURN_ORDER_ASSUMPTIONS,
    DeploymentScorecardComponent,
    DeploymentScorecardPayload,
)
from warhammer_companion.domain.exposure import DeploymentExposurePayload
from warhammer_companion.domain.missions import MissionPackPayload
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.overlays import ToolkitAssumption, ToolkitReadiness, ToolkitWarning

DEPLOYMENT_SCORECARD_TOOLKIT_SCHEMA_VERSION = "deployment-scorecard-toolkit/v0"
DEPLOYMENT_SCORECARD_WARNINGS = (
    "Deployment scorecard is an estimated diagnostic using manual inch-based 2D inputs.",
    "Mission context is source-pending; objective/action scoring is not modeled.",
    "Turn-order assumption is manual; opponent intent is not modeled.",
)


def build_deployment_scorecard_toolkit_result(
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
    turn_order: str,
) -> ToolkitResult[DeploymentScorecardPayload]:
    exposure_result = build_deployment_exposure_toolkit_result(
        packet,
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
    mission_result = build_mission_pack_toolkit_result()
    block_reasons = _scorecard_block_reasons(
        turn_order=turn_order,
        exposure_block_reasons=exposure_result.block_reasons,
    )
    input_hash = _deployment_scorecard_hash(
        exposure_input_hash=exposure_result.input_hash,
        mission_pack_input_hash=mission_result.input_hash,
        turn_order=turn_order,
    )
    suffix = input_hash.removeprefix("sha256:")[:12]
    readiness: ToolkitReadiness = "blocked" if block_reasons else "estimated"
    payload = DeploymentScorecardPayload(
        packet=packet,
        deployment_zone_id=deployment_zone_id,
        friendly_center=friendly_center,
        friendly_base_diameter=friendly_base_diameter,
        enemy_source_center=enemy_source_center,
        enemy_base_diameter=enemy_base_diameter,
        enemy_move_distance=enemy_move_distance,
        enemy_threat_range=enemy_threat_range,
        enemy_threat_mode=exposure_result.payload.enemy_threat_mode,
        exposure_mode=exposure_result.payload.exposure_mode,
        turn_order=turn_order,
        deployment_exposure_result_id=exposure_result.result_id,
        deployment_exposure_readiness=exposure_result.readiness,
        deployment_exposure=exposure_result.payload,
        mission_pack_result_id=mission_result.result_id,
        mission_pack_readiness=mission_result.readiness,
        mission_source_refs=mission_result.payload.source_refs,
        components=_scorecard_components(
            exposure_result=exposure_result,
            mission_result=mission_result,
            turn_order=turn_order,
            turn_order_valid=turn_order in TURN_ORDER_ASSUMPTIONS,
        ),
        not_exposed_under_assumptions=(
            False
            if exposure_result.is_blocked
            else exposure_result.payload.placement.not_exposed_under_assumptions
        ),
        threat_probability_at_center=exposure_result.payload.threat_probability_at_center,
    )
    return ToolkitResult(
        result_id=f"{packet.id}:deployment-scorecard:{suffix}",
        tool_id="deployment_scorecard",
        input_hash=input_hash,
        readiness=readiness,
        payload=payload,
        overlays=() if block_reasons else exposure_result.overlays,
        assumptions=(
            ToolkitAssumption(
                assumption_id="manual-inch-inputs",
                detail=(
                    "Coordinates, base diameters, movement, and threat distances are manual "
                    "battlefield-inch inputs."
                ),
            ),
            ToolkitAssumption(
                assumption_id="manual-turn-order",
                detail=f"Turn order is supplied manually as {turn_order}.",
            ),
        ),
        warnings=_scorecard_warnings(blocked=bool(block_reasons)),
        block_reasons=block_reasons,
        source_ref_ids=mission_result.source_ref_ids,
    )


def _scorecard_block_reasons(
    *,
    turn_order: str,
    exposure_block_reasons: tuple[BlockReason, ...],
) -> tuple[BlockReason, ...]:
    reasons: list[BlockReason] = []
    if turn_order not in TURN_ORDER_ASSUMPTIONS:
        reasons.append(
            BlockReason(
                reason_id="invalid-turn-order",
                detail="Turn order must be going-first or going-second.",
            )
        )
    reasons.extend(exposure_block_reasons)
    return tuple(reasons)


def _scorecard_components(
    *,
    exposure_result: ToolkitResult[DeploymentExposurePayload],
    mission_result: ToolkitResult[MissionPackPayload],
    turn_order: str,
    turn_order_valid: bool,
) -> tuple[DeploymentScorecardComponent, ...]:
    return (
        _deployment_fit_component(exposure_result),
        _selected_exposure_component(exposure_result),
        DeploymentScorecardComponent(
            component_id="mission-readiness",
            label="Mission readiness",
            assessment="warning",
            detail=(
                f"Mission context is {mission_result.readiness} and source-pending; "
                "objective/action scoring is not modeled."
            ),
            source_ref_ids=mission_result.source_ref_ids,
        ),
        DeploymentScorecardComponent(
            component_id="turn-order-assumption",
            label="Turn order assumption",
            assessment="warning" if turn_order_valid else "blocked",
            detail=(
                f"Manual turn order: {turn_order}."
                if turn_order_valid
                else "Turn order must be going-first or going-second."
            ),
        ),
    )


def _deployment_fit_component(
    exposure_result: ToolkitResult[DeploymentExposurePayload],
) -> DeploymentScorecardComponent:
    if exposure_result.is_blocked:
        reason_ids = ", ".join(reason.reason_id for reason in exposure_result.block_reasons)
        return DeploymentScorecardComponent(
            component_id="deployment-fit",
            label="Deployment fit",
            assessment="blocked",
            detail=f"Deployment exposure input is blocked: {reason_ids}.",
            source_ref_ids=(exposure_result.result_id,),
        )
    placement = exposure_result.payload.placement
    if (
        placement.within_board
        and placement.within_deployment_zone
        and placement.clear_of_dense_features
    ):
        return DeploymentScorecardComponent(
            component_id="deployment-fit",
            label="Deployment fit",
            assessment="checked",
            detail=(
                "Manual footprint fits the selected deployment zone and board in the 2D estimate."
            ),
            source_ref_ids=(exposure_result.result_id,),
        )
    reason_ids = ", ".join(placement.reason_ids)
    return DeploymentScorecardComponent(
        component_id="deployment-fit",
        label="Deployment fit",
        assessment="warning",
        detail=f"Manual footprint has deployment diagnostics: {reason_ids}.",
        source_ref_ids=(exposure_result.result_id,),
    )


def _selected_exposure_component(
    exposure_result: ToolkitResult[DeploymentExposurePayload],
) -> DeploymentScorecardComponent:
    if exposure_result.is_blocked:
        return DeploymentScorecardComponent(
            component_id="selected-exposure",
            label="Selected exposure",
            assessment="blocked",
            detail="Selected exposure cannot run until deployment exposure input is valid.",
            source_ref_ids=(exposure_result.result_id,),
        )
    placement = exposure_result.payload.placement
    probability = exposure_result.payload.threat_probability_at_center * 100.0
    if placement.not_exposed_under_assumptions:
        return DeploymentScorecardComponent(
            component_id="selected-exposure",
            label="Selected exposure",
            assessment="checked",
            detail=(
                "Selected threat/LOS region does not intersect the friendly base under current "
                f"assumptions. Threat probability at center: {probability:.1f}%."
            ),
            source_ref_ids=(exposure_result.result_id,),
        )
    return DeploymentScorecardComponent(
        component_id="selected-exposure",
        label="Selected exposure",
        assessment="warning",
        detail=(
            "Selected threat/LOS region intersects the friendly base under current assumptions. "
            f"Threat probability at center: {probability:.1f}%."
        ),
        source_ref_ids=(exposure_result.result_id,),
    )


def _scorecard_warnings(*, blocked: bool) -> tuple[ToolkitWarning, ...]:
    warnings = [
        ToolkitWarning(
            warning_id="estimated-deployment-scorecard",
            detail=DEPLOYMENT_SCORECARD_WARNINGS[0],
        ),
        ToolkitWarning(
            warning_id="mission-context-source-pending",
            detail=DEPLOYMENT_SCORECARD_WARNINGS[1],
        ),
        ToolkitWarning(
            warning_id="manual-turn-order-assumption",
            detail=DEPLOYMENT_SCORECARD_WARNINGS[2],
        ),
    ]
    if blocked:
        warnings.append(
            ToolkitWarning(
                warning_id="blocked-deployment-scorecard",
                detail="Manual input cannot be evaluated until blockers are resolved.",
            )
        )
    return tuple(warnings)


def _deployment_scorecard_hash(
    *,
    exposure_input_hash: str,
    mission_pack_input_hash: str,
    turn_order: str,
) -> str:
    payload = {
        "deployment_exposure_input_hash": exposure_input_hash,
        "mission_pack_input_hash": mission_pack_input_hash,
        "schema_version": DEPLOYMENT_SCORECARD_TOOLKIT_SCHEMA_VERSION,
        "tool_id": "deployment_scorecard",
        "turn_order": turn_order,
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
