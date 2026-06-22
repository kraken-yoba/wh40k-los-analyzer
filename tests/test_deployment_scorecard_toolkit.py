from __future__ import annotations

from warhammer_companion.application.deployment_scorecard import (
    build_deployment_scorecard_toolkit_result,
)
from warhammer_companion.domain.deployment_scorecard import (
    DEPLOYMENT_SCORECARD_ASSESSMENTS,
    DEPLOYMENT_SCORECARD_COMPONENT_IDS,
)
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_deployment_scorecard_result_is_estimated_and_component_based() -> None:
    result = _build_scorecard(turn_order="going-first")
    text = _visible_result_text(result)

    assert result.tool_id == "deployment_scorecard"
    assert result.readiness == "estimated"
    assert not result.allows_recommendation_language()
    assert result.payload.turn_order == "going-first"
    assert result.payload.mission_pack_readiness == "estimated"
    assert {source.source_ref_id for source in result.payload.mission_source_refs} >= {
        "event-companion-layout-metadata",
        "public-mission-sheet-candidate",
    }
    assert [component.component_id for component in result.payload.components] == list(
        DEPLOYMENT_SCORECARD_COMPONENT_IDS
    )
    assert {component.assessment for component in result.payload.components} <= set(
        DEPLOYMENT_SCORECARD_ASSESSMENTS
    )
    assert not hasattr(result.payload, "total_score")
    assert not hasattr(result.payload, "rank")
    assert not hasattr(result.payload, "grade")
    for forbidden in (
        "legal",
        " safe",
        "optimal",
        "recommended",
        "likely",
        "guaranteed",
        "preferred",
        "pairing",
    ):
        assert forbidden not in text


def test_deployment_scorecard_supports_both_turn_order_assumptions() -> None:
    first = _build_scorecard(turn_order="going-first")
    second = _build_scorecard(turn_order="going-second")

    assert first.readiness == "estimated"
    assert second.readiness == "estimated"
    assert first.payload.turn_order == "going-first"
    assert second.payload.turn_order == "going-second"
    assert first.input_hash != second.input_hash
    assert any(
        component.component_id == "turn-order-assumption" and "going-second" in component.detail
        for component in second.payload.components
    )


def test_deployment_scorecard_blocks_invalid_turn_order_without_overlays() -> None:
    result = _build_scorecard(turn_order="alpha-strike")

    assert result.readiness == "blocked"
    assert not result.overlays
    assert result.payload.turn_order == "alpha-strike"
    assert [reason.reason_id for reason in result.block_reasons] == ["invalid-turn-order"]
    assert any(
        component.component_id == "turn-order-assumption" and component.assessment == "blocked"
        for component in result.payload.components
    )


def test_deployment_scorecard_blocks_invalid_manual_inputs_without_overlays() -> None:
    result = _build_scorecard(friendly_base_diameter=0.0)

    assert result.readiness == "blocked"
    assert not result.overlays
    assert [reason.reason_id for reason in result.block_reasons] == [
        "invalid-friendly-base-diameter"
    ]
    assert any(
        component.component_id == "deployment-fit" and component.assessment == "blocked"
        for component in result.payload.components
    )


def test_deployment_scorecard_identity_changes_with_manual_footprint() -> None:
    base = _build_scorecard()
    moved = _build_scorecard(friendly_center=(11.0, 5.0))

    assert base.input_hash != moved.input_hash
    assert base.result_id.endswith(base.input_hash.removeprefix("sha256:")[:12])
    assert moved.result_id.endswith(moved.input_hash.removeprefix("sha256:")[:12])


def test_deployment_scorecard_identity_changes_with_enemy_movement_profile() -> None:
    non_mobile = _build_scorecard(
        enemy_move_distance=9.0,
        enemy_threat_range=0.5,
        enemy_threat_mode="fixed-move-plus-range",
        enemy_movement_profile_id="ground-non-mobile",
    )
    mobile = _build_scorecard(
        enemy_move_distance=9.0,
        enemy_threat_range=0.5,
        enemy_threat_mode="fixed-move-plus-range",
        enemy_movement_profile_id="ground-mobile",
    )
    hover_fly = _build_scorecard(
        enemy_move_distance=9.0,
        enemy_threat_range=0.5,
        enemy_threat_mode="fixed-move-plus-range",
        enemy_movement_profile_id="fly-hover-take-to-skies",
    )

    assert non_mobile.input_hash != mobile.input_hash
    assert non_mobile.input_hash != hover_fly.input_hash
    assert mobile.input_hash != hover_fly.input_hash
    assert non_mobile.payload.deployment_exposure.enemy_movement_profile_id == ("ground-non-mobile")
    assert mobile.payload.deployment_exposure.enemy_movement_profile_id == "ground-mobile"
    assert hover_fly.payload.deployment_exposure.enemy_movement_profile_id == (
        "fly-hover-take-to-skies"
    )


def _build_scorecard(
    *,
    friendly_center: tuple[float, float] = (10.0, 5.0),
    friendly_base_diameter: float = 1.57,
    enemy_move_distance: float = 0.0,
    enemy_threat_range: float = 1.0,
    enemy_threat_mode: str = "raw-range",
    enemy_movement_profile_id: str = "ground-non-mobile",
    turn_order: str = "going-first",
):
    return build_deployment_scorecard_toolkit_result(
        SAMPLE_PACKETS[0],
        deployment_zone_id="attacker",
        friendly_center=friendly_center,
        friendly_base_diameter=friendly_base_diameter,
        enemy_source_center=(38.0, 52.0),
        enemy_base_diameter=1.57,
        enemy_move_distance=enemy_move_distance,
        enemy_threat_range=enemy_threat_range,
        enemy_threat_mode=enemy_threat_mode,
        enemy_movement_profile_id=enemy_movement_profile_id,
        exposure_mode="threat-only",
        turn_order=turn_order,
    )


def _visible_result_text(result) -> str:
    component_text = " ".join(
        f"{component.label} {component.detail}" for component in result.payload.components
    )
    warnings = " ".join(warning.detail for warning in result.warnings)
    assumptions = " ".join(assumption.detail for assumption in result.assumptions)
    return f"{component_text} {warnings} {assumptions}".lower()
