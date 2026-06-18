from __future__ import annotations

from shapely.geometry import Point, Polygon

from warhammer_companion.domain.models import (
    DenseTerrainFeature,
    DeploymentZone,
    MapPacket,
    TerrainArea,
    TerrainKind,
)
from warhammer_companion.los.geometry import (
    binary_visibility_overlay_from_base,
    circular_base,
    deployment_edge_sample_points,
    heatmap_from_deployment_zone,
    heatmap_visibility_polygons_from_deployment_edge,
    heatmap_visibility_polygons_from_deployment_zone,
    is_line_blocked,
    visibility_polygon_from_base,
    visibility_rays_from_base,
)
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_line_is_blocked_by_intersecting_polygon() -> None:
    blocker = Polygon([(2, 2), (4, 2), (4, 4), (2, 4)])

    assert is_line_blocked((0, 3), (6, 3), [blocker])


def test_line_is_clear_when_it_misses_polygon() -> None:
    blocker = Polygon([(2, 2), (4, 2), (4, 4), (2, 4)])

    assert not is_line_blocked((0, 1), (6, 1), [blocker])


def test_base_area_can_be_ignored_for_own_position() -> None:
    blocker = Polygon([(1, 1), (3, 1), (3, 3), (1, 3)])
    base = circular_base((2, 2), 3.0)

    assert not is_line_blocked((2, 2), (2.5, 2.0), [blocker], ignored_area=base)


def test_heatmap_visibility_polygons_are_generated_from_deployment_samples() -> None:
    packet = SAMPLE_PACKETS[0]

    polygons = heatmap_visibility_polygons_from_deployment_zone(packet, "attacker")

    assert polygons
    assert all(not item.polygon.is_empty for item in polygons)


def test_deployment_edge_samples_bottom_zone_front_edge_and_offset() -> None:
    packet = SAMPLE_PACKETS[0]

    edge_samples = deployment_edge_sample_points(packet, "attacker", sample_step=11.0)
    offset_samples = deployment_edge_sample_points(
        packet,
        "attacker",
        sample_step=11.0,
        offset_inches=6,
    )

    assert edge_samples
    assert {round(sample[1], 2) for sample in edge_samples} == {10.0}
    assert {round(sample[1], 2) for sample in offset_samples} == {16.0}
    attacker_zone = packet.deployment_zone("attacker").polygon()
    assert all(attacker_zone.disjoint(Point(sample)) for sample in offset_samples)


def test_deployment_edge_samples_top_zone_offset_toward_board_center() -> None:
    packet = SAMPLE_PACKETS[0]

    edge_samples = deployment_edge_sample_points(packet, "defender", sample_step=11.0)
    offset_samples = deployment_edge_sample_points(
        packet,
        "defender",
        sample_step=11.0,
        offset_inches=6,
    )

    assert edge_samples
    assert {round(sample[1], 2) for sample in edge_samples} == {50.0}
    assert {round(sample[1], 2) for sample in offset_samples} == {44.0}
    defender_zone = packet.deployment_zone("defender").polygon()
    assert all(defender_zone.disjoint(Point(sample)) for sample in offset_samples)


def test_deployment_edge_samples_ignore_near_board_edges_from_extraction_noise() -> None:
    packet = MapPacket(
        id="near-boundary-zone",
        name="Near Boundary Zone",
        source="Geometry unit test fixture.",
        terrain_areas=[],
        dense_features=[],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[
                    (0.04, 50.02),
                    (43.96, 50.02),
                    (43.96, 59.95),
                    (0.04, 59.95),
                ],
            )
        ],
    )

    edge_samples = deployment_edge_sample_points(packet, "attacker", sample_step=50.0)
    offset_samples = deployment_edge_sample_points(
        packet,
        "attacker",
        sample_step=50.0,
        offset_inches=6,
    )

    assert {round(sample[1], 2) for sample in edge_samples} == {50.02}
    assert {round(sample[1], 2) for sample in offset_samples} == {44.02}
    attacker_zone = packet.deployment_zone("attacker").polygon()
    assert all(attacker_zone.disjoint(Point(sample)) for sample in offset_samples)


