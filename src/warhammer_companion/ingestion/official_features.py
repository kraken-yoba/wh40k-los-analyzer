from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry import Point as ShapelyPoint

from warhammer_companion.ingestion.coordinates import BoardTransform, image_to_board_point

Point = tuple[float, float]
BBox = tuple[float, float, float, float]
WallSide = Literal["left", "right", "top", "bottom"]
OfficialFeatureCode = Literal["AB", "CD", "EF", "GH"]
OfficialFeatureProfile = Literal["ruined_wall_l", "ruined_wall_u", "ruined_wall_perimeter"]
OFFICIAL_FEATURE_CODES: tuple[OfficialFeatureCode, ...] = ("AB", "CD", "EF", "GH")


@dataclass(frozen=True)
class OfficialFeatureTemplate:
    profile: OfficialFeatureProfile
    width: float
    height: float


@dataclass(frozen=True)
class OfficialFeatureLabel:
    code: OfficialFeatureCode
    bbox: BBox


@dataclass(frozen=True)
class OrientedFrame:
    x_axis: Point
    y_axis: Point


OFFICIAL_FEATURE_TEMPLATES: dict[OfficialFeatureCode, OfficialFeatureTemplate] = {
    "AB": OfficialFeatureTemplate("ruined_wall_l", width=5.0, height=4.5),
    "CD": OfficialFeatureTemplate("ruined_wall_l", width=6.0, height=4.5),
    "EF": OfficialFeatureTemplate("ruined_wall_l", width=5.0, height=4.5),
    "GH": OfficialFeatureTemplate("ruined_wall_l", width=4.0, height=3.6),
}


def extract_official_feature_labels(
    page: Any,
    transform: BoardTransform,
    terrain_areas: Sequence[Any],
    *,
    raster_features: Sequence[Any] = (),
    source_page: int,
    element_factory: Callable[..., Any],
) -> list[Any]:
    elements: list[Any] = []
    code_ordinals: dict[OfficialFeatureCode, int] = {}
    used_anchor_ids: set[str] = set()
    for label in _official_feature_label_candidates(page):
        code = label.code
        bbox = label.bbox
        center = image_to_board_point(
            ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0),
            transform,
        )
        terrain_area = _terrain_area_for_point(center, terrain_areas)
        if terrain_area is None:
            continue
        template = OFFICIAL_FEATURE_TEMPLATES[code]
        anchor_feature = _nearest_raster_dense_feature(
            center,
            terrain_area,
            raster_features,
            used_anchor_ids=used_anchor_ids,
        )
        anchor = _feature_anchor_center(anchor_feature) if anchor_feature is not None else center
        footprint = _official_feature_template_footprint(
            anchor,
            terrain_area,
            width=template.width,
            height=template.height,
        )
        if footprint is None:
            continue
        if anchor_feature is not None:
            used_anchor_ids.add(anchor_feature.id)
        code_ordinals[code] = code_ordinals.get(code, 0) + 1
        ordinal = code_ordinals[code]
        elements.append(
            element_factory(
                id=f"page-{source_page}-official-feature-{code.lower()}-{ordinal}",
                label=f"{code} Terrain Feature",
                kind="terrain_feature",
                feature_type="dense",
                feature_profile=template.profile,
                feature_wall_sides=_official_feature_wall_sides(
                    template.profile,
                    anchor,
                    terrain_area,
                ),
                official_feature_code=code,
                terrain_area_id=terrain_area.id,
                footprint=footprint,
                source_page=source_page,
                source_bbox=bbox,
                source_drawing_index=None,
                confidence=0.95,
                warnings=[
                    f"official-feature-code:{code}",
                    f"official-feature-template:{template.profile}",
                    "official-feature-anchor:"
                    + ("raster-dense" if anchor_feature is not None else "label"),
                ],
            )
        )
    return elements


