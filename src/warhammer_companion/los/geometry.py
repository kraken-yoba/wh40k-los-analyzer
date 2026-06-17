from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, sin

from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from warhammer_companion.domain.models import MapPacket


@dataclass(frozen=True)
class VisibilityRay:
    target: tuple[float, float]
    visible: bool


@dataclass(frozen=True)
class HeatmapCell:
    x: float
    y: float
    visibility: float


@dataclass(frozen=True)
class CoverageCell:
    x: float
    y: float
    visible: bool


@dataclass(frozen=True)
class VisibilityPolygon:
    origin: tuple[float, float]
    polygon: Polygon


def circular_base(center: tuple[float, float], diameter: float, resolution: int = 48) -> Polygon:
    return Point(center).buffer(diameter / 2.0, quad_segs=resolution)


def is_line_blocked(
    origin: tuple[float, float],
    target: tuple[float, float],
    blockers: list[Polygon],
    ignored_area: Polygon | None = None,
) -> bool:
    return _is_segment_blocked(
        origin,
        target,
        _blocker_union(blockers),
        ignored_area=ignored_area,
    )


def visibility_rays_from_base(
    packet: MapPacket,
    center: tuple[float, float],
    base_diameter: float,
    target_spacing: float = 6.0,
) -> list[VisibilityRay]:
    base = circular_base(center, base_diameter)
    blockers = _blocker_union(packet.blockers()).difference(base)
    rays: list[VisibilityRay] = []

    x = 0.0
    while x <= packet.board.width:
        rays.append(_ray_to(packet, center, (x, 0.0), blockers, base))
        rays.append(_ray_to(packet, center, (x, packet.board.height), blockers, base))
        x += target_spacing

    y = target_spacing
    while y < packet.board.height:
        rays.append(_ray_to(packet, center, (0.0, y), blockers, base))
        rays.append(_ray_to(packet, center, (packet.board.width, y), blockers, base))
        y += target_spacing

    return rays


def binary_visibility_overlay_from_base(
    packet: MapPacket,
    center: tuple[float, float],
    base_diameter: float,
    grid_step: float = 1.0,
) -> list[CoverageCell]:
    base = circular_base(center, base_diameter)
    blockers = _blocker_union(packet.blockers()).difference(base)
    cells: list[CoverageCell] = []

    y = grid_step / 2.0
    while y < packet.board.height:
        x = grid_step / 2.0
        while x < packet.board.width:
            target = (x, y)
            visible = not _is_segment_blocked(center, target, blockers)
            cells.append(CoverageCell(x=x, y=y, visible=visible))
            x += grid_step
        y += grid_step

    return cells


def heatmap_visibility_polygons_from_deployment_zone(
    packet: MapPacket,
    deployment_zone_id: str,
    sample_step: float = 2.0,
) -> list[VisibilityPolygon]:
    zone = packet.deployment_zone(deployment_zone_id).polygon()
    sample_points = _points_in_polygon(zone, sample_step)
    return [
        VisibilityPolygon(origin=sample, polygon=visibility_polygon_from_point(packet, sample))
        for sample in sample_points
    ]


def visibility_polygon_from_point(packet: MapPacket, origin: tuple[float, float]) -> Polygon:
    board = _board_polygon(packet)
    blockers = packet.blockers()
    segments = _polygon_segments(board) + [
        segment for blocker in blockers for segment in _polygon_segments(blocker)
    ]
    vertices = _polygon_vertices(board) + [
        vertex for blocker in blockers for vertex in _polygon_vertices(blocker)
    ]
    ray_length = max(packet.board.width, packet.board.height) * 3.0
    angles = sorted(
        angle + offset
        for vertex in vertices
        for angle in [atan2(vertex[1] - origin[1], vertex[0] - origin[0])]
        for offset in (-0.0001, 0.0, 0.0001)
    )

    points = [
        hit
        for angle in angles
        for hit in [_nearest_ray_hit(origin, angle, ray_length, segments)]
        if hit is not None
    ]
    if len(points) < 3:
        return Polygon()

    polygon = Polygon(points)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    clipped = polygon.intersection(board)
    if isinstance(clipped, Polygon):
        return clipped
    if isinstance(clipped, MultiPolygon):
        return max(clipped.geoms, key=lambda item: item.area)
    return Polygon()


