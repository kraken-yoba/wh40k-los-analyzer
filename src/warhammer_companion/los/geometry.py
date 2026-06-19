from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import atan2, ceil, cos, sin

from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    Point,
    Polygon,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points, unary_union

from warhammer_companion.domain.deployment_geometry import smooth_deployment_footprint
from warhammer_companion.domain.models import MapPacket, TerrainArea

BOARD_BOUNDARY_EDGE_TOLERANCE = 0.25
OFFSET_SAMPLE_DISTANCE_TOLERANCE_INCHES = 0.15
TERRAIN_CONTACT_TOLERANCE_INCHES = 0.15


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
    polygon: BaseGeometry


@dataclass(frozen=True)
class _LosBlockers:
    opaque: list[Polygon]
    obscuring: list[BaseGeometry]


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
    blockers = _los_blockers_for_base(packet, base)
    rays: list[VisibilityRay] = []

    x = 0.0
    while x <= packet.board.width:
        rays.append(_ray_to(packet, center, (x, 0.0), blockers, ignored_area=base))
        rays.append(_ray_to(packet, center, (x, packet.board.height), blockers, ignored_area=base))
        x += target_spacing

    y = target_spacing
    while y < packet.board.height:
        rays.append(_ray_to(packet, center, (0.0, y), blockers, ignored_area=base))
        rays.append(_ray_to(packet, center, (packet.board.width, y), blockers, ignored_area=base))
        y += target_spacing

    return rays


def binary_visibility_overlay_from_base(
    packet: MapPacket,
    center: tuple[float, float],
    base_diameter: float,
    grid_step: float = 1.0,
) -> list[CoverageCell]:
    base = circular_base(center, base_diameter)
    blockers = _los_blockers_for_base(packet, base)
    cells: list[CoverageCell] = []

    y = grid_step / 2.0
    while y < packet.board.height:
        x = grid_step / 2.0
        while x < packet.board.width:
            target = (x, y)
            visible = not _is_los_blocked(center, target, blockers, ignored_area=base)
            cells.append(CoverageCell(x=x, y=y, visible=visible))
            x += grid_step
        y += grid_step

    return cells


def visibility_polygon_from_base(
    packet: MapPacket,
    center: tuple[float, float],
    base_diameter: float,
) -> BaseGeometry:
    base = circular_base(center, base_diameter)
    return visibility_polygon_from_point(
        packet, center, blockers=_los_blockers_for_base(packet, base)
    )


def heatmap_visibility_polygons_from_deployment_zone(
    packet: MapPacket,
    deployment_zone_id: str,
    sample_step: float = 2.0,
) -> list[VisibilityPolygon]:
    zone = _deployment_zone_polygon(packet, deployment_zone_id)
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


def heatmap_exclusion_zone(
    packet: MapPacket,
    deployment_zone_id: str,
    *,
    source: str,
    offset_inches: float = 0.0,
) -> BaseGeometry:
    zone = _deployment_zone_polygon(packet, deployment_zone_id)
    board = _board_polygon(packet)
    if source == "interior" or offset_inches <= 0:
        return zone.intersection(board)
    return zone.buffer(offset_inches).intersection(board).buffer(0)


def safe_heatmap_regions(
    packet: MapPacket,
    visibility_polygons: list[VisibilityPolygon],
    *,
    excluded_area: BaseGeometry | None = None,
) -> BaseGeometry:
    board = _board_polygon(packet)
    visible_parts = [
        item.polygon.intersection(board)
        for item in visibility_polygons
        if not item.polygon.is_empty
    ]
    visible_region = unary_union(visible_parts) if visible_parts else Polygon()
    safe_region = board.difference(visible_region)
    if excluded_area is not None and not excluded_area.is_empty:
        safe_region = safe_region.difference(excluded_area)
    return safe_region.buffer(0)


def deployment_edge_sample_points(
    packet: MapPacket,
    deployment_zone_id: str,
    sample_step: float = 2.0,
    offset_inches: float = 0.0,
) -> list[tuple[float, float]]:
    if sample_step <= 0:
        raise ValueError("sample_step must be positive")
    zone = _deployment_zone_polygon(packet, deployment_zone_id)
    board = _board_polygon(packet)
    if offset_inches > 0:
        offset_samples = _offset_frontier_sample_points(
            zone,
            board,
            sample_step=sample_step,
            offset_inches=offset_inches,
        )
        if offset_samples:
            return offset_samples
    samples: list[tuple[float, float]] = []
    for start, end in _front_edge_segments(zone, board):
        normal = _front_edge_normal(start, end, zone, board)
        for sample in _sample_segment(start, end, sample_step):
            shifted = (
                sample[0] + normal[0] * offset_inches,
                sample[1] + normal[1] * offset_inches,
            )
            shifted_point = Point(shifted)
            if board.covers(shifted_point) and (
                offset_inches <= 0 or not zone.covers(shifted_point)
            ):
                samples.append((round(shifted[0], 6), round(shifted[1], 6)))
    if samples:
        return samples
    centroid = zone.centroid
    return [(round(centroid.x, 6), round(centroid.y, 6))]


