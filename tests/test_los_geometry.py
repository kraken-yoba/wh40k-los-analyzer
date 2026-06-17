from __future__ import annotations

from shapely.geometry import Point, Polygon

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


def test_base_touching_terrain_footprint_sees_through_that_footprint() -> None:
    packet = SAMPLE_PACKETS[0]

    outside_polygon = visibility_polygon_from_base(packet, center=(13.0, 30.0), base_diameter=1.57)
    touching_polygon = visibility_polygon_from_base(
        packet, center=(14.25, 30.0), base_diameter=1.57
    )

    target_behind_c = Point(35.0, 30.0)
    assert not outside_polygon.covers(target_behind_c)
    assert touching_polygon.covers(target_behind_c)


def test_visibility_rays_include_visible_and_blocked_results() -> None:
    packet = SAMPLE_PACKETS[0]

    rays = visibility_rays_from_base(packet, center=(22.0, 10.0), base_diameter=1.57)

    assert rays
    assert any(ray.visible for ray in rays)
    assert any(not ray.visible for ray in rays)
