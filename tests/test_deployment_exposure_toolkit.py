from __future__ import annotations

from shapely.geometry import Point

from warhammer_companion.application.deployment_exposure import (
    build_deployment_exposure_toolkit_result,
)
from warhammer_companion.domain.models import DeploymentZone, MapPacket
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_deployment_exposure_result_is_estimated_and_non_recommending() -> None:
    result = build_deployment_exposure_toolkit_result(
        SAMPLE_PACKETS[0],
        deployment_zone_id="attacker",
        friendly_center=(10.0, 5.0),
        friendly_base_diameter=1.57,
        enemy_source_center=(38.0, 52.0),
        enemy_base_diameter=1.57,
        enemy_move_distance=0.0,
        enemy_threat_range=1.0,
        enemy_threat_mode="raw-range",
        exposure_mode="threat-only",
    )

    assert result.tool_id == "deployment_exposure"
    assert result.readiness == "estimated"
    assert not result.allows_recommendation_language()
    assert len(result.overlays) == 3
    assert [overlay.layer_kind for overlay in result.overlays] == [
        "deployment_candidate_staging",
        "enemy_threat_projection",
        "enemy_los_projection",
    ]
    assert result.payload.deployment_zone_id == "attacker"
    assert result.payload.placement.not_exposed_under_assumptions
    assert result.payload.threat_probability_at_center == 0.0
    warning_text = " ".join(warning.detail.lower() for warning in result.warnings)
    assert "estimated deployment exposure diagnostic" in warning_text
    assert "not a placement planner" in warning_text
    for forbidden in ("legal", " safe", "recommended", "optimal", "likely", "guaranteed"):
        assert forbidden not in warning_text


def test_deployment_exposure_blocks_invalid_manual_inputs_without_overlays() -> None:
    result = build_deployment_exposure_toolkit_result(
        SAMPLE_PACKETS[0],
        deployment_zone_id="attacker",
        friendly_center=(10.0, 5.0),
        friendly_base_diameter=0.0,
        enemy_source_center=(38.0, 52.0),
        enemy_base_diameter=1.57,
        enemy_move_distance=0.0,
        enemy_threat_range=1.0,
        enemy_threat_mode="raw-range",
        exposure_mode="threat-only",
    )

    assert result.readiness == "blocked"
    assert not result.overlays
    assert [reason.reason_id for reason in result.block_reasons] == [
        "invalid-friendly-base-diameter"
    ]


def test_deployment_exposure_marks_friendly_base_exposed_to_selected_threat() -> None:
    result = build_deployment_exposure_toolkit_result(
        SAMPLE_PACKETS[0],
        deployment_zone_id="attacker",
        friendly_center=(10.0, 5.0),
        friendly_base_diameter=1.57,
        enemy_source_center=(10.0, 9.0),
        enemy_base_diameter=1.57,
        enemy_move_distance=0.0,
        enemy_threat_range=4.0,
        enemy_threat_mode="raw-range",
        exposure_mode="threat-only",
    )

    assert result.readiness == "estimated"
    assert result.payload.placement.exposed_to_threat
    assert not result.payload.placement.not_exposed_under_assumptions
    assert "exposed-under-selected-assumptions" in result.payload.placement.reason_ids
    assert "intersects-threat-component" in result.payload.placement.reason_ids


def test_deployment_exposure_uses_candidate_geometry_for_curved_deployment_zones() -> None:
    packet = _curved_deployment_packet()
    friendly_center = (12.2, 30.8)

    result = build_deployment_exposure_toolkit_result(
        packet,
        deployment_zone_id="attacker",
        friendly_center=friendly_center,
        friendly_base_diameter=1.57,
        enemy_source_center=(40.0, 5.0),
        enemy_base_diameter=1.57,
        enemy_move_distance=0.0,
        enemy_threat_range=1.0,
        enemy_threat_mode="raw-range",
        exposure_mode="threat-only",
    )

    assert not result.payload.candidate_center_region.covers(Point(friendly_center))
    assert not result.payload.placement.not_exposed_under_assumptions
    assert "friendly-base-outside-deployment-zone" in result.payload.placement.reason_ids


