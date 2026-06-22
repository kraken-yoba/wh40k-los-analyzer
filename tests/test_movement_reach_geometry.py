from __future__ import annotations

from pathlib import Path

import pytest
from shapely.geometry import LineString, Point

from warhammer_companion.domain.models import (
    BoardSize,
    DenseTerrainFeature,
    DeploymentZone,
    MapPacket,
    TerrainArea,
    TerrainKind,
)
from warhammer_companion.domain.packet_io import load_packet_directory
from warhammer_companion.los.movement import (
    base_center_region,
    movement_endpoint_diagnostic,
    movement_envelope,
)


def test_base_center_region_respects_board_edge_base_radius() -> None:
    packet = _movement_packet(dense_features=[])

    region = base_center_region(packet, base_radius=1.0)

    assert tuple(round(value, 3) for value in region.bounds) == (1.0, 1.0, 9.0, 9.0)
    assert region.covers(Point(1.0, 1.0))
    assert not region.covers(Point(0.99, 5.0))


def test_base_center_region_collapses_oversized_base_to_board_center() -> None:
    packet = _movement_packet(dense_features=[])

    region = base_center_region(packet, base_radius=99.0)

    assert tuple(round(value, 3) for value in region.bounds) == (5.0, 5.0, 5.0, 5.0)
    assert region.covers(Point(5.0, 5.0))
    assert not region.covers(Point(5.01, 5.0))


def test_base_center_region_rejects_negative_base_radius() -> None:
    packet = _movement_packet(dense_features=[])

    with pytest.raises(ValueError, match="base_radius must be non-negative"):
        base_center_region(packet, base_radius=-0.1)


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

    assert not diagnostic.within_distance
    assert diagnostic.within_board
    assert diagnostic.clear_of_dense_features
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


def test_non_mobile_endpoint_routes_around_dense_feature_when_detour_is_in_budget() -> None:
    packet = _route_packet()

    diagnostic = movement_endpoint_diagnostic(
        packet,
        start_center=(2.0, 5.0),
        target_center=(8.0, 5.0),
        base_diameter=0.5,
        move_distance=8.5,
        movement_profile_id="ground-non-mobile",
    )

    assert diagnostic.distance == 6.0
    assert diagnostic.route_distance is not None
    assert diagnostic.route_distance > diagnostic.distance
    assert diagnostic.within_distance
    assert diagnostic.clear_of_dense_features
    assert diagnostic.estimated_reachable
    assert len(diagnostic.route_points) >= 3


def test_non_mobile_endpoint_blocks_dense_route_when_detour_is_over_budget() -> None:
    packet = _route_packet()

    diagnostic = movement_endpoint_diagnostic(
        packet,
        start_center=(2.0, 5.0),
        target_center=(8.0, 5.0),
        base_diameter=0.5,
        move_distance=6.1,
        movement_profile_id="ground-non-mobile",
    )

    assert diagnostic.distance <= 6.1
    assert diagnostic.route_distance is not None
    assert diagnostic.route_distance > 6.1
    assert not diagnostic.within_distance
    assert not diagnostic.estimated_reachable
    assert "target-outside-move-distance" in diagnostic.reason_ids


def test_non_mobile_route_edges_do_not_cross_dense_traversal_blocker() -> None:
    dense_wall = DenseTerrainFeature(
        id="dense-wall",
        terrain_area_id="wall",
        label="Dense wall",
        footprint=[(4.45, 0.0), (4.55, 0.0), (4.55, 10.0), (4.45, 10.0)],
        profile="solid-los-blocker",
    )
    packet = _route_packet(dense_features=[dense_wall])

    diagnostic = movement_endpoint_diagnostic(
        packet,
        start_center=(4.0, 5.0),
        target_center=(6.0, 5.0),
        base_diameter=0.1,
        move_distance=3.0,
        movement_profile_id="ground-non-mobile",
        routing_resolution=1.0,
    )

    assert not diagnostic.estimated_reachable
    assert "dense-feature-route-blocked" in diagnostic.reason_ids
    if diagnostic.route_points:
        route_line = LineString(diagnostic.route_points)
        assert not route_line.intersects(dense_wall.polygon().buffer(0.06))


