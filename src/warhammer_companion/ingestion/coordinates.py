from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from shapely.geometry import Polygon

Point = tuple[float, float]


@dataclass(frozen=True)
class BoardTransform:
    board_rect: tuple[float, float, float, float]
    board_width_inches: float = 44.0
    board_height_inches: float = 60.0

    def __post_init__(self) -> None:
        left, top, right, bottom = self.board_rect
        if right <= left:
            raise ValueError("board_rect right must be greater than left")
        if bottom <= top:
            raise ValueError("board_rect bottom must be greater than top")
        if self.board_width_inches <= 0:
            raise ValueError("board_width_inches must be positive")
        if self.board_height_inches <= 0:
            raise ValueError("board_height_inches must be positive")

    @property
    def left(self) -> float:
        return self.board_rect[0]

    @property
    def top(self) -> float:
        return self.board_rect[1]

    @property
    def right(self) -> float:
        return self.board_rect[2]

    @property
    def bottom(self) -> float:
        return self.board_rect[3]

    @property
    def width_px(self) -> float:
        return self.right - self.left

    @property
    def height_px(self) -> float:
        return self.bottom - self.top

    def image_to_board_point(self, point: Point) -> Point:
        return image_to_board_point(point, self)


def image_to_board_point(point: Point, transform: BoardTransform) -> Point:
    x, y = point
    board_x = (x - transform.left) * transform.board_width_inches / transform.width_px
    board_y = (transform.bottom - y) * transform.board_height_inches / transform.height_px
    return (board_x, board_y)


def image_contour_to_board_polygon(
    contour: Sequence[Any],
    transform: BoardTransform,
) -> Polygon:
    points = [image_to_board_point(_contour_point(point), transform) for point in contour]
    if len(points) < 3:
        raise ValueError("contour must contain at least three points")

    polygon = Polygon(points)
    if polygon.is_empty:
        raise ValueError("contour produced an empty polygon")
    return polygon


def snap_polygon(polygon: Polygon, *, increment: float = 0.25) -> Polygon:
    if increment <= 0:
        raise ValueError("increment must be positive")

    exterior = [_snap_point(point, increment) for point in polygon.exterior.coords]
    interiors = [
        [_snap_point(point, increment) for point in interior.coords]
        for interior in polygon.interiors
    ]
    return Polygon(exterior, interiors)


def _contour_point(raw_point: Any) -> Point:
    point = raw_point.tolist() if hasattr(raw_point, "tolist") else raw_point
    while _is_single_nested_point(point):
        point = point[0]
    if not isinstance(point, Sequence) or len(point) < 2:
        raise ValueError(f"invalid contour point: {raw_point!r}")
    return (float(point[0]), float(point[1]))


def _is_single_nested_point(point: Any) -> bool:
    return isinstance(point, Sequence) and len(point) == 1 and isinstance(point[0], Sequence)


def _snap_point(point: Sequence[float], increment: float) -> Point:
    return (_snap_value(float(point[0]), increment), _snap_value(float(point[1]), increment))


def _snap_value(value: float, increment: float) -> float:
    snapped = round(value / increment) * increment
    return round(snapped, 6)