def test_heatmap_visibility_polygons_can_use_offset_deployment_edge() -> None:
    packet = SAMPLE_PACKETS[0]

    polygons = heatmap_visibility_polygons_from_deployment_edge(
        packet,
        "attacker",
        sample_step=11.0,
        offset_inches=6,
    )

    assert polygons
    assert {round(item.origin[1], 2) for item in polygons} == {16.0}
    assert all(not item.polygon.is_empty for item in polygons)


def test_heatmap_returns_cells_for_sample_packet() -> None:
    packet = SAMPLE_PACKETS[0]

    cells = heatmap_from_deployment_zone(packet, "attacker", grid_step=8.0, sample_step=8.0)

    assert cells
    assert all(0.0 <= cell.visibility <= 1.0 for cell in cells)


def test_default_heatmap_uses_one_inch_cells() -> None:
    packet = SAMPLE_PACKETS[0]

    cells = heatmap_from_deployment_zone(packet, "attacker")

    assert len(cells) == int(packet.board.width * packet.board.height)


def test_binary_visibility_overlay_returns_board_cells() -> None:
    packet = SAMPLE_PACKETS[0]

    cells = binary_visibility_overlay_from_base(packet, center=(22.0, 10.0), base_diameter=1.57)

    assert len(cells) == int(packet.board.width * packet.board.height)
    assert any(cell.visible for cell in cells)
    assert any(not cell.visible for cell in cells)


def test_base_not_touching_terrain_footprint_can_see_into_but_not_through_it() -> None:
    packet = _single_ruin_packet()

    polygon = visibility_polygon_from_base(packet, center=(13.0, 30.0), base_diameter=1.57)

    assert polygon.covers(Point(16.0, 30.0))
    assert not polygon.covers(Point(35.0, 54.0))


def test_base_not_touching_terrain_footprint_still_blocked_by_dense_feature() -> None:
    packet = _single_ruin_packet()

    polygon = visibility_polygon_from_base(packet, center=(13.0, 30.0), base_diameter=1.57)

    assert not polygon.covers(Point(27.0, 30.0))


def test_binary_visibility_overlay_can_see_into_but_not_through_footprint() -> None:
    packet = _single_ruin_packet()

    cells = binary_visibility_overlay_from_base(packet, center=(13.0, 30.0), base_diameter=1.57)
    by_position = {(cell.x, cell.y): cell.visible for cell in cells}

    assert by_position[(16.5, 30.5)]
    assert not by_position[(35.5, 54.5)]


def test_heatmap_visibility_polygons_can_see_into_but_not_through_footprint() -> None:
    packet = _side_deployment_single_ruin_packet()

    polygons = heatmap_visibility_polygons_from_deployment_edge(
        packet,
        "attacker",
        sample_step=100.0,
    )

    assert any(item.polygon.covers(Point(16.0, 30.0)) for item in polygons)
    assert all(not item.polygon.covers(Point(35.0, 54.0)) for item in polygons)
    assert all(not item.polygon.covers(Point(27.0, 30.0)) for item in polygons)


def test_grid_heatmap_can_see_into_but_not_through_footprint() -> None:
    packet = _point_deployment_single_ruin_packet()

    cells = heatmap_from_deployment_zone(packet, "attacker")
    by_position = {(cell.x, cell.y): cell.visibility for cell in cells}

    assert by_position[(16.5, 30.5)] == 1.0
    assert by_position[(27.5, 30.5)] == 0.0
    assert by_position[(35.5, 54.5)] == 0.0


def test_visibility_rays_apply_footprint_shadow_touching_and_dense_blockers() -> None:
    packet = _single_ruin_packet()

    outside_rays = visibility_rays_from_base(packet, center=(13.0, 30.0), base_diameter=1.57)
    touching_rays = visibility_rays_from_base(packet, center=(14.25, 30.0), base_diameter=1.57)
    outside_by_target = {ray.target: ray.visible for ray in outside_rays}
    touching_by_target = {ray.target: ray.visible for ray in touching_rays}

    assert not outside_by_target[(42.0, 60.0)]
    assert touching_by_target[(42.0, 60.0)]
    assert not touching_by_target[(44.0, 30.0)]


def test_concave_terrain_shadow_preserves_visible_notch() -> None:
    packet = _concave_ruin_packet()

    polygon = visibility_polygon_from_base(packet, center=(10.0, 35.0), base_diameter=1.57)

    assert polygon.covers(Point(20.0, 30.0))
    assert not polygon.covers(Point(35.0, 35.0))