def heatmap_from_deployment_zone(
    packet: MapPacket,
    deployment_zone_id: str,
    grid_step: float = 1.0,
    sample_step: float = 2.0,
) -> list[HeatmapCell]:
    zone = packet.deployment_zone(deployment_zone_id).polygon()
    blockers = _blocker_union(packet.blockers())
    sample_points = _points_in_polygon(zone, sample_step)
    cells: list[HeatmapCell] = []

    y = grid_step / 2.0
    while y < packet.board.height:
        x = grid_step / 2.0
        while x < packet.board.width:
            target = (x, y)
            visible_count = 0
            for sample in sample_points:
                if not _is_segment_blocked(sample, target, blockers):
                    visible_count += 1
            visibility = visible_count / len(sample_points) if sample_points else 0.0
            cells.append(HeatmapCell(x=x, y=y, visibility=visibility))
            x += grid_step
        y += grid_step

    return cells


def _ray_to(
    packet: MapPacket,
    origin: tuple[float, float],
    target: tuple[float, float],
    blockers: BaseGeometry,
    base: Polygon,
) -> VisibilityRay:
    board = _board_polygon(packet)
    target_point = Point(target)
    if not board.covers(target_point):
        return VisibilityRay(target=target, visible=False)
    visible = not _is_segment_blocked(origin, target, blockers)
    return VisibilityRay(target=target, visible=visible)


def _blocker_union(blockers: list[Polygon]) -> BaseGeometry:
    return unary_union(blockers) if blockers else Polygon()


def _is_segment_blocked(
    origin: tuple[float, float],
    target: tuple[float, float],
    blocker_union: BaseGeometry,
    ignored_area: Polygon | None = None,
) -> bool:
    line = LineString([origin, target])
    if line.length == 0:
        return False

    effective_blockers = blocker_union
    if ignored_area is not None:
        effective_blockers = effective_blockers.difference(ignored_area)

    if effective_blockers.is_empty:
        return False

    return effective_blockers.intersects(line)


def _board_polygon(packet: MapPacket) -> Polygon:
    return Polygon(
        [
            (0, 0),
            (packet.board.width, 0),
            (packet.board.width, packet.board.height),
            (0, packet.board.height),
        ]
    )


def _polygon_vertices(polygon: Polygon) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in list(polygon.exterior.coords)[:-1]]


def _polygon_segments(polygon: Polygon) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    vertices = _polygon_vertices(polygon)
    return list(zip(vertices, vertices[1:] + vertices[:1], strict=True))


def _nearest_ray_hit(
    origin: tuple[float, float],
    angle: float,
    ray_length: float,
    segments: list[tuple[tuple[float, float], tuple[float, float]]],
) -> tuple[float, float] | None:
    ray_end = (origin[0] + cos(angle) * ray_length, origin[1] + sin(angle) * ray_length)
    ray = LineString([origin, ray_end])
    closest: tuple[float, float] | None = None
    closest_distance = float("inf")

    for segment_start, segment_end in segments:
        intersection = ray.intersection(LineString([segment_start, segment_end]))
        for point in _intersection_points(intersection):
            distance = (point[0] - origin[0]) ** 2 + (point[1] - origin[1]) ** 2
            if 1e-9 < distance < closest_distance:
                closest = point
                closest_distance = distance

    return closest


def _intersection_points(geometry: BaseGeometry) -> list[tuple[float, float]]:
    if geometry.is_empty:
        return []
    if isinstance(geometry, Point):
        return [(geometry.x, geometry.y)]
    if isinstance(geometry, MultiPoint):
        return [(point.x, point.y) for point in geometry.geoms]
    if isinstance(geometry, LineString):
        return [(float(x), float(y)) for x, y in geometry.coords]
    if isinstance(geometry, GeometryCollection):
        points: list[tuple[float, float]] = []
        for part in geometry.geoms:
            points.extend(_intersection_points(part))
        return points
    return []


def _points_in_polygon(polygon: Polygon, spacing: float) -> list[tuple[float, float]]:
    min_x, min_y, max_x, max_y = polygon.bounds
    points: list[tuple[float, float]] = []
    y = min_y + spacing / 2.0
    while y < max_y:
        x = min_x + spacing / 2.0
        while x < max_x:
            point = Point(x, y)
            if polygon.covers(point):
                points.append((x, y))
            x += spacing
        y += spacing
    if not points:
        centroid = polygon.centroid
        points.append((centroid.x, centroid.y))
    return points
