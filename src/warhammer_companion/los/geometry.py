from __future__ import annotations

from dataclasses import dataclass
from math import atan2, ceil, cos, sin

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


def clamp_base_center(
    packet: MapPacket, center: tuple[float, float], base_diameter: float
) -> tuple[float, float]:
    radius = max(base_diameter / 2.0, 0.0)
    min_x = min(radius, packet.board.width / 2.0)
    max_x = max(packet.board.width - radius, min_x)
    min_y = min(radius, packet.board.height / 2.0)
    max_y = max(packet.board.height - radius, min_y)
    return (_clamp(center[0], min_x, max_x), _clamp(center[1], min_y, max_y))


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
    blockers = _blocker_union(_blockers_for_base(packet, base)).difference(base)
    rays: list[VisibilityRay] = []

    x = 0.0
    while x <= packet.board.width:
        rays.append(_ray_to(packet, center, (x, 0.0), blockers))
        rays.append(_ray_to(packet, center, (x, packet.board.height), blockers))
        x += target_spacing

    y = target_spacing
    while y < packet.board.height:
        rays.append(_ray_to(packet, center, (0.0, y), blockers))
        rays.append(_ray_to(packet, center, (packet.board.width, y), blockers))
        y += target_spacing

    return rays


def binary_visibility_overlay_from_base(
    packet: MapPacket,
    center: tuple[float, float],
    base_diameter: float,
    grid_step: float = 1.0,
) -> list[CoverageCell]:
    base = circular_base(center, base_diameter)
    blockers = _blocker_union(_blockers_for_base(packet, base)).difference(base)
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


def visibility_polygon_from_base(
    packet: MapPacket,
    center: tuple[float, float],
    base_diameter: float,
) -> Polygon:
    base = circular_base(center, base_diameter)
    return visibility_polygon_from_point(packet, center, blockers=_blockers_for_base(packet, base))


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


def heatmap_visibility_polygons_from_deployment_edge(
    packet: MapPacket,
    deployment_zone_id: str,
    sample_step: float = 2.0,
    offset_inches: float = 0.0,
) -> list[VisibilityPolygon]:
    sample_points = deployment_edge_sample_points(
        packet,
        deployment_zone_id,
        sample_step=sample_step,
        offset_inches=offset_inches,
    )
    return [
        VisibilityPolygon(origin=sample, polygon=visibility_polygon_from_point(packet, sample))
        for sample in sample_points
    ]


def deployment_edge_sample_points(
    packet: MapPacket,
    deployment_zone_id: str,
    sample_step: float = 2.0,
    offset_inches: float = 0.0,
) -> list[tuple[float, float]]:
    if sample_step <= 0:
        raise ValueError("sample_step must be positive")
    zone = packet.deployment_zone(deployment_zone_id).polygon()
    board = _board_polygon(packet)
    samples: list[tuple[float, float]] = []
    for start, end in _polygon_segments(zone):
        segment = LineString([start, end])
        if segment.length <= 0:
            continue
        if _board_boundary_overlap_length(segment, board) >= segment.length - 1e-7:
            continue
        normal = _front_edge_normal(start, end, zone, board)
        for sample in _sample_segment(start, end, sample_step):
            shifted = (
                sample[0] + normal[0] * offset_inches,
                sample[1] + normal[1] * offset_inches,
            )
            if board.covers(Point(shifted)):
                samples.append((round(shifted[0], 6), round(shifted[1], 6)))
    if samples:
        return samples
    centroid = zone.centroid
    return [(round(centroid.x, 6), round(centroid.y, 6))]


def visibility_polygon_from_point(
    packet: MapPacket,
    origin: tuple[float, float],
    blockers: list[Polygon] | None = None,
) -> Polygon:
    board = _board_polygon(packet)
    active_blockers = packet.blockers() if blockers is None else blockers
    segments = _polygon_segments(board) + [
        segment for blocker in active_blockers for segment in _polygon_segments(blocker)
    ]
    vertices = _polygon_vertices(board) + [
        vertex for blocker in active_blockers for vertex in _polygon_vertices(blocker)
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
) -> VisibilityRay:
    board = _board_polygon(packet)
    target_point = Point(target)
    if not board.covers(target_point):
        return VisibilityRay(target=target, visible=False)
    visible = not _is_segment_blocked(origin, target, blockers)
    return VisibilityRay(target=target, visible=visible)