def visibility_polygon_from_point(
    packet: MapPacket,
    origin: tuple[float, float],
    blockers: _LosBlockers | list[Polygon] | None = None,
) -> BaseGeometry:
    board = _board_polygon(packet)
    active_blockers = (
        _los_blockers_for_point(packet, origin)
        if blockers is None
        else _coerce_los_blockers(blockers)
    )
    board_segments = _polygon_segments(board)
    opaque_segments = [
        segment for blocker in active_blockers.opaque for segment in _polygon_segments(blocker)
    ]
    vertices = _polygon_vertices(board) + [
        vertex
        for blocker in active_blockers.opaque + active_blockers.obscuring
        for vertex in _geometry_vertices(blocker)
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
        for hit in [
            _nearest_visibility_hit(
                origin,
                angle,
                ray_length,
                board_segments,
                opaque_segments,
                active_blockers.obscuring,
            )
        ]
        if hit is not None
    ]
    if len(points) < 3:
        return Polygon()

    polygon: BaseGeometry = Polygon(points)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    return polygon.intersection(board)


def heatmap_from_deployment_zone(
    packet: MapPacket,
    deployment_zone_id: str,
    grid_step: float = 1.0,
    sample_step: float = 2.0,
) -> list[HeatmapCell]:
    zone = _deployment_zone_polygon(packet, deployment_zone_id)
    sample_points = _points_in_polygon(zone, sample_step)
    sample_blockers = [
        (sample, _los_blockers_for_point(packet, sample)) for sample in sample_points
    ]
    cells: list[HeatmapCell] = []

    y = grid_step / 2.0
    while y < packet.board.height:
        x = grid_step / 2.0
        while x < packet.board.width:
            target = (x, y)
            visible_count = 0
            for sample, blockers in sample_blockers:
                if not _is_los_blocked(sample, target, blockers):
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
    blockers: _LosBlockers,
    ignored_area: Polygon | None = None,
) -> VisibilityRay:
    board = _board_polygon(packet)
    target_point = Point(target)
    if not board.covers(target_point):
        return VisibilityRay(target=target, visible=False)
    visible = not _is_los_blocked(origin, target, blockers, ignored_area=ignored_area)
    return VisibilityRay(target=target, visible=visible)


def _los_blockers_for_point(packet: MapPacket, origin: tuple[float, float]) -> _LosBlockers:
    origin_point = Point(origin)
    ignored_group_ids = _terrain_group_ids_covering_point(packet, origin_point)
    return _LosBlockers(
        opaque=[feature.polygon() for feature in packet.dense_features if feature.blocks_los],
        obscuring=_obscuring_terrain_geometries(packet, ignored_group_ids=ignored_group_ids),
    )


def _los_blockers_for_base(packet: MapPacket, base: Polygon) -> _LosBlockers:
    touched_group_ids = _terrain_group_ids_touched_by_base(packet, base)
    return _LosBlockers(
        opaque=[feature.polygon() for feature in packet.dense_features if feature.blocks_los],
        obscuring=_obscuring_terrain_geometries(packet, ignored_group_ids=touched_group_ids),
    )


def _coerce_los_blockers(blockers: _LosBlockers | list[Polygon]) -> _LosBlockers:
    if isinstance(blockers, _LosBlockers):
        return blockers
    return _LosBlockers(opaque=blockers, obscuring=[])


def _terrain_group_ids_covering_point(packet: MapPacket, point: Point) -> set[str]:
    covered: set[str] = set()
    for area in packet.terrain_areas:
        polygon = area.polygon()
        if polygon.covers(point):
            covered.add(_terrain_group_key(area))
    return covered


def _terrain_group_ids_touched_by_base(packet: MapPacket, base: Polygon) -> set[str]:
    touched: set[str] = set()
    for area in packet.terrain_areas:
        polygon = area.polygon()
        if base.intersects(polygon) or base.distance(polygon) <= 1e-7:
            touched.add(_terrain_group_key(area))
    return touched


def _obscuring_terrain_geometries(
    packet: MapPacket,
    *,
    ignored_group_ids: set[str],
) -> list[BaseGeometry]:
    grouped_polygons: dict[str, list[Polygon]] = {}
    for area in packet.terrain_areas:
        if not area.blocks_los:
            continue
        group_key = _terrain_group_key(area)
        if group_key in ignored_group_ids:
            continue
        grouped_polygons.setdefault(group_key, []).append(area.polygon())
    geometries: list[BaseGeometry] = []
    for polygons in grouped_polygons.values():
        geometry = unary_union(polygons)
        if not geometry.is_empty:
            geometries.append(geometry)
    return _merge_hairline_contact_geometries(geometries)