def official_feature_code_from_text(text: str) -> OfficialFeatureCode | None:
    normalized = "".join(text.upper().split())
    for code in OFFICIAL_FEATURE_CODES:
        if normalized == code:
            return code
    return None


def _official_feature_label_candidates(page: Any) -> list[OfficialFeatureLabel]:
    labels: list[OfficialFeatureLabel] = []
    for word in page.get_text("words"):
        if len(word) < 5:
            continue
        code = official_feature_code_from_text(str(word[4]))
        if code is None:
            continue
        labels.append(
            OfficialFeatureLabel(
                code=code,
                bbox=cast(BBox, tuple(float(value) for value in word[:4])),
            )
        )
    return labels


def _terrain_area_for_point(
    point: Point,
    terrain_areas: Sequence[Any],
) -> Any | None:
    shapely_point = ShapelyPoint(point)
    containing = [area for area in terrain_areas if area.polygon().covers(shapely_point)]
    if containing:
        return min(containing, key=lambda area: area.polygon().area)
    if not terrain_areas:
        return None
    nearest = min(terrain_areas, key=lambda area: area.polygon().distance(shapely_point))
    if nearest.polygon().distance(shapely_point) <= 0.35:
        return nearest
    return None


def _nearest_raster_dense_feature(
    point: Point,
    terrain_area: Any,
    raster_features: Sequence[Any],
    *,
    used_anchor_ids: set[str],
) -> Any | None:
    shapely_point = ShapelyPoint(point)
    candidates = [
        feature
        for feature in raster_features
        if feature.kind == "terrain_feature"
        and feature.feature_type == "dense"
        and feature.terrain_area_id == terrain_area.id
        and feature.id not in used_anchor_ids
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda feature: feature.polygon().centroid.distance(shapely_point))


def _feature_anchor_center(feature: Any) -> Point:
    centroid = feature.polygon().centroid
    return (float(centroid.x), float(centroid.y))


def _official_feature_template_footprint(
    center: Point,
    terrain_area: Any,
    *,
    width: float,
    height: float,
) -> list[Point] | None:
    area_polygon = terrain_area.polygon()
    frame = _oriented_frame(area_polygon)
    local_area_points = [_to_local(point, frame) for point in area_polygon.exterior.coords[:-1]]
    min_x = min(point[0] for point in local_area_points)
    max_x = max(point[0] for point in local_area_points)
    min_y = min(point[1] for point in local_area_points)
    max_y = max(point[1] for point in local_area_points)
    width = min(width, max(max_x - min_x, 0.1))
    height = min(height, max(max_y - min_y, 0.1))
    local_center = _to_local(center, frame)
    x0 = _clamp(local_center[0] - width / 2.0, min_x, max_x - width)
    y0 = _clamp(local_center[1] - height / 2.0, min_y, max_y - height)
    candidate = _local_polygon_to_world(
        [
            (x0, y0),
            (x0 + width, y0),
            (x0 + width, y0 + height),
            (x0, y0 + height),
        ],
        frame,
    )
    clipped = _largest_polygon(candidate.intersection(area_polygon))
    if clipped.is_empty or clipped.area <= 0.05:
        return None
    return _polygon_points(clipped)


def _official_feature_wall_sides(
    profile: OfficialFeatureProfile,
    center: Point,
    terrain_area: Any,
) -> list[WallSide] | None:
    if profile not in {"ruined_wall_l", "ruined_wall_u", "ruined_wall_perimeter"}:
        return None
    area_polygon = terrain_area.polygon()
    frame = _oriented_frame(area_polygon)
    local_area_points = [_to_local(point, frame) for point in area_polygon.exterior.coords[:-1]]
    min_x = min(point[0] for point in local_area_points)
    max_x = max(point[0] for point in local_area_points)
    min_y = min(point[1] for point in local_area_points)
    max_y = max(point[1] for point in local_area_points)
    local_center = _to_local(center, frame)
    rx = (local_center[0] - min_x) / max(max_x - min_x, 1e-9)
    ry = (local_center[1] - min_y) / max(max_y - min_y, 1e-9)
    horizontal: WallSide = "left" if rx < 0.5 else "right"
    vertical: WallSide = "bottom" if ry < 0.5 else "top"
    if profile == "ruined_wall_l":
        return [horizontal, vertical]
    if profile == "ruined_wall_u":
        open_side = _nearest_side(rx, ry)
        all_sides: tuple[WallSide, ...] = ("left", "right", "top", "bottom")
        return [side for side in all_sides if side != open_side]
    return ["left", "right", "top", "bottom"]


