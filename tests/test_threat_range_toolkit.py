from __future__ import annotations

from warhammer_companion.application.threat_range import build_threat_range_toolkit_result
from warhammer_companion.domain.models import (
    BoardSize,
    DenseTerrainFeature,
    DeploymentZone,
    MapPacket,
    TerrainArea,
    TerrainKind,
)
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_threat_range_toolkit_result_is_estimated_and_non_recommending() -> None:
    result = build_threat_range_toolkit_result(
        SAMPLE_PACKETS[0],
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
        threat_range=2.0,
        mode="2d6-move-plus-range",
    )

    assert result.tool_id == "threat_range"
    assert result.readiness == "estimated"
    assert not result.allows_recommendation_language()
    assert len(result.overlays) == 1
    assert result.overlays[0].layer_kind == "threat_projection"
    assert result.payload.mode == "2d6-move-plus-range"
    assert result.payload.measurement_convention == "source-base-edge-to-target-point"
    assert result.payload.target_probability > 0.0
    warning_text = " ".join(warning.detail.lower() for warning in result.warnings)
    assert "estimated 2d threat projection" in warning_text
    assert "source base edge to target point" in warning_text
    assert "source-backed rules pending" in warning_text
    assert "no recommendations" in warning_text
    for forbidden in ("legal", " safe", "recommended", "optimal", "likely", "guaranteed"):
        assert forbidden not in warning_text


def test_threat_range_toolkit_blocks_invalid_manual_inputs_without_overlays() -> None:
    result = build_threat_range_toolkit_result(
        SAMPLE_PACKETS[0],
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=0.0,
        move_distance=6.0,
        threat_range=2.0,
        mode="raw-range",
    )

    assert result.readiness == "blocked"
    assert not result.overlays
    assert result.block_reasons
    assert result.block_reasons[0].reason_id == "invalid-base-diameter"


def test_threat_range_toolkit_blocks_source_base_that_overhangs_board() -> None:
    result = build_threat_range_toolkit_result(
        SAMPLE_PACKETS[0],
        source_center=(0.0, 0.0),
        target_point=(1.0, 1.0),
        base_diameter=2.0,
        move_distance=0.0,
        threat_range=2.0,
        mode="raw-range",
    )

    assert result.readiness == "blocked"
    assert not result.overlays
    assert [reason.reason_id for reason in result.block_reasons] == ["source-base-outside-board"]