def _blockers_for_base(packet: MapPacket, base: Polygon) -> list[Polygon]:
    touched_area_ids = _terrain_area_ids_touched_by_base(packet, base)
    blockers = [
        area.polygon()
        for area in packet.terrain_areas
        if area.blocks_los and area.id not in touched_area_ids
    ]
    blockers.extend(
        feature.polygon()
        for feature in packet.dense_features
        if feature.blocks_los and feature.terrain_area_id not in touched_area_ids
    )
    return blockers


def _terrain_area_ids_touched_by_base(packet: MapPacket, base: Polygon) -> set[str]:
    touched: set[str] = set()
    for area in packet.terrain_areas:
        polygon = area.polygon()
        if base.intersects(polygon) or base.distance(polygon) <= 1e-7:
            touched.add(area.id)
    return touched


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


def _board_boundary_overlap_length(line: LineString, board: Polygon) -> float:
    return float(line.intersection(board.boundary).length)


def _sample_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    spacing: float,
) -> list[tuple[float, float]]:
    line = LineString([start, end])
    count = max(1, ceil(line.length / spacing))
    return [
        (
            start[0] + (end[0] - start[0]) * ((index + 0.5) / count),
            start[1] + (end[1] - start[1]) * ((index + 0.5) / count),
        )
        for index in range(count)
    ]


def _front_edge_normal(
    start: tuple[float, float],
    end: tuple[float, float],
    zone: Polygon,
    board: Polygon,
) -> tuple[float, float]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = (dx**2 + dy**2) ** 0.5
    if length <= 0:
        return (0.0, 0.0)
    midpoint = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    candidates = [(-dy / length, dx / length), (dy / length, -dx / length)]
    for candidate in candidates:
        probe = (
            midpoint[0] + candidate[0] * 0.05,
            midpoint[1] + candidate[1] * 0.05,
        )
        point = Point(probe)
        if board.covers(point) and not zone.covers(point):
            return candidate
    board_center = board.centroid
    toward_center = (board_center.x - midpoint[0], board_center.y - midpoint[1])
    return max(
        candidates,
        key=lambda candidate: candidate[0] * toward_center[0]
        + candidate[1] * toward_center[1],
    )


def _nearest_ray_hit(
    origin: tuple[float, float],
    angle: float,
    ray_length: float,
    segments: list[tuple[tuple[float, float], tuple[float, float]]],
) -> tuple[float, float] | None:
    dx = cos(angle)
    dy = sin(angle)
    closest: tuple[float, float] | None = None
    closest_distance = float("inf")

    for segment_start, segment_end in segments:
        hit = _ray_segment_hit(origin, (dx, dy), ray_length, segment_start, segment_end)
        if hit is None:
            continue
        distance = (hit[0] - origin[0]) ** 2 + (hit[1] - origin[1]) ** 2
        if 1e-9 < distance < closest_distance:
            closest = hit
            closest_distance = distance

    return closest


def _ray_segment_hit(
    origin: tuple[float, float],
    direction: tuple[float, float],
    ray_length: float,
    segment_start: tuple[float, float],
    segment_end: tuple[float, float],
) -> tuple[float, float] | None:
    ox, oy = origin
    dx, dy = direction
    sx, sy = segment_start
    ex, ey = segment_end
    vx = ex - sx
    vy = ey - sy
    denominator = _cross(dx, dy, vx, vy)
    if abs(denominator) <= 1e-12:
        return None

    rel_x = sx - ox
    rel_y = sy - oy
    ray_distance = _cross(rel_x, rel_y, vx, vy) / denominator
    segment_position = _cross(rel_x, rel_y, dx, dy) / denominator
    if ray_distance <= 1e-9 or ray_distance > ray_length:
        return None
    if segment_position < -1e-9 or segment_position > 1.0 + 1e-9:
        return None
    return (ox + dx * ray_distance, oy + dy * ray_distance)


def _cross(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * by - ay * bx


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


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)
