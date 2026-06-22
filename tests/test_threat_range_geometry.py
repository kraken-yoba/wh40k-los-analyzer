from __future__ import annotations

from pathlib import Path

import pytest
from shapely.geometry import Point, box

from warhammer_companion.domain.models import (
    BoardSize,
    DenseTerrainFeature,
    DeploymentZone,
    MapPacket,
    TerrainArea,
    TerrainKind,
)
from warhammer_companion.domain.packet_io import load_packet_directory
from warhammer_companion.los.exposure import allowed_deployment_center_region
from warhammer_companion.los.movement import movement_envelope_from_region
from warhammer_companion.los.threat import (
    target_threat_probability,
    threat_distribution,
    threat_projection,
    threat_projection_regions,
    threat_projection_regions_from_source_region,
    threat_reach_probability,
)


def test_raw_threat_projection_uses_source_base_edge_to_target_point_convention() -> None:
    packet = _threat_packet()

    projection = threat_projection(
        packet,
        source_center=(2.0, 2.0),
        base_diameter=2.0,
        move_distance=6.0,
        threat_range=3.0,
        mode="raw-range",
    )

    assert projection.covers(Point(6.0, 2.0))
    assert not projection.covers(Point(6.2, 2.0))


def test_fixed_move_plus_range_respects_dense_movement_blocker() -> None:
    packet = _threat_packet()

    projection = threat_projection(
        packet,
        source_center=(2.0, 6.0),
        base_diameter=1.0,
        move_distance=8.0,
        threat_range=0.1,
        mode="fixed-move-plus-range",
    )

    assert not projection.covers(Point(6.0, 6.0))
    assert projection.covers(Point(3.0, 6.0))


def test_fixed_move_plus_range_allows_zero_fixed_movement_without_crashing() -> None:
    packet = _threat_packet(dense_features=[])

    projection = threat_projection(
        packet,
        source_center=(2.0, 2.0),
        base_diameter=2.0,
        move_distance=0.0,
        threat_range=3.0,
        mode="fixed-move-plus-range",
    )

    assert projection.covers(Point(6.0, 2.0))
    assert not projection.covers(Point(6.2, 2.0))


def test_d6_distribution_has_exact_equal_probabilities_and_reach_budgets() -> None:
    distribution = threat_distribution(
        mode="d6-move-plus-range",
        move_distance=6.0,
        threat_range=2.0,
        base_diameter=1.0,
    )

    assert [outcome.variable_inches for outcome in distribution] == [1, 2, 3, 4, 5, 6]
    assert [outcome.dice_label for outcome in distribution] == ["D6"] * 6
    assert all(outcome.probability == pytest.approx(1.0 / 6.0) for outcome in distribution)
    assert distribution[0].total_reach == pytest.approx(9.5)
    assert distribution[-1].total_reach == pytest.approx(14.5)


