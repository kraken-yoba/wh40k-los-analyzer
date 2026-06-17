from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString, Point, Polygon
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


def circular_base(center: tuple[float, float], diameter: float, resolution: int = 48) -> Polygon:
    return Point(center).buffer(diameter / 2.0, quad_segs=resolution)


def is_line_blocked(
    origin: tuple[float, float],
    target: tuple[float, float],
    blockers: list[Polygon],
    ignored_area: Polygon | None = None,
) -> bool:
    line = LineString([origin, target])
    if line.length == 0:
        return False

    blocker_union = unary_union(blockers) if blockers else Polygon()
    if ignored_area is not None:
        blocker_union = blocker_union.difference(ignored_area)

    if blocker_union.is_empty:
        return False

    intersection = line.intersection(blocker_union)
    if intersection.is_empty:
        return False

    return intersection.length > 1e-6 or intersection.geom_type in {"Point", "MultiPoint"}


def visibility_rays_from_base(
    packet: MapPacket,
    center: tuple[float, float],
    base_diameter: float,
    target_spacing: float = 6.0,
) -> list[VisibilityRay]:
    base = circular_base(center, base_diameter)
    blockers = packet.blockers()
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


def heatmap_from_deployment_zone(
    packet: MapPacket,
    deployment_zone_id: str,
    grid_step: float = 4.0,
    sample_step: float = 4.0,
) -> list[HeatmapCell]:
    zone = packet.deployment_zone(deployment_zone_id).polygon()
    blockers = packet.blockers()
    sample_points = _points_in_polygon(zone, sample_step)
    cells: list[HeatmapCell] = []

    y = grid_step / 2.0
    while y < packet.board.height:
        x = grid_step / 2.0
        while x < packet.board.width:
            target = (x, y)
            visible_count = 0
            for sample in sample_points:
                if not is_line_blocked(sample, target, blockers):
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
    blockers: list[Polygon],
    base: Polygon,
) -> VisibilityRay:
    board = Polygon(
        [
            (0, 0),
            (packet.board.width, 0),
            (packet.board.width, packet.board.height),
            (0, packet.board.height),
        ]
    )
    target_point = Point(target)
    if not board.covers(target_point):
        return VisibilityRay(target=target, visible=False)
    visible = not is_line_blocked(origin, target, blockers, ignored_area=base)
    return VisibilityRay(target=target, visible=visible)


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