def test_deployment_exposure_modes_distinguish_selected_risk_from_components() -> None:
    packet = _open_board_packet()
    common_inputs = {
        "deployment_zone_id": "attacker",
        "friendly_center": (10.0, 10.0),
        "friendly_base_diameter": 1.57,
        "enemy_source_center": (10.0, 30.0),
        "enemy_base_diameter": 1.57,
        "enemy_move_distance": 0.0,
        "enemy_threat_range": 1.0,
        "enemy_threat_mode": "raw-range",
    }

    threat_only = build_deployment_exposure_toolkit_result(
        packet,
        **common_inputs,
        exposure_mode="threat-only",
    )
    los_only = build_deployment_exposure_toolkit_result(
        packet,
        **common_inputs,
        exposure_mode="los-only",
    )
    threat_or_los = build_deployment_exposure_toolkit_result(
        packet,
        **common_inputs,
        exposure_mode="threat-or-los",
    )
    threat_and_los = build_deployment_exposure_toolkit_result(
        packet,
        **common_inputs,
        exposure_mode="threat-and-los",
    )

    assert threat_only.payload.placement.not_exposed_under_assumptions
    assert not los_only.payload.placement.not_exposed_under_assumptions
    assert not threat_or_los.payload.placement.not_exposed_under_assumptions
    assert threat_and_los.payload.placement.not_exposed_under_assumptions
    assert "exposed-under-selected-assumptions" not in threat_only.payload.placement.reason_ids
    assert "exposed-under-selected-assumptions" in los_only.payload.placement.reason_ids
    assert "exposed-under-selected-assumptions" in threat_or_los.payload.placement.reason_ids
    assert "exposed-under-selected-assumptions" not in threat_and_los.payload.placement.reason_ids
    assert "intersects-los-component" in threat_and_los.payload.placement.reason_ids
    details = " ".join(reason.detail.lower() for reason in threat_and_los.payload.placement.reasons)
    assert "los component estimate" in details
    assert "under selected assumptions" not in details