def _terrain_group_key(area: TerrainArea) -> str:
    return area.terrain_group_id or area.id


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


def _is_los_blocked(
    origin: tuple[float, float],
    target: tuple[float, float],
    blockers: _LosBlockers,
    ignored_area: Polygon | None = None,
) -> bool:
    line = LineString([origin, target])
    if line.length == 0:
        return False

    opaque_blockers = _blocker_union(blockers.opaque)
    if ignored_area is not None:
        opaque_blockers = opaque_blockers.difference(ignored_area)
    if not opaque_blockers.is_empty and opaque_blockers.intersects(line):
        return True

    origin_point = Point(origin)
    target_point = Point(target)
    for terrain_area in blockers.obscuring:
        if terrain_area.covers(origin_point) or terrain_area.covers(target_point):
            continue
        intersection = line.intersection(terrain_area)
        if not intersection.is_empty and intersection.length > 1e-9:
            return True
    return False


def _merge_hairline_contact_geometries(geometries: list[BaseGeometry]) -> list[BaseGeometry]:
    if len(geometries) < 2:
        return geometries

    half_tolerance = TERRAIN_CONTACT_TOLERANCE_INCHES / 2.0
    bridged_geometries: list[BaseGeometry] = list(geometries)
    for left, right in combinations(geometries, 2):
        if left.distance(right) > TERRAIN_CONTACT_TOLERANCE_INCHES:
            continue
        left_point, right_point = nearest_points(left, right)
        if left_point.distance(right_point) <= 1e-9:
            connector = left_point.buffer(half_tolerance, quad_segs=2)
        else:
            connector = LineString([left_point, right_point]).buffer(
                half_tolerance,
                cap_style="round",
                join_style="mitre",
            )
        if not connector.is_empty and connector.area > 1e-6:
            bridged_geometries.append(connector)

    merged = unary_union(bridged_geometries)
    if merged.is_empty:
        return []
    if hasattr(merged, "geoms"):
        return [geometry for geometry in merged.geoms if not geometry.is_empty]
    return [merged]


def _board_polygon(packet: MapPacket) -> Polygon:
    return Polygon(
        [
            (0, 0),
            (packet.board.width, 0),
            (packet.board.width, packet.board.height),
            (0, packet.board.height),
        ]
    )


def _deployment_zone_polygon(packet: MapPacket, deployment_zone_id: str) -> Polygon:
    zone = packet.deployment_zone(deployment_zone_id)
    return Polygon(smooth_deployment_footprint(zone.footprint))


def _polygon_vertices(polygon: Polygon) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in list(polygon.exterior.coords)[:-1]]


def _geometry_vertices(geometry: BaseGeometry) -> list[tuple[float, float]]:
    if isinstance(geometry, Polygon):
        return _polygon_vertices(geometry)
    if hasattr(geometry, "geoms"):
        vertices: list[tuple[float, float]] = []
        for part in geometry.geoms:
            vertices.extend(_geometry_vertices(part))
        return vertices
    return []


def _polygon_segments(polygon: Polygon) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    vertices = _polygon_vertices(polygon)
    return list(zip(vertices, vertices[1:] + vertices[:1], strict=True))


def _front_edge_segments(
    zone: Polygon,
    board: Polygon,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for start, end in _polygon_segments(zone):
        segment = LineString([start, end])
        if segment.length <= 0:
            continue
        if _is_board_boundary_segment(segment, board):
            continue
        segments.append((start, end))
    return segments


def _offset_frontier_sample_points(
    zone: Polygon,
    board: Polygon,
    *,
    sample_step: float,
    offset_inches: float,
) -> list[tuple[float, float]]:
    expanded_zone = zone.buffer(offset_inches).intersection(board).buffer(0)
    if expanded_zone.is_empty:
        return []

    samples: list[tuple[float, float]] = []
    seen: set[tuple[float, float]] = set()
    for line in _intersection_lines(expanded_zone.boundary):
        if line.length <= 0:
            continue
        if _is_board_boundary_segment(line, board):
            continue
        for sample in _sample_line(line, sample_step):
            point = Point(sample)
            if not board.covers(point) or zone.covers(point):
                continue
            if abs(zone.distance(point) - offset_inches) > OFFSET_SAMPLE_DISTANCE_TOLERANCE_INCHES:
                continue
            rounded = (round(sample[0], 6), round(sample[1], 6))
            if rounded in seen:
                continue
            seen.add(rounded)
            samples.append(rounded)
    return samples


def _is_board_boundary_segment(line: LineString, board: Polygon) -> bool:
    if line.intersection(board.boundary).length >= line.length - 1e-7:
        return True
    min_x, min_y, max_x, max_y = line.bounds
    board_min_x, board_min_y, board_max_x, board_max_y = board.bounds
    tolerance = BOARD_BOUNDARY_EDGE_TOLERANCE
    return (
        max_x <= board_min_x + tolerance
        or min_x >= board_max_x - tolerance
        or max_y <= board_min_y + tolerance
        or min_y >= board_max_y - tolerance
    )


def _sample_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    spacing: float,
) -> list[tuple[float, float]]:
    line = LineString([start, end])
    return _sample_line(line, spacing)


