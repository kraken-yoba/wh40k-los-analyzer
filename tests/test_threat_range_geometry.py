from __future__ import annotations

import pytest
from shapely.geometry import Point

from warhammer_companion.domain.models import (
    BoardSize,
    DenseTerrainFeature,
    DeploymentZone,
    MapPacket,
    TerrainArea,
    TerrainKind,
)
from warhammer_companion.los.threat import (
    target_threat_probability,
    threat_distribution,
    threat_projection,
    threat_projection_regions,
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
