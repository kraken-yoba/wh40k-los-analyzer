from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from warhammer_companion.ingestion.coordinates import (
    BoardTransform,
    image_contour_to_board_polygon,
    image_to_board_point,
    snap_polygon,
)


def test_image_to_board_point_converts_top_left_image_to_lower_left_board_inches() -> None:
    transform = BoardTransform(board_rect=(100.0, 50.0, 540.0, 650.0))

    assert image_to_board_point((100.0, 650.0), transform) == (0.0, 0.0)
    assert image_to_board_point((540.0, 50.0), transform) == (44.0, 60.0)
    assert image_to_board_point((320.0, 350.0), transform) == (22.0, 30.0)


def test_image_to_board_point_inverts_y_axis() -> None:
    transform = BoardTransform(board_rect=(0.0, 0.0, 440.0, 600.0))

    lower_point = image_to_board_point((220.0, 500.0), transform)
    upper_point = image_to_board_point((220.0, 100.0), transform)

    assert lower_point == (22.0, 10.0)
    assert upper_point == (22.0, 50.0)


def test_image_contour_to_board_polygon_converts_contours_to_valid_polygons() -> None:
    transform = BoardTransform(board_rect=(0.0, 0.0, 440.0, 600.0))
    contour = [(0.0, 600.0), (110.0, 600.0), (110.0, 450.0), (0.0, 450.0)]

    polygon = image_contour_to_board_polygon(contour, transform)

    assert isinstance(polygon, Polygon)
    assert polygon.is_valid
    assert list(polygon.exterior.coords) == [
        (0.0, 0.0),
        (11.0, 0.0),
        (11.0, 15.0),
        (0.0, 15.0),
        (0.0, 0.0),
    ]


def test_board_transform_rejects_invalid_rectangles() -> None:
    with pytest.raises(ValueError, match="right must be greater than left"):
        BoardTransform(board_rect=(10.0, 0.0, 10.0, 60.0))

    with pytest.raises(ValueError, match="bottom must be greater than top"):
        BoardTransform(board_rect=(0.0, 10.0, 44.0, 10.0))


def test_image_contour_to_board_polygon_rejects_short_contours() -> None:
    transform = BoardTransform(board_rect=(0.0, 0.0, 440.0, 600.0))

    with pytest.raises(ValueError, match="at least three points"):
        image_contour_to_board_polygon([(0.0, 0.0), (1.0, 1.0)], transform)


def test_snap_polygon_rounds_coordinates_to_quarter_inches() -> None:
    polygon = Polygon(
        [
            (0.12, 0.13),
            (10.37, 0.12),
            (10.38, 4.88),
            (0.11, 4.89),
        ]
    )

    snapped = snap_polygon(polygon, increment=0.25)

    assert list(snapped.exterior.coords) == [
        (0.0, 0.25),
        (10.25, 0.0),
        (10.5, 5.0),
        (0.0, 5.0),
        (0.0, 0.25),
    ]