def test_2d6_distribution_has_exact_counts_and_threshold_probabilities() -> None:
    distribution = threat_distribution(
        mode="2d6-move-plus-range",
        move_distance=6.0,
        threat_range=2.0,
        base_diameter=2.0,
    )

    assert [outcome.variable_inches for outcome in distribution] == list(range(2, 13))
    assert [outcome.numerator for outcome in distribution] == [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
    assert sum(outcome.probability for outcome in distribution) == pytest.approx(1.0)
    assert threat_reach_probability(distribution, threshold_inches=8.0) == pytest.approx(1.0)
    assert threat_reach_probability(distribution, threshold_inches=22.0) == pytest.approx(0.0)
    assert threat_reach_probability(distribution, threshold_inches=17.0) == pytest.approx(
        15.0 / 36.0
    )
    assert threat_reach_probability(
        distribution, threshold_inches=16.0
    ) >= threat_reach_probability(
        distribution,
        threshold_inches=17.0,
    )


def test_target_threat_probability_accumulates_exact_regions() -> None:
    packet = _threat_packet()
    regions = threat_projection_regions(
        packet,
        source_center=(2.0, 2.0),
        base_diameter=2.0,
        move_distance=1.0,
        threat_range=0.0,
        mode="d6-move-plus-range",
    )

    assert target_threat_probability(regions, target_point=(4.0, 2.0)) == pytest.approx(1.0)
    assert target_threat_probability(regions, target_point=(9.9, 2.0)) == pytest.approx(1.0 / 6.0)
    assert target_threat_probability(regions, target_point=(10.2, 2.0)) == pytest.approx(0.0)


def test_raw_range_projection_is_profile_invariant() -> None:
    packet = _threat_route_packet()

    non_mobile = threat_projection(
        packet,
        source_center=(2.0, 5.0),
        base_diameter=0.5,
        move_distance=8.0,
        threat_range=1.0,
        mode="raw-range",
        movement_profile_id="ground-non-mobile",
    )
    mobile = threat_projection(
        packet,
        source_center=(2.0, 5.0),
        base_diameter=0.5,
        move_distance=8.0,
        threat_range=1.0,
        mode="raw-range",
        movement_profile_id="ground-mobile",
    )

    assert non_mobile.equals_exact(mobile, tolerance=0.001)


def test_move_plus_range_uses_profile_aware_point_probability() -> None:
    packet = _threat_route_packet()

    non_mobile_regions = threat_projection_regions(
        packet,
        source_center=(2.0, 5.0),
        base_diameter=0.5,
        move_distance=6.1,
        threat_range=0.1,
        mode="fixed-move-plus-range",
        movement_profile_id="ground-non-mobile",
    )
    mobile_regions = threat_projection_regions(
        packet,
        source_center=(2.0, 5.0),
        base_diameter=0.5,
        move_distance=6.1,
        threat_range=0.1,
        mode="fixed-move-plus-range",
        movement_profile_id="ground-mobile",
    )

    target = (8.2, 5.0)
    assert target_threat_probability(non_mobile_regions, target_point=target) == pytest.approx(0.0)
    assert target_threat_probability(mobile_regions, target_point=target) == pytest.approx(1.0)


def test_fly_penalty_and_hover_profile_change_threat_probability() -> None:
    packet = _threat_route_packet()

    penalized_regions = threat_projection_regions(
        packet,
        source_center=(2.0, 5.0),
        base_diameter=0.5,
        move_distance=7.5,
        threat_range=0.1,
        mode="fixed-move-plus-range",
        movement_profile_id="fly-take-to-skies",
    )
    hover_regions = threat_projection_regions(
        packet,
        source_center=(2.0, 5.0),
        base_diameter=0.5,
        move_distance=7.5,
        threat_range=0.1,
        mode="fixed-move-plus-range",
        movement_profile_id="fly-hover-take-to-skies",
    )

    target = (8.2, 5.0)
    assert target_threat_probability(penalized_regions, target_point=target) == pytest.approx(0.0)
    assert target_threat_probability(hover_regions, target_point=target) == pytest.approx(1.0)


def test_threat_distribution_records_effective_move_after_fly_penalty() -> None:
    distribution = threat_distribution(
        mode="fixed-move-plus-range",
        move_distance=7.5,
        threat_range=0.5,
        base_diameter=1.0,
        movement_profile_id="fly-take-to-skies",
    )

    assert distribution[0].effective_move_distance == pytest.approx(5.5)
    assert distribution[0].total_reach == pytest.approx(6.5)


def test_zero_move_source_region_movement_returns_endpoint_clear_source_region() -> None:
    packet = _deployment_threat_route_packet()
    source_region = allowed_deployment_center_region(
        packet,
        deployment_zone_id="attacker",
        base_radius=0.25,
    )

    envelope = movement_envelope_from_region(
        packet,
        source_center_region=source_region,
        base_diameter=0.5,
        move_distance=0.0,
        movement_profile_id="ground-mobile",
    )

    assert envelope.covers(Point(2.0, 5.0))
    assert not envelope.covers(Point(3.5, 5.0))


def test_raw_threat_projection_from_source_region_buffers_source_region() -> None:
    packet = _deployment_threat_route_packet()
    source_region = allowed_deployment_center_region(
        packet,
        deployment_zone_id="attacker",
        base_radius=0.25,
    )

    regions = threat_projection_regions_from_source_region(
        packet,
        source_center_region=source_region,
        base_diameter=0.5,
        move_distance=9.0,
        threat_range=1.0,
        mode="raw-range",
        movement_profile_id="fly-take-to-skies",
    )

    expected = source_region.buffer(1.25).intersection(box(0.0, 0.0, 10.0, 10.0)).buffer(0)
    assert len(regions) == 1
    assert regions[0].geometry.normalize().equals_exact(expected.normalize(), tolerance=0.001)


def test_move_plus_range_from_source_region_uses_profile_aware_routing() -> None:
    packet = _deployment_threat_route_packet()
    source_region = allowed_deployment_center_region(
        packet,
        deployment_zone_id="attacker",
        base_radius=0.25,
    )
    target = (8.2, 5.0)

    non_mobile_regions = threat_projection_regions_from_source_region(
        packet,
        source_center_region=source_region,
        base_diameter=0.5,
        move_distance=5.2,
        threat_range=0.1,
        mode="fixed-move-plus-range",
        movement_profile_id="ground-non-mobile",
    )
    mobile_regions = threat_projection_regions_from_source_region(
        packet,
        source_center_region=source_region,
        base_diameter=0.5,
        move_distance=5.2,
        threat_range=0.1,
        mode="fixed-move-plus-range",
        movement_profile_id="ground-mobile",
    )

    assert target_threat_probability(non_mobile_regions, target_point=target) == pytest.approx(0.0)
    assert target_threat_probability(mobile_regions, target_point=target) == pytest.approx(1.0)


def test_fly_penalty_changes_source_region_threat_probability() -> None:
    packet = _deployment_threat_route_packet()
    source_region = allowed_deployment_center_region(
        packet,
        deployment_zone_id="attacker",
        base_radius=0.25,
    )
    target = (8.2, 5.0)

    penalized_regions = threat_projection_regions_from_source_region(
        packet,
        source_center_region=source_region,
        base_diameter=0.5,
        move_distance=5.5,
        threat_range=0.1,
        mode="fixed-move-plus-range",
        movement_profile_id="fly-take-to-skies",
    )
    hover_regions = threat_projection_regions_from_source_region(
        packet,
        source_center_region=source_region,
        base_diameter=0.5,
        move_distance=5.5,
        threat_range=0.1,
        mode="fixed-move-plus-range",
        movement_profile_id="fly-hover-take-to-skies",
    )

    assert target_threat_probability(penalized_regions, target_point=target) == pytest.approx(0.0)
    assert target_threat_probability(hover_regions, target_point=target) == pytest.approx(1.0)


def test_official_page_9_page_52_threat_routing_smoke() -> None:
    packets = _official_seed_packets()

    for packet_id in ("official-event-companion-page-9", "official-event-companion-page-52"):
        packet = packets[packet_id]
        non_mobile_regions = threat_projection_regions(
            packet,
            source_center=(14.0, 32.75),
            base_diameter=1.57,
            move_distance=9.0,
            threat_range=0.5,
            mode="fixed-move-plus-range",
            movement_profile_id="ground-non-mobile",
        )
        mobile_regions = threat_projection_regions(
            packet,
            source_center=(14.0, 32.75),
            base_diameter=1.57,
            move_distance=9.0,
            threat_range=0.5,
            mode="fixed-move-plus-range",
            movement_profile_id="ground-mobile",
        )

        assert len(non_mobile_regions) == 1
        assert len(mobile_regions) == 1
        assert non_mobile_regions[0].outcome.effective_move_distance == pytest.approx(9.0)
        assert mobile_regions[0].outcome.effective_move_distance == pytest.approx(9.0)
        if packet_id == "official-event-companion-page-9":
            target = (22.5, 32.75)
            assert target_threat_probability(non_mobile_regions, target_point=target) == (
                pytest.approx(0.0)
            )
            assert target_threat_probability(mobile_regions, target_point=target) == pytest.approx(
                1.0
            )


def test_deployment_zone_source_page_9_threat_projection_smoke() -> None:
    packet = _official_seed_packets()["official-event-companion-page-9"]
    source_region = allowed_deployment_center_region(
        packet,
        deployment_zone_id="attacker",
        base_radius=1.57 / 2.0,
    )

    regions = threat_projection_regions_from_source_region(
        packet,
        source_center_region=source_region,
        base_diameter=1.57,
        move_distance=9.0,
        threat_range=0.5,
        mode="fixed-move-plus-range",
        movement_profile_id="ground-mobile",
    )

    assert len(regions) == 1
    assert not regions[0].geometry.is_empty


def test_deployment_zone_source_page_52_threat_projection_smoke() -> None:
    packet = _official_seed_packets()["official-event-companion-page-52"]
    source_region = allowed_deployment_center_region(
        packet,
        deployment_zone_id="defender",
        base_radius=1.57 / 2.0,
    )

    regions = threat_projection_regions_from_source_region(
        packet,
        source_center_region=source_region,
        base_diameter=1.57,
        move_distance=9.0,
        threat_range=0.5,
        mode="fixed-move-plus-range",
        movement_profile_id="ground-mobile",
    )

    assert len(regions) == 1
    assert not regions[0].geometry.is_empty


def _threat_packet(
    dense_features: list[DenseTerrainFeature] | None = None,
) -> MapPacket:
    return MapPacket(
        id="threat-test",
        name="Threat Test",
        source="unit test",
        board=BoardSize(width=10.0, height=10.0),
        terrain_areas=[
            TerrainArea(
                id="ruin",
                label="Ruin",
                kind=TerrainKind.RUINS,
                footprint=[(5.0, 5.0), (7.0, 5.0), (7.0, 7.0), (5.0, 7.0)],
            )
        ],
        dense_features=dense_features
        if dense_features is not None
        else [
            DenseTerrainFeature(
                id="dense",
                terrain_area_id="ruin",
                label="Dense",
                footprint=[(5.0, 5.0), (7.0, 5.0), (7.0, 7.0), (5.0, 7.0)],
                profile="container_or_solid",
            )
        ],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0.0, 0.0), (10.0, 0.0), (10.0, 2.0), (0.0, 2.0)],
            )
        ],
    )