def test_concave_terrain_shadow_stops_at_first_intersection_interval() -> None:
    packet = _u_shaped_ruin_packet()

    polygon = visibility_polygon_from_base(packet, center=(10.0, 30.0), base_diameter=1.57)

    assert not polygon.covers(Point(25.0, 30.0))


def test_base_touching_terrain_footprint_sees_through_that_footprint() -> None:
    packet = _single_ruin_packet()

    outside_polygon = visibility_polygon_from_base(packet, center=(13.0, 30.0), base_diameter=1.57)
    touching_polygon = visibility_polygon_from_base(
        packet, center=(14.25, 30.0), base_diameter=1.57
    )

    target_through_footprint = Point(35.0, 54.0)
    assert not outside_polygon.covers(target_through_footprint)
    assert touching_polygon.covers(target_through_footprint)


def test_base_touching_terrain_footprint_still_blocked_by_dense_feature() -> None:
    packet = _single_ruin_packet()

    touching_polygon = visibility_polygon_from_base(
        packet, center=(14.25, 30.0), base_diameter=1.57
    )

    target_behind_dense_feature = Point(35.0, 30.0)
    assert not touching_polygon.covers(target_behind_dense_feature)


def test_visibility_rays_include_visible_and_blocked_results() -> None:
    packet = SAMPLE_PACKETS[0]

    rays = visibility_rays_from_base(packet, center=(22.0, 10.0), base_diameter=1.57)

    assert rays
    assert any(ray.visible for ray in rays)
    assert any(not ray.visible for ray in rays)


def _single_ruin_packet() -> MapPacket:
    return MapPacket(
        id="single-ruin",
        name="Single Ruin",
        source="LOS geometry unit test fixture.",
        terrain_areas=[
            TerrainArea(
                id="c",
                label="C",
                kind=TerrainKind.RUINS,
                footprint=[(15, 24), (29, 24), (29, 36), (15, 36)],
            )
        ],
        dense_features=[
            DenseTerrainFeature(
                id="c-dense",
                terrain_area_id="c",
                label="C dense",
                footprint=[(18, 26), (26, 26), (26, 34), (18, 34)],
            )
        ],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0, 0), (44, 0), (44, 10), (0, 10)],
            )
        ],
    )


def _side_deployment_single_ruin_packet() -> MapPacket:
    packet = _single_ruin_packet()
    return packet.model_copy(
        update={
            "deployment_zones": [
                DeploymentZone(
                    id="attacker",
                    label="Attacker",
                    footprint=[(0, 0), (13, 0), (13, 60), (0, 60)],
                )
            ]
        }
    )


def _point_deployment_single_ruin_packet() -> MapPacket:
    packet = _single_ruin_packet()
    return packet.model_copy(
        update={
            "deployment_zones": [
                DeploymentZone(
                    id="attacker",
                    label="Attacker",
                    footprint=[(12.5, 29.5), (13.5, 29.5), (13.5, 30.5), (12.5, 30.5)],
                )
            ]
        }
    )


def _concave_ruin_packet() -> MapPacket:
    return MapPacket(
        id="concave-ruin",
        name="Concave Ruin",
        source="LOS geometry unit test fixture.",
        terrain_areas=[
            TerrainArea(
                id="l",
                label="L",
                kind=TerrainKind.RUINS,
                footprint=[(15, 20), (30, 20), (30, 40), (25, 40), (25, 25), (15, 25)],
            )
        ],
        dense_features=[],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0, 0), (44, 0), (44, 10), (0, 10)],
            )
        ],
    )


def _u_shaped_ruin_packet() -> MapPacket:
    return MapPacket(
        id="u-ruin",
        name="U Ruin",
        source="LOS geometry unit test fixture.",
        terrain_areas=[
            TerrainArea(
                id="u",
                label="U",
                kind=TerrainKind.RUINS,
                footprint=[
                    (15, 20),
                    (30, 20),
                    (30, 40),
                    (25, 40),
                    (25, 25),
                    (20, 25),
                    (20, 40),
                    (15, 40),
                ],
            )
        ],
        dense_features=[],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0, 0), (44, 0), (44, 10), (0, 10)],
            )
        ],
    )