def test_mobile_endpoint_ignores_dense_traversal_but_not_endpoint_occupancy() -> None:
    packet = _route_packet()

    through_dense = movement_endpoint_diagnostic(
        packet,
        start_center=(2.0, 5.0),
        target_center=(8.0, 5.0),
        base_diameter=0.5,
        move_distance=6.1,
        movement_profile_id="ground-mobile",
    )
    inside_dense = movement_endpoint_diagnostic(
        packet,
        start_center=(2.0, 5.0),
        target_center=(5.0, 5.0),
        base_diameter=0.5,
        move_distance=6.1,
        movement_profile_id="ground-mobile",
    )

    assert through_dense.estimated_reachable
    assert through_dense.route_distance == pytest.approx(6.0)
    assert not inside_dense.estimated_reachable
    assert "dense-feature-target-collision" in inside_dense.reason_ids


def test_fly_take_to_skies_ignores_dense_traversal_and_applies_penalty() -> None:
    packet = _route_packet()

    penalized = movement_endpoint_diagnostic(
        packet,
        start_center=(2.0, 5.0),
        target_center=(8.0, 5.0),
        base_diameter=0.5,
        move_distance=7.5,
        movement_profile_id="fly-take-to-skies",
    )
    hover = movement_endpoint_diagnostic(
        packet,
        start_center=(2.0, 5.0),
        target_center=(8.0, 5.0),
        base_diameter=0.5,
        move_distance=7.5,
        movement_profile_id="fly-hover-take-to-skies",
    )

    assert penalized.effective_move_distance == pytest.approx(5.5)
    assert not penalized.estimated_reachable
    assert hover.effective_move_distance == pytest.approx(7.5)
    assert hover.estimated_reachable


def test_terrain_areas_do_not_block_movement_without_dense_feature() -> None:
    terrain = TerrainArea(
        id="area-only",
        label="Area only",
        kind=TerrainKind.RUINS,
        footprint=[(4.0, 2.0), (6.0, 2.0), (6.0, 8.0), (4.0, 8.0)],
    )
    packet = _route_packet(terrain_areas=[terrain], dense_features=[])

    diagnostic = movement_endpoint_diagnostic(
        packet,
        start_center=(2.0, 5.0),
        target_center=(8.0, 5.0),
        base_diameter=0.5,
        move_distance=6.1,
        movement_profile_id="ground-non-mobile",
    )

    assert diagnostic.route_distance == pytest.approx(6.0)
    assert diagnostic.estimated_reachable


def test_official_page_9_page_52_movement_routing_smoke() -> None:
    packets = _official_seed_packets()

    for packet_id in ("official-event-companion-page-9", "official-event-companion-page-52"):
        packet = packets[packet_id]
        non_mobile = movement_endpoint_diagnostic(
            packet,
            start_center=(14.0, 32.75),
            target_center=(22.5, 32.75),
            base_diameter=1.57,
            move_distance=9.0,
            movement_profile_id="ground-non-mobile",
        )
        mobile = movement_endpoint_diagnostic(
            packet,
            start_center=(14.0, 32.75),
            target_center=(22.5, 32.75),
            base_diameter=1.57,
            move_distance=9.0,
            movement_profile_id="ground-mobile",
        )

        assert non_mobile.effective_move_distance == pytest.approx(9.0)
        assert mobile.effective_move_distance == pytest.approx(9.0)
        assert mobile.route_distance is not None
        assert mobile.routing_metadata.traversal_policy == "dense-features-ignored-for-traversal"
        if packet_id == "official-event-companion-page-9":
            assert not non_mobile.estimated_reachable
            assert mobile.estimated_reachable


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


def _official_seed_packets() -> dict[str, MapPacket]:
    seed_dir = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "warhammer_companion"
        / "seed_data"
        / "map-packets"
    )
    return {packet.id: packet for packet in load_packet_directory(seed_dir)}


def _route_packet(
    *,
    terrain_areas: list[TerrainArea] | None = None,
    dense_features: list[DenseTerrainFeature] | None = None,
) -> MapPacket:
    terrain = TerrainArea(
        id="route-terrain",
        label="Route Terrain",
        kind=TerrainKind.RUINS,
        footprint=[(4.0, 3.5), (6.0, 3.5), (6.0, 6.5), (4.0, 6.5)],
    )
    dense = DenseTerrainFeature(
        id="route-dense",
        terrain_area_id=terrain.id,
        label="Route Dense",
        footprint=terrain.footprint,
        profile="solid-los-blocker",
    )
    return MapPacket(
        id="movement-route-test",
        name="Movement Route Test",
        source="Synthetic route movement test fixture.",
        board=BoardSize(width=10.0, height=10.0),
        terrain_areas=terrain_areas if terrain_areas is not None else [terrain],
        dense_features=dense_features if dense_features is not None else [dense],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0.0, 0.0), (10.0, 0.0), (10.0, 2.0), (0.0, 2.0)],
            ),
        ],
    )