def test_deployment_exposure_identity_includes_manual_inputs_and_modes() -> None:
    packet = SAMPLE_PACKETS[0]
    base = build_deployment_exposure_toolkit_result(
        packet,
        deployment_zone_id="attacker",
        friendly_center=(10.0, 5.0),
        friendly_base_diameter=1.57,
        enemy_source_center=(38.0, 52.0),
        enemy_base_diameter=1.57,
        enemy_move_distance=0.0,
        enemy_threat_range=1.0,
        enemy_threat_mode="raw-range",
        exposure_mode="threat-only",
    )
    variants = [
        build_deployment_exposure_toolkit_result(
            packet,
            deployment_zone_id="defender",
            friendly_center=(10.0, 55.0),
            friendly_base_diameter=1.57,
            enemy_source_center=(38.0, 52.0),
            enemy_base_diameter=1.57,
            enemy_move_distance=0.0,
            enemy_threat_range=1.0,
            enemy_threat_mode="raw-range",
            exposure_mode="threat-only",
        ),
        build_deployment_exposure_toolkit_result(
            packet,
            deployment_zone_id="attacker",
            friendly_center=(11.0, 5.0),
            friendly_base_diameter=1.57,
            enemy_source_center=(38.0, 52.0),
            enemy_base_diameter=1.57,
            enemy_move_distance=0.0,
            enemy_threat_range=1.0,
            enemy_threat_mode="raw-range",
            exposure_mode="threat-only",
        ),
        build_deployment_exposure_toolkit_result(
            packet,
            deployment_zone_id="attacker",
            friendly_center=(10.0, 5.0),
            friendly_base_diameter=2.0,
            enemy_source_center=(38.0, 52.0),
            enemy_base_diameter=1.57,
            enemy_move_distance=0.0,
            enemy_threat_range=1.0,
            enemy_threat_mode="raw-range",
            exposure_mode="threat-only",
        ),
        build_deployment_exposure_toolkit_result(
            packet,
            deployment_zone_id="attacker",
            friendly_center=(10.0, 5.0),
            friendly_base_diameter=1.57,
            enemy_source_center=(37.0, 52.0),
            enemy_base_diameter=1.57,
            enemy_move_distance=0.0,
            enemy_threat_range=1.0,
            enemy_threat_mode="raw-range",
            exposure_mode="threat-only",
        ),
        build_deployment_exposure_toolkit_result(
            packet,
            deployment_zone_id="attacker",
            friendly_center=(10.0, 5.0),
            friendly_base_diameter=1.57,
            enemy_source_center=(38.0, 52.0),
            enemy_base_diameter=2.0,
            enemy_move_distance=0.0,
            enemy_threat_range=1.0,
            enemy_threat_mode="raw-range",
            exposure_mode="threat-only",
        ),
        build_deployment_exposure_toolkit_result(
            packet,
            deployment_zone_id="attacker",
            friendly_center=(10.0, 5.0),
            friendly_base_diameter=1.57,
            enemy_source_center=(38.0, 52.0),
            enemy_base_diameter=1.57,
            enemy_move_distance=1.0,
            enemy_threat_range=1.0,
            enemy_threat_mode="raw-range",
            exposure_mode="threat-only",
        ),
        build_deployment_exposure_toolkit_result(
            packet,
            deployment_zone_id="attacker",
            friendly_center=(10.0, 5.0),
            friendly_base_diameter=1.57,
            enemy_source_center=(38.0, 52.0),
            enemy_base_diameter=1.57,
            enemy_move_distance=0.0,
            enemy_threat_range=2.0,
            enemy_threat_mode="raw-range",
            exposure_mode="threat-only",
        ),
        build_deployment_exposure_toolkit_result(
            packet,
            deployment_zone_id="attacker",
            friendly_center=(10.0, 5.0),
            friendly_base_diameter=1.57,
            enemy_source_center=(38.0, 52.0),
            enemy_base_diameter=1.57,
            enemy_move_distance=0.0,
            enemy_threat_range=1.0,
            enemy_threat_mode="d6-move-plus-range",
            exposure_mode="threat-only",
        ),
        build_deployment_exposure_toolkit_result(
            packet,
            deployment_zone_id="attacker",
            friendly_center=(10.0, 5.0),
            friendly_base_diameter=1.57,
            enemy_source_center=(38.0, 52.0),
            enemy_base_diameter=1.57,
            enemy_move_distance=0.0,
            enemy_threat_range=1.0,
            enemy_threat_mode="raw-range",
            exposure_mode="los-only",
        ),
    ]

    hashes = {base.input_hash, *(variant.input_hash for variant in variants)}
    assert len(hashes) == 1 + len(variants)
    suffix = base.input_hash.removeprefix("sha256:")[:12]
    assert base.result_id.endswith(suffix)
    assert all(overlay.layer_id.endswith(suffix) for overlay in base.overlays)


def _open_board_packet() -> MapPacket:
    return MapPacket(
        id="open-board",
        name="Open Board",
        source="Deployment exposure unit test fixture.",
        terrain_areas=[],
        dense_features=[],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0.0, 0.0), (44.0, 0.0), (44.0, 60.0), (0.0, 60.0)],
            )
        ],
    )


def _curved_deployment_packet() -> MapPacket:
    return MapPacket(
        id="curved-deployment",
        name="Curved Deployment",
        source="Deployment exposure unit test fixture.",
        terrain_areas=[],
        dense_features=[],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[
                    (22.0, 60.0),
                    (22.0, 40.0),
                    (18.5, 39.3),
                    (15.6, 37.4),
                    (13.7, 34.5),
                    (13.0, 30.0),
                    (0.0, 30.0),
                    (0.0, 60.0),
                ],
            )
        ],
    )