def _official_seed_packets() -> dict[str, MapPacket]:
    seed_dir = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "warhammer_companion"
        / "seed_data"
        / "map-packets"
    )
    return {packet.id: packet for packet in load_packet_directory(seed_dir)}


def _threat_route_packet() -> MapPacket:
    terrain = TerrainArea(
        id="route-ruin",
        label="Route Ruin",
        kind=TerrainKind.RUINS,
        footprint=[(4.0, 3.5), (6.0, 3.5), (6.0, 6.5), (4.0, 6.5)],
    )
    return MapPacket(
        id="threat-route-test",
        name="Threat Route Test",
        source="unit test",
        board=BoardSize(width=10.0, height=10.0),
        terrain_areas=[terrain],
        dense_features=[
            DenseTerrainFeature(
                id="route-dense",
                terrain_area_id=terrain.id,
                label="Route Dense",
                footprint=terrain.footprint,
                profile="container_or_solid",
            )
        ],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0.0, 0.0), (10.0, 0.0), (10.0, 2.0), (0.0, 2.0)],
            )
        ],
    )


def _deployment_threat_route_packet() -> MapPacket:
    terrain = TerrainArea(
        id="route-ruin",
        label="Route Ruin",
        kind=TerrainKind.RUINS,
        footprint=[(4.0, 3.5), (6.0, 3.5), (6.0, 6.5), (4.0, 6.5)],
    )
    return MapPacket(
        id="deployment-threat-route-test",
        name="Deployment Threat Route Test",
        source="unit test",
        board=BoardSize(width=10.0, height=10.0),
        terrain_areas=[terrain],
        dense_features=[
            DenseTerrainFeature(
                id="route-dense",
                terrain_area_id=terrain.id,
                label="Route Dense",
                footprint=terrain.footprint,
                profile="container_or_solid",
            )
        ],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0.5, 4.0), (3.0, 4.0), (3.0, 6.0), (0.5, 6.0)],
            ),
            DeploymentZone(
                id="defender",
                label="Defender",
                footprint=[(7.0, 4.0), (9.5, 4.0), (9.5, 6.0), (7.0, 6.0)],
            ),
        ],
    )
