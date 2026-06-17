from __future__ import annotations

from shapely.geometry import Polygon

from warhammer_companion.los.geometry import (
    binary_visibility_overlay_from_base,
    circular_base,
    heatmap_from_deployment_zone,
    is_line_blocked,
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


def test_visibility_rays_include_visible_and_blocked_results() -> None:
    packet = SAMPLE_PACKETS[0]

    rays = visibility_rays_from_base(packet, center=(22.0, 10.0), base_diameter=1.57)

    assert rays
    assert any(ray.visible for ray in rays)
    assert any(not ray.visible for ray in rays)