def test_threat_range_toolkit_deployment_zone_source_ignores_source_coordinates() -> None:
    packet = SAMPLE_PACKETS[0]
    finite = build_threat_range_toolkit_result(
        packet,
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=0.0,
        threat_range=2.0,
        mode="raw-range",
        source_mode="deployment-zone",
        source_deployment_zone_id="attacker",
    )
    invalid_point = build_threat_range_toolkit_result(
        packet,
        source_center=(float("nan"), 999.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=0.0,
        threat_range=2.0,
        mode="raw-range",
        source_mode="deployment-zone",
        source_deployment_zone_id="attacker",
    )

    assert finite.readiness == "estimated"
    assert invalid_point.readiness == "estimated"
    assert finite.input_hash == invalid_point.input_hash
    assert finite.payload.source_mode == "deployment-zone"
    assert finite.payload.source_deployment_zone_id == "attacker"
    assert finite.payload.max_threat_region.equals_exact(
        invalid_point.payload.max_threat_region,
        tolerance=0.001,
    )


def test_threat_range_toolkit_invalid_source_mode_blocks_without_overlays() -> None:
    result = build_threat_range_toolkit_result(
        SAMPLE_PACKETS[0],
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=0.0,
        threat_range=2.0,
        mode="raw-range",
        source_mode="army-roster",
    )

    assert result.readiness == "blocked"
    assert not result.overlays
    assert "invalid-source-mode" in {reason.reason_id for reason in result.block_reasons}


def test_threat_range_toolkit_invalid_source_deployment_zone_blocks_without_overlays() -> None:
    result = build_threat_range_toolkit_result(
        SAMPLE_PACKETS[0],
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=0.0,
        threat_range=2.0,
        mode="raw-range",
        source_mode="deployment-zone",
        source_deployment_zone_id="missing",
    )

    assert result.readiness == "blocked"
    assert not result.overlays
    assert [reason.reason_id for reason in result.block_reasons] == [
        "invalid-source-deployment-zone"
    ]


def test_threat_range_toolkit_empty_source_region_blocks_without_overlays() -> None:
    result = build_threat_range_toolkit_result(
        _empty_source_region_packet(),
        source_center=(16.0, 10.0),
        target_point=(5.0, 5.0),
        base_diameter=4.0,
        move_distance=0.0,
        threat_range=2.0,
        mode="raw-range",
        source_mode="deployment-zone",
        source_deployment_zone_id="attacker",
    )

    assert result.readiness == "blocked"
    assert not result.overlays
    assert [reason.reason_id for reason in result.block_reasons] == ["empty-source-region"]


def test_threat_range_toolkit_source_zone_changes_identity() -> None:
    packet = SAMPLE_PACKETS[0]
    attacker = build_threat_range_toolkit_result(
        packet,
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=0.0,
        threat_range=2.0,
        mode="raw-range",
        source_mode="deployment-zone",
        source_deployment_zone_id="attacker",
    )
    defender = build_threat_range_toolkit_result(
        packet,
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=0.0,
        threat_range=2.0,
        mode="raw-range",
        source_mode="deployment-zone",
        source_deployment_zone_id="defender",
    )

    assert attacker.input_hash != defender.input_hash
    assert not attacker.payload.max_threat_region.equals_exact(
        defender.payload.max_threat_region,
        tolerance=0.001,
    )


def test_threat_range_toolkit_raw_deployment_source_is_profile_invariant() -> None:
    packet = SAMPLE_PACKETS[0]
    non_mobile = build_threat_range_toolkit_result(
        packet,
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=9.0,
        threat_range=2.0,
        mode="raw-range",
        source_mode="deployment-zone",
        source_deployment_zone_id="attacker",
        movement_profile_id="ground-non-mobile",
    )
    fly = build_threat_range_toolkit_result(
        packet,
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=9.0,
        threat_range=2.0,
        mode="raw-range",
        source_mode="deployment-zone",
        source_deployment_zone_id="attacker",
        movement_profile_id="fly-take-to-skies",
    )

    assert non_mobile.input_hash == fly.input_hash
    assert non_mobile.payload.max_threat_region.equals_exact(
        fly.payload.max_threat_region,
        tolerance=0.001,
    )


def test_threat_range_toolkit_blocks_oversized_routing_grid_without_raising() -> None:
    result = build_threat_range_toolkit_result(
        _oversized_route_packet(),
        source_center=(20.0, 100.0),
        target_point=(180.0, 100.0),
        base_diameter=1.0,
        move_distance=180.0,
        threat_range=0.5,
        mode="fixed-move-plus-range",
        movement_profile_id="ground-non-mobile",
    )

    assert result.readiness == "blocked"
    assert not result.overlays
    assert [reason.reason_id for reason in result.block_reasons] == [
        "movement-routing-node-budget-exceeded"
    ]
    assert "too large" in result.warnings[0].detail.lower()


def test_threat_range_toolkit_invalid_mode_hash_does_not_collide_with_raw_range() -> None:
    packet = SAMPLE_PACKETS[0]
    invalid = build_threat_range_toolkit_result(
        packet,
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
        threat_range=2.0,
        mode="bad-mode",
    )
    raw = build_threat_range_toolkit_result(
        packet,
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
        threat_range=2.0,
        mode="raw-range",
    )

    assert invalid.readiness == "blocked"
    assert invalid.input_hash != raw.input_hash


def test_threat_range_toolkit_identity_includes_manual_inputs_and_measurement() -> None:
    packet = SAMPLE_PACKETS[0]
    base = build_threat_range_toolkit_result(
        packet,
        source_center=(16.0, 10.0),
        target_point=(24.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
        threat_range=2.0,
        mode="2d6-move-plus-range",
    )
    variants = [
        build_threat_range_toolkit_result(
            packet.model_copy(update={"name": f"{packet.name} revised"}),
            source_center=(16.0, 10.0),
            target_point=(24.0, 10.0),
            base_diameter=1.57,
            move_distance=6.0,
            threat_range=2.0,
            mode="2d6-move-plus-range",
        ),
        build_threat_range_toolkit_result(
            packet,
            source_center=(17.0, 10.0),
            target_point=(24.0, 10.0),
            base_diameter=1.57,
            move_distance=6.0,
            threat_range=2.0,
            mode="2d6-move-plus-range",
        ),
        build_threat_range_toolkit_result(
            packet,
            source_center=(16.0, 10.0),
            target_point=(25.0, 10.0),
            base_diameter=1.57,
            move_distance=6.0,
            threat_range=2.0,
            mode="2d6-move-plus-range",
        ),
        build_threat_range_toolkit_result(
            packet,
            source_center=(16.0, 10.0),
            target_point=(24.0, 10.0),
            base_diameter=2.0,
            move_distance=6.0,
            threat_range=2.0,
            mode="2d6-move-plus-range",
        ),
        build_threat_range_toolkit_result(
            packet,
            source_center=(16.0, 10.0),
            target_point=(24.0, 10.0),
            base_diameter=1.57,
            move_distance=7.0,
            threat_range=2.0,
            mode="2d6-move-plus-range",
        ),
        build_threat_range_toolkit_result(
            packet,
            source_center=(16.0, 10.0),
            target_point=(24.0, 10.0),
            base_diameter=1.57,
            move_distance=6.0,
            threat_range=3.0,
            mode="2d6-move-plus-range",
        ),
        build_threat_range_toolkit_result(
            packet,
            source_center=(16.0, 10.0),
            target_point=(24.0, 10.0),
            base_diameter=1.57,
            move_distance=6.0,
            threat_range=2.0,
            mode="d6-move-plus-range",
        ),
    ]

    hashes = {base.input_hash, *(variant.input_hash for variant in variants)}
    assert len(hashes) == 1 + len(variants)
    suffix = base.input_hash.removeprefix("sha256:")[:12]
    assert base.result_id.endswith(suffix)
    assert base.overlays[0].layer_id.endswith(suffix)


def _oversized_route_packet() -> MapPacket:
    terrain = TerrainArea(
        id="wall",
        label="Wall",
        kind=TerrainKind.RUINS,
        footprint=[(99.0, 0.0), (101.0, 0.0), (101.0, 200.0), (99.0, 200.0)],
    )
    dense = DenseTerrainFeature(
        id="dense-wall",
        terrain_area_id=terrain.id,
        label="Dense wall",
        footprint=terrain.footprint,
        profile="solid-los-blocker",
    )
    return MapPacket(
        id="oversized-route",
        name="Oversized Route",
        source="Synthetic oversized route fixture.",
        board=BoardSize(width=200.0, height=200.0),
        terrain_areas=[terrain],
        dense_features=[dense],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0.0, 0.0), (200.0, 0.0), (200.0, 20.0), (0.0, 20.0)],
            )
        ],
    )


def _empty_source_region_packet() -> MapPacket:
    return MapPacket(
        id="empty-source-region",
        name="Empty Source Region",
        source="Synthetic empty source region fixture.",
        board=BoardSize(width=10.0, height=10.0),
        terrain_areas=[],
        dense_features=[],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
            )
        ],
    )