def _nearest_side(rx: float, ry: float) -> WallSide:
    distances: dict[WallSide, float] = {
        "left": rx,
        "right": 1.0 - rx,
        "bottom": ry,
        "top": 1.0 - ry,
    }
    return min(distances, key=lambda side: distances[side])


def _oriented_frame(polygon: Polygon) -> OrientedFrame:
    rectangle = polygon.minimum_rotated_rectangle
    if not isinstance(rectangle, Polygon):
        return OrientedFrame(x_axis=(1.0, 0.0), y_axis=(0.0, 1.0))
    coords = list(rectangle.exterior.coords)[:-1]
    if len(coords) < 2:
        return OrientedFrame(x_axis=(1.0, 0.0), y_axis=(0.0, 1.0))
    edges: list[tuple[float, float, float]] = []
    for index, start in enumerate(coords):
        end = coords[(index + 1) % len(coords)]
        dx = float(end[0] - start[0])
        dy = float(end[1] - start[1])
        length = (dx * dx + dy * dy) ** 0.5
        edges.append((length, dx, dy))
    horizontal_edges = [edge for edge in edges if abs(edge[2]) <= max(edge[0] * 0.02, 1e-9)]
    if horizontal_edges:
        length, dx, dy = max(horizontal_edges, key=lambda edge: edge[0])
    else:
        max_length = max(edge[0] for edge in edges)
        longest_edges = [
            edge for edge in edges if abs(edge[0] - max_length) <= max(max_length * 0.001, 1e-9)
        ]
        length, dx, dy = max(longest_edges, key=lambda edge: abs(edge[1]))
    if length <= 1e-9:
        return OrientedFrame(x_axis=(1.0, 0.0), y_axis=(0.0, 1.0))
    if (abs(dx) >= abs(dy) and dx < 0) or (abs(dx) < abs(dy) and dy < 0):
        dx = -dx
        dy = -dy
    x_axis = (dx / length, dy / length)
    y_axis = (-x_axis[1], x_axis[0])
    return OrientedFrame(x_axis=x_axis, y_axis=y_axis)


def _to_local(point: Point, frame: OrientedFrame) -> Point:
    return (
        point[0] * frame.x_axis[0] + point[1] * frame.x_axis[1],
        point[0] * frame.y_axis[0] + point[1] * frame.y_axis[1],
    )


def _to_world(point: Point, frame: OrientedFrame) -> Point:
    return (
        point[0] * frame.x_axis[0] + point[1] * frame.y_axis[0],
        point[0] * frame.x_axis[1] + point[1] * frame.y_axis[1],
    )


def _local_polygon_to_world(points: Sequence[Point], frame: OrientedFrame) -> Polygon:
    return Polygon([_to_world(point, frame) for point in points])


def _clamp(value: float, minimum: float, maximum: float) -> float:
    if minimum > maximum:
        return minimum
    return min(max(value, minimum), maximum)


def _polygon_points(polygon: Polygon) -> list[Point]:
    return [(float(x), float(y)) for x, y in list(polygon.exterior.coords)[:-1]]


def _largest_polygon(geometry: object) -> Polygon:
    if isinstance(geometry, Polygon):
        return geometry
    if isinstance(geometry, MultiPolygon) and geometry.geoms:
        return max(geometry.geoms, key=lambda polygon: polygon.area)
    return Polygon()