def _sample_line(line: LineString, spacing: float) -> list[tuple[float, float]]:
    count = max(1, ceil(line.length / spacing))
    return [
        _line_interpolated_point(line, line.length * ((index + 0.5) / count))
        for index in range(count)
    ]


def _line_interpolated_point(line: LineString, distance: float) -> tuple[float, float]:
    point = line.interpolate(distance)
    return (point.x, point.y)


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
        key=lambda candidate: candidate[0] * toward_center[0] + candidate[1] * toward_center[1],
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


def _nearest_visibility_hit(
    origin: tuple[float, float],
    angle: float,
    ray_length: float,
    board_segments: list[tuple[tuple[float, float], tuple[float, float]]],
    opaque_segments: list[tuple[tuple[float, float], tuple[float, float]]],
    obscuring_polygons: list[BaseGeometry],
) -> tuple[float, float] | None:
    candidates = [
        _nearest_ray_hit(origin, angle, ray_length, board_segments),
        _nearest_ray_hit(origin, angle, ray_length, opaque_segments),
        _nearest_obscuring_exit_hit(origin, angle, ray_length, obscuring_polygons),
    ]
    hits = [hit for hit in candidates if hit is not None]
    if not hits:
        return None
    return min(hits, key=lambda hit: (hit[0] - origin[0]) ** 2 + (hit[1] - origin[1]) ** 2)


def _nearest_obscuring_exit_hit(
    origin: tuple[float, float],
    angle: float,
    ray_length: float,
    obscuring_polygons: list[BaseGeometry],
) -> tuple[float, float] | None:
    ox, oy = origin
    dx = cos(angle)
    dy = sin(angle)
    ray = LineString([(ox, oy), (ox + dx * ray_length, oy + dy * ray_length)])
    closest_entry = float("inf")
    closest_hit: tuple[float, float] | None = None

    for polygon in obscuring_polygons:
        intersection = ray.intersection(polygon)
        if intersection.is_empty or intersection.length <= 1e-9:
            continue
        interval = _first_ray_intersection_interval(
            intersection,
            origin,
            (dx, dy),
            ray_length,
        )
        if interval is None:
            continue
        entry_distance, exit_distance = interval
        if entry_distance < closest_entry:
            closest_entry = entry_distance
            closest_hit = (ox + dx * exit_distance, oy + dy * exit_distance)

    return closest_hit


def _first_ray_intersection_interval(
    intersection: BaseGeometry,
    origin: tuple[float, float],
    direction: tuple[float, float],
    ray_length: float,
) -> tuple[float, float] | None:
    intervals: list[tuple[float, float]] = []
    for line in _intersection_lines(intersection):
        distances = [
            _project_ray_distance(point, origin, direction) for point in _intersection_points(line)
        ]
        distances = [distance for distance in distances if 1e-9 < distance <= ray_length + 1e-9]
        if distances:
            intervals.append((min(distances), max(distances)))
    if not intervals:
        return None
    return min(intervals, key=lambda interval: interval[0])


def _project_ray_distance(
    point: tuple[float, float],
    origin: tuple[float, float],
    direction: tuple[float, float],
) -> float:
    return (point[0] - origin[0]) * direction[0] + (point[1] - origin[1]) * direction[1]


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
    if isinstance(geometry, MultiLineString):
        line_points: list[tuple[float, float]] = []
        for line in geometry.geoms:
            line_points.extend(_intersection_points(line))
        return line_points
    if isinstance(geometry, GeometryCollection):
        points: list[tuple[float, float]] = []
        for part in geometry.geoms:
            points.extend(_intersection_points(part))
        return points
    return []


def _intersection_lines(geometry: BaseGeometry) -> list[LineString]:
    if geometry.is_empty:
        return []
    if isinstance(geometry, LineString):
        return [geometry]
    if isinstance(geometry, MultiLineString):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        lines: list[LineString] = []
        for part in geometry.geoms:
            lines.extend(_intersection_lines(part))
        return lines
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
