from __future__ import annotations

from shapely.geometry import Point

from warhammer_companion.domain.models import (
    BoardSize,
    DenseTerrainFeature,
    DeploymentZone,
    MapPacket,
    TerrainArea,
    TerrainKind,
)
from warhammer_companion.los.movement import movement_endpoint_diagnostic, movement_envelope


def test_movement_envelope_respects_board_edge_base_radius() -> None:
    packet = _movement_packet(dense_features=[])

    envelope = movement_envelope(
        packet,
        start_center=(5.0, 5.0),
        base_diameter=2.0,
        move_distance=99.0,
    )

    assert tuple(round(value, 3) for value in envelope.bounds) == (1.0, 1.0, 9.0, 9.0)
    assert envelope.covers(Point(1.0, 1.0))
    assert not envelope.covers(Point(0.99, 5.0))


def test_movement_envelope_excludes_dense_feature_buffered_for_base_radius() -> None:
    packet = _movement_packet()

    envelope = movement_envelope(
        packet,
        start_center=(2.0, 2.0),
        base_diameter=2.0,
        move_distance=10.0,
    )

    assert not envelope.covers(Point(6.0, 6.0))
    assert not envelope.covers(Point(4.25, 6.0))
    assert envelope.covers(Point(2.0, 8.0))


def test_endpoint_diagnostic_blocks_over_distance_targets() -> None:
    packet = _movement_packet(dense_features=[])

    diagnostic = movement_endpoint_diagnostic(
        packet,
        start_center=(2.0, 2.0),
        target_center=(8.1, 2.0),
        base_diameter=1.0,
        move_distance=6.0,
    )

    assert diagnostic.distance > 6.0
    assert not diagnostic.within_distance
    assert diagnostic.within_board
    assert diagnostic.clear_of_dense_features
    assert not diagnostic.estimated_reachable
    assert "target-outside-move-distance" in diagnostic.reason_ids


def test_endpoint_diagnostic_blocks_dense_swept_corridor_collision() -> None:
    packet = _movement_packet()

    diagnostic = movement_endpoint_diagnostic(
        packet,
        start_center=(2.0, 6.0),
        target_center=(9.0, 6.0),
        base_diameter=1.0,
        move_distance=8.0,
    )

    assert diagnostic.within_distance
    assert diagnostic.within_board
    assert not diagnostic.clear_of_dense_features
    assert not diagnostic.estimated_reachable
    assert "dense-feature-swept-corridor" in diagnostic.reason_ids


def test_endpoint_diagnostic_allows_clear_in_range_target_under_estimate() -> None:
    packet = _movement_packet()

    diagnostic = movement_endpoint_diagnostic(
        packet,
        start_center=(2.0, 2.0),
        target_center=(2.0, 8.0),
        base_diameter=1.0,
        move_distance=6.0,
    )

    assert diagnostic.distance == 6.0
    assert diagnostic.within_distance
    assert diagnostic.within_board
    assert diagnostic.clear_of_dense_features
    assert diagnostic.estimated_reachable
    assert diagnostic.reason_ids == ()


def _movement_packet(
    *,
    dense_features: list[DenseTerrainFeature] | None = None,
) -> MapPacket:
    terrain = TerrainArea(
        id="terrain-1",
        label="Terrain 1",
        kind=TerrainKind.RUINS,
        footprint=[(5.0, 5.0), (7.0, 5.0), (7.0, 7.0), (5.0, 7.0)],
    )
    return MapPacket(
        id="movement-test",
        name="Movement Test",
        source="Synthetic movement test fixture.",
        board=BoardSize(width=10.0, height=10.0),
        terrain_areas=[terrain],
        dense_features=(
            dense_features
            if dense_features is not None
            else [
                DenseTerrainFeature(
                    id="dense-1",
                    terrain_area_id=terrain.id,
                    label="Dense 1",
                    footprint=terrain.footprint,
                    profile="solid-los-blocker",
                )
            ]
        ),
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0.0, 0.0), (10.0, 0.0), (10.0, 2.0), (0.0, 2.0)],
            ),
            DeploymentZone(
                id="defender",
                label="Defender",
                footprint=[(0.0, 8.0), (10.0, 8.0), (10.0, 10.0), (0.0, 10.0)],
            ),
        ],
    )
