from __future__ import annotations

import hashlib
from collections.abc import Hashable, MutableMapping
from dataclasses import dataclass
from heapq import heappop, heappush
from math import floor, hypot, isfinite

from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.movement import (
    DEFAULT_MOVEMENT_PROFILE_ID,
    DEFAULT_ROUTING_RESOLUTION_INCHES,
    MAX_ROUTING_GRID_NODES,
    MOVEMENT_ROUTING_ALGORITHM_VERSION,
    MOVEMENT_ROUTING_TOLERANCE_INCHES,
    MovementDiagnosticReason,
    MovementEndpointDiagnostic,
    MovementProfile,
    MovementRoutingMetadata,
    effective_move_distance,
    movement_profile_for_id,
)

_GridKey = tuple[int, int]
_PacketGeometryKey = tuple[
    str,
    float,
    float,
    tuple[tuple[tuple[float, float], ...], ...],
]
_RouteFieldCacheKey = tuple[
    _PacketGeometryKey,
    float,
    tuple[float, float],
    str,
    float,
]
_EnvelopeCacheKey = tuple[
    _PacketGeometryKey,
    tuple[float, float],
    float,
    float,
    str,
    float,
]
_RegionRouteFieldCacheKey = tuple[
    _PacketGeometryKey,
    float,
    str,
    str,
    float,
]
_ROUTE_FIELD_CACHE: dict[_RouteFieldCacheKey, _RouteField] = {}
_REGION_ROUTE_FIELD_CACHE: dict[_RegionRouteFieldCacheKey, _RouteField] = {}
_ENVELOPE_CACHE: dict[_EnvelopeCacheKey, BaseGeometry] = {}
_CACHE_LIMIT = 64


class MovementRoutingBudgetExceeded(ValueError):
    def __init__(self, *, node_count: int, node_limit: int) -> None:
        self.node_count = node_count
        self.node_limit = node_limit
        super().__init__(
            f"routing grid exceeds node budget: {node_count} nodes exceeds {node_limit}"
        )


@dataclass(frozen=True, slots=True)
class _RouteField:
    nodes: dict[_GridKey, tuple[float, float]]
    distances: dict[_GridKey, float]
    previous: dict[_GridKey, _GridKey | None]
    start_key: _GridKey
    metadata: MovementRoutingMetadata


def movement_envelope(
    packet: MapPacket,
    *,
    start_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    movement_profile_id: str = DEFAULT_MOVEMENT_PROFILE_ID,
    routing_resolution: float = DEFAULT_ROUTING_RESOLUTION_INCHES,
) -> BaseGeometry:
    _require_positive("base_diameter", base_diameter)
    _require_positive("move_distance", move_distance)
    _require_positive("routing_resolution", routing_resolution)
    _require_finite_point("start_center", start_center)
    base_radius = base_diameter / 2.0
    cache_key = _envelope_cache_key(
        packet=packet,
        start_center=start_center,
        base_diameter=base_diameter,
        move_distance=move_distance,
        movement_profile_id=movement_profile_id,
        routing_resolution=routing_resolution,
    )
    cached = _ENVELOPE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    board_center_region = base_center_region(packet, base_radius)
    profile = movement_profile_for_id(movement_profile_id)
    effective_distance = effective_move_distance(move_distance, profile.profile_id)
    endpoint_blockers = dense_endpoint_collision_regions(packet, base_radius)

    start_point = Point(start_center)
    if (
        effective_distance <= MOVEMENT_ROUTING_TOLERANCE_INCHES
        or profile.ignores_dense_traversal
        or _traversal_blockers(packet, base_radius, profile).is_empty
    ):
        envelope = start_point.buffer(effective_distance).intersection(board_center_region)
        if not endpoint_blockers.is_empty:
            envelope = envelope.difference(endpoint_blockers)
        result = envelope.buffer(0)
        _cache_put(_ENVELOPE_CACHE, cache_key, result)
        return result

    field = _build_route_field(
        packet=packet,
        base_radius=base_radius,
        start_center=start_center,
        profile=profile,
        resolution=routing_resolution,
    )
    cells: list[BaseGeometry] = []
    cell_radius = min(routing_resolution / 4.0, 0.25)
    for key, distance in field.distances.items():
        if distance > effective_distance + _route_budget_tolerance(routing_resolution):
            continue
        x, y = field.nodes[key]
        point = Point(x, y)
        if not endpoint_blockers.is_empty and endpoint_blockers.covers(point):
            continue
        cells.append(point.buffer(cell_radius))
    if not cells:
        envelope = Polygon()
    else:
        envelope = unary_union(cells).intersection(board_center_region)
    if not endpoint_blockers.is_empty:
        envelope = envelope.difference(endpoint_blockers)
    result = envelope.buffer(0)
    _cache_put(_ENVELOPE_CACHE, cache_key, result)
    return result


def movement_envelope_from_region(
    packet: MapPacket,
    *,
    source_center_region: BaseGeometry,
    base_diameter: float,
    move_distance: float,
    movement_profile_id: str = DEFAULT_MOVEMENT_PROFILE_ID,
    routing_resolution: float = DEFAULT_ROUTING_RESOLUTION_INCHES,
) -> BaseGeometry:
    _require_positive("base_diameter", base_diameter)
    _require_non_negative("move_distance", move_distance)
    _require_positive("routing_resolution", routing_resolution)
    base_radius = base_diameter / 2.0
    board_center_region = base_center_region(packet, base_radius)
    profile = movement_profile_for_id(movement_profile_id)
    effective_distance = effective_move_distance(move_distance, profile.profile_id)
    endpoint_blockers = dense_endpoint_collision_regions(packet, base_radius)
    source_region = source_center_region.intersection(board_center_region).buffer(0)
    if not endpoint_blockers.is_empty:
        source_region = source_region.difference(endpoint_blockers).buffer(0)
    if source_region.is_empty:
        return Polygon()

    if effective_distance <= MOVEMENT_ROUTING_TOLERANCE_INCHES:
        return source_region

    traversal_blockers = _traversal_blockers(packet, base_radius, profile)
    if profile.ignores_dense_traversal or traversal_blockers.is_empty:
        envelope = source_region.buffer(effective_distance).intersection(board_center_region)
        if not endpoint_blockers.is_empty:
            envelope = envelope.difference(endpoint_blockers)
        return envelope.buffer(0)

    field = _build_route_field_from_region(
        packet=packet,
        base_radius=base_radius,
        source_center_region=source_region,
        profile=profile,
        resolution=routing_resolution,
    )
    cells: list[BaseGeometry] = [source_region]
    cell_radius = min(routing_resolution / 4.0, 0.25)
    for key, distance in field.distances.items():
        if distance > effective_distance + _route_budget_tolerance(routing_resolution):
            continue
        x, y = field.nodes[key]
        point = Point(x, y)
        if not endpoint_blockers.is_empty and endpoint_blockers.covers(point):
            continue
        cells.append(point.buffer(cell_radius))
    envelope = unary_union(cells).intersection(board_center_region)
    if not endpoint_blockers.is_empty:
        envelope = envelope.difference(endpoint_blockers)
    return envelope.buffer(0)


def movement_endpoint_diagnostic(
    packet: MapPacket,
    *,
    start_center: tuple[float, float],
    target_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    movement_profile_id: str = DEFAULT_MOVEMENT_PROFILE_ID,
    routing_resolution: float = DEFAULT_ROUTING_RESOLUTION_INCHES,
) -> MovementEndpointDiagnostic:
    _require_positive("base_diameter", base_diameter)
    _require_positive("move_distance", move_distance)
    _require_positive("routing_resolution", routing_resolution)
    _require_finite_point("start_center", start_center)
    _require_finite_point("target_center", target_center)
    base_radius = base_diameter / 2.0
    board_center_region = base_center_region(packet, base_radius)
    profile = movement_profile_for_id(movement_profile_id)
    effective_distance = effective_move_distance(move_distance, profile.profile_id)
    endpoint_blockers = dense_endpoint_collision_regions(packet, base_radius)
    traversal_blockers = _traversal_blockers(packet, base_radius, profile)
    raw_dense_blockers = _dense_movement_blockers(packet)
    metadata = _routing_metadata(
        profile=profile,
        resolution=routing_resolution,
        node_count=0,
        snapped_endpoint=None,
    )

    distance = hypot(target_center[0] - start_center[0], target_center[1] - start_center[1])
    start_within_board = board_center_region.covers(Point(start_center))
    target_within_board = board_center_region.covers(Point(target_center))
    within_board = start_within_board and target_within_board
    start_clear = not endpoint_blockers.covers(Point(start_center))
    target_clear = not endpoint_blockers.covers(Point(target_center))
    swept_path = swept_base_path(
        start_center=start_center,
        target_center=target_center,
        base_diameter=base_diameter,
    )
    corridor_clear = (
        raw_dense_blockers.is_empty
        or profile.ignores_dense_traversal
        or not swept_path.intersects(raw_dense_blockers)
    )
    route_distance: float | None = None
    route_points: tuple[tuple[float, float], ...] = ()
    if within_board and start_clear and target_clear:
        if profile.ignores_dense_traversal or traversal_blockers.is_empty or corridor_clear:
            route_distance = distance
            route_points = (start_center, target_center)
        else:
            field = _build_route_field(
                packet=packet,
                base_radius=base_radius,
                start_center=start_center,
                profile=profile,
                resolution=routing_resolution,
            )
            target_key = _nearest_visible_key(
                target_center,
                nodes=field.nodes,
                blockers=traversal_blockers,
            )
            metadata = _routing_metadata(
                profile=profile,
                resolution=routing_resolution,
                node_count=len(field.nodes),
                snapped_endpoint=field.nodes.get(target_key) if target_key is not None else None,
            )
            if target_key is not None and target_key in field.distances:
                snapped_target = field.nodes[target_key]
                route_distance = field.distances[target_key] + hypot(
                    target_center[0] - snapped_target[0],
                    target_center[1] - snapped_target[1],
                )
                route_points = _reconstruct_route_points(
                    field=field,
                    target_key=target_key,
                    actual_start=start_center,
                    actual_target=target_center,
                )
    budget_tolerance = (
        _route_budget_tolerance(routing_resolution)
        if metadata.node_count > 0
        else MOVEMENT_ROUTING_TOLERANCE_INCHES
    )
    within_distance = (
        route_distance is not None and route_distance <= effective_distance + budget_tolerance
    )
    clear_of_dense_features = (
        target_clear and start_clear and (corridor_clear or route_distance is not None)
    )

    reasons: list[MovementDiagnosticReason] = []
    if not within_distance:
        reasons.append(
            MovementDiagnosticReason(
                reason_id="target-outside-move-distance",
                detail=(
                    "Target center is outside the estimated route distance for the selected "
                    "movement assumptions."
                ),
            )
        )
    if not start_within_board:
        reasons.append(
            MovementDiagnosticReason(
                reason_id="start-outside-board",
                detail="Start center cannot keep the circular base fully inside the board.",
            )
        )
    if not target_within_board:
        reasons.append(
            MovementDiagnosticReason(
                reason_id="target-outside-board",
                detail="Target center cannot keep the circular base fully inside the board.",
            )
        )
    if not start_clear:
        reasons.append(
            MovementDiagnosticReason(
                reason_id="dense-feature-start-collision",
                detail="Start base overlaps a dense feature in the 2D estimate.",
            )
        )
    if not target_clear:
        reasons.append(
            MovementDiagnosticReason(
                reason_id="dense-feature-target-collision",
                detail="Target base overlaps a dense feature in the 2D estimate.",
            )
        )
    if target_clear and not corridor_clear and not within_distance:
        reasons.append(
            MovementDiagnosticReason(
                reason_id="dense-feature-swept-corridor",
                detail=(
                    "Direct swept circular-base corridor crosses a dense feature; the estimated "
                    "route is not within the selected movement distance."
                ),
            )
        )
    if route_distance is None and within_board and start_clear and target_clear:
        reasons.append(
            MovementDiagnosticReason(
                reason_id="dense-feature-route-blocked",
                detail="No estimated route around dense feature traversal blockers was found.",
            )
        )

    return MovementEndpointDiagnostic(
        distance=round(distance, 6),
        within_distance=within_distance,
        within_board=within_board,
        clear_of_dense_features=clear_of_dense_features,
        estimated_reachable=not reasons,
        reasons=tuple(reasons),
        route_distance=round(route_distance, 6) if route_distance is not None else None,
        route_points=tuple((round(x, 6), round(y, 6)) for x, y in route_points),
        effective_move_distance=round(effective_distance, 6),
        routing_metadata=metadata,
    )


def swept_base_path(
    *,
    start_center: tuple[float, float],
    target_center: tuple[float, float],
    base_diameter: float,
) -> BaseGeometry:
    _require_positive("base_diameter", base_diameter)
    base_radius = base_diameter / 2.0
    if start_center == target_center:
        return Point(start_center).buffer(base_radius)
    return LineString([start_center, target_center]).buffer(base_radius, cap_style="round")


def swept_route_path(
    *,
    route_points: tuple[tuple[float, float], ...],
    base_diameter: float,
) -> BaseGeometry:
    _require_positive("base_diameter", base_diameter)
    base_radius = base_diameter / 2.0
    if len(route_points) < 2:
        return Polygon()
    if route_points[0] == route_points[-1]:
        return Point(route_points[0]).buffer(base_radius)
    return LineString(route_points).buffer(base_radius, cap_style="round")


def dense_movement_collision_regions(packet: MapPacket, base_radius: float) -> BaseGeometry:
    return dense_endpoint_collision_regions(packet, base_radius)


def dense_endpoint_collision_regions(packet: MapPacket, base_radius: float) -> BaseGeometry:
    if base_radius < 0:
        raise ValueError("base_radius must be non-negative")
    dense_blockers = _dense_movement_blockers(packet)
    if dense_blockers.is_empty:
        return Polygon()
    return dense_blockers.buffer(base_radius)


def _dense_movement_blockers(packet: MapPacket) -> BaseGeometry:
    blockers = [feature.polygon() for feature in packet.dense_features if feature.blocks_los]
    return unary_union(blockers) if blockers else Polygon()


def base_center_region(packet: MapPacket, base_radius: float) -> Polygon:
    if base_radius < 0:
        raise ValueError("base_radius must be non-negative")
    min_x = min(base_radius, packet.board.width / 2.0)
    max_x = max(packet.board.width - base_radius, min_x)
    min_y = min(base_radius, packet.board.height / 2.0)
    max_y = max(packet.board.height - base_radius, min_y)
    return box(min_x, min_y, max_x, max_y)


def _require_positive(field_name: str, value: float) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_non_negative(field_name: str, value: float) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _require_finite_point(field_name: str, point: tuple[float, float]) -> None:
    if len(point) != 2 or not all(isfinite(value) for value in point):
        raise ValueError(f"{field_name} must contain two finite coordinates")


def _traversal_blockers(
    packet: MapPacket,
    base_radius: float,
    profile: MovementProfile,
) -> BaseGeometry:
    if profile.ignores_dense_traversal:
        return Polygon()
    dense_blockers = _dense_movement_blockers(packet)
    if dense_blockers.is_empty:
        return Polygon()
    return dense_blockers.buffer(base_radius + MOVEMENT_ROUTING_TOLERANCE_INCHES)


def _routing_metadata(
    *,
    profile: MovementProfile,
    resolution: float,
    node_count: int,
    snapped_endpoint: tuple[float, float] | None,
) -> MovementRoutingMetadata:
    return MovementRoutingMetadata(
        algorithm_version=MOVEMENT_ROUTING_ALGORITHM_VERSION,
        resolution_inches=resolution,
        tolerance_inches=MOVEMENT_ROUTING_TOLERANCE_INCHES,
        traversal_policy=profile.traversal_policy,
        endpoint_occupancy_policy=profile.endpoint_occupancy_policy,
        node_count=node_count,
        snapped_endpoint=snapped_endpoint,
    )


def _build_route_field(
    *,
    packet: MapPacket,
    base_radius: float,
    start_center: tuple[float, float],
    profile: MovementProfile,
    resolution: float,
) -> _RouteField:
    cache_key: _RouteFieldCacheKey = (
        _packet_geometry_key(packet),
        round(base_radius, 6),
        (round(start_center[0], 6), round(start_center[1], 6)),
        profile.profile_id,
        round(resolution, 6),
    )
    cached = _ROUTE_FIELD_CACHE.get(cache_key)
    if cached is not None:
        return cached
    board_center_region = base_center_region(packet, base_radius)
    blockers = _traversal_blockers(packet, base_radius, profile)
    nodes = _route_nodes(
        board_center_region=board_center_region,
        blockers=blockers,
        resolution=resolution,
    )
    if len(nodes) > MAX_ROUTING_GRID_NODES:
        raise MovementRoutingBudgetExceeded(
            node_count=len(nodes),
            node_limit=MAX_ROUTING_GRID_NODES,
        )
    start_key = _nearest_visible_key(start_center, nodes=nodes, blockers=blockers)
    if start_key is None:
        metadata = _routing_metadata(
            profile=profile,
            resolution=resolution,
            node_count=len(nodes),
            snapped_endpoint=None,
        )
        field = _RouteField(
            nodes=nodes,
            distances={},
            previous={},
            start_key=(0, 0),
            metadata=metadata,
        )
        _cache_put(_ROUTE_FIELD_CACHE, cache_key, field)
        return field
    distances, previous = _dijkstra(
        nodes=nodes,
        start_key=start_key,
        resolution=resolution,
        blockers=blockers,
    )
    metadata = _routing_metadata(
        profile=profile,
        resolution=resolution,
        node_count=len(nodes),
        snapped_endpoint=None,
    )
    field = _RouteField(
        nodes=nodes,
        distances=distances,
        previous=previous,
        start_key=start_key,
        metadata=metadata,
    )
    _cache_put(_ROUTE_FIELD_CACHE, cache_key, field)
    return field


def _build_route_field_from_region(
    *,
    packet: MapPacket,
    base_radius: float,
    source_center_region: BaseGeometry,
    profile: MovementProfile,
    resolution: float,
) -> _RouteField:
    cache_key: _RegionRouteFieldCacheKey = (
        _packet_geometry_key(packet),
        round(base_radius, 6),
        _geometry_digest(source_center_region),
        profile.profile_id,
        round(resolution, 6),
    )
    cached = _REGION_ROUTE_FIELD_CACHE.get(cache_key)
    if cached is not None:
        return cached
    board_center_region = base_center_region(packet, base_radius)
    blockers = _traversal_blockers(packet, base_radius, profile)
    nodes = _route_nodes(
        board_center_region=board_center_region,
        blockers=blockers,
        resolution=resolution,
    )
    if len(nodes) > MAX_ROUTING_GRID_NODES:
        raise MovementRoutingBudgetExceeded(
            node_count=len(nodes),
            node_limit=MAX_ROUTING_GRID_NODES,
        )
    source_keys = tuple(
        key for key, node in nodes.items() if source_center_region.covers(Point(node))
    )
    if not source_keys:
        metadata = _routing_metadata(
            profile=profile,
            resolution=resolution,
            node_count=len(nodes),
            snapped_endpoint=None,
        )
        field = _RouteField(
            nodes=nodes,
            distances={},
            previous={},
            start_key=(0, 0),
            metadata=metadata,
        )
        _cache_put(_REGION_ROUTE_FIELD_CACHE, cache_key, field)
        return field
    distances, previous = _multi_source_dijkstra(
        nodes=nodes,
        source_keys=source_keys,
        resolution=resolution,
        blockers=blockers,
    )
    metadata = _routing_metadata(
        profile=profile,
        resolution=resolution,
        node_count=len(nodes),
        snapped_endpoint=None,
    )
    field = _RouteField(
        nodes=nodes,
        distances=distances,
        previous=previous,
        start_key=source_keys[0],
        metadata=metadata,
    )
    _cache_put(_REGION_ROUTE_FIELD_CACHE, cache_key, field)
    return field


def _route_nodes(
    *,
    board_center_region: BaseGeometry,
    blockers: BaseGeometry,
    resolution: float,
) -> dict[_GridKey, tuple[float, float]]:
    min_x, min_y, max_x, max_y = board_center_region.bounds
    xs = _axis_values(min_x, max_x, resolution)
    ys = _axis_values(min_y, max_y, resolution)
    nodes: dict[_GridKey, tuple[float, float]] = {}
    for ix, x in enumerate(xs):
        for iy, y in enumerate(ys):
            point = Point(x, y)
            if not board_center_region.covers(point):
                continue
            if not blockers.is_empty and blockers.covers(point):
                continue
            nodes[(ix, iy)] = (x, y)
    return nodes


def _axis_values(min_value: float, max_value: float, resolution: float) -> list[float]:
    if max_value <= min_value:
        return [round(min_value, 6)]
    count = max(0, floor((max_value - min_value) / resolution))
    values = [round(min_value + index * resolution, 6) for index in range(count + 1)]
    if max_value - values[-1] > resolution / 4.0:
        values.append(round(max_value, 6))
    elif values[-1] != round(max_value, 6):
        values[-1] = round(max_value, 6)
    return values


def _nearest_visible_key(
    point: tuple[float, float],
    *,
    nodes: dict[_GridKey, tuple[float, float]],
    blockers: BaseGeometry,
) -> _GridKey | None:
    if not nodes:
        return None
    candidates = sorted(
        nodes.items(),
        key=lambda item: hypot(point[0] - item[1][0], point[1] - item[1][1]),
    )
    for key, node in candidates[:32]:
        segment = LineString([point, node])
        if _segment_clear(segment, blockers):
            return key
    return None


def _dijkstra(
    *,
    nodes: dict[_GridKey, tuple[float, float]],
    start_key: _GridKey,
    resolution: float,
    blockers: BaseGeometry,
) -> tuple[dict[_GridKey, float], dict[_GridKey, _GridKey | None]]:
    distances: dict[_GridKey, float] = {start_key: 0.0}
    previous: dict[_GridKey, _GridKey | None] = {start_key: None}
    queue: list[tuple[float, _GridKey]] = [(0.0, start_key)]
    while queue:
        current_distance, key = heappop(queue)
        if current_distance > distances[key]:
            continue
        for neighbor in _neighbors(key, nodes, blockers):
            cost = _edge_cost(key, neighbor, nodes, resolution)
            candidate = current_distance + cost
            if candidate + 1e-9 < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                previous[neighbor] = key
                heappush(queue, (candidate, neighbor))
    return distances, previous


def _multi_source_dijkstra(
    *,
    nodes: dict[_GridKey, tuple[float, float]],
    source_keys: tuple[_GridKey, ...],
    resolution: float,
    blockers: BaseGeometry,
) -> tuple[dict[_GridKey, float], dict[_GridKey, _GridKey | None]]:
    distances: dict[_GridKey, float] = {key: 0.0 for key in source_keys}
    previous: dict[_GridKey, _GridKey | None] = {key: None for key in source_keys}
    queue: list[tuple[float, _GridKey]] = []
    for key in source_keys:
        heappush(queue, (0.0, key))
    while queue:
        current_distance, key = heappop(queue)
        if current_distance > distances[key]:
            continue
        for neighbor in _neighbors(key, nodes, blockers):
            cost = _edge_cost(key, neighbor, nodes, resolution)
            candidate = current_distance + cost
            if candidate + 1e-9 < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                previous[neighbor] = key
                heappush(queue, (candidate, neighbor))
    return distances, previous


def _neighbors(
    key: _GridKey,
    nodes: dict[_GridKey, tuple[float, float]],
    blockers: BaseGeometry,
) -> list[_GridKey]:
    ix, iy = key
    candidates = [
        (ix - 1, iy - 1),
        (ix - 1, iy),
        (ix - 1, iy + 1),
        (ix, iy - 1),
        (ix, iy + 1),
        (ix + 1, iy - 1),
        (ix + 1, iy),
        (ix + 1, iy + 1),
    ]
    return [
        candidate
        for candidate in candidates
        if candidate in nodes
        and _segment_clear(LineString([nodes[key], nodes[candidate]]), blockers)
    ]


def _segment_clear(segment: LineString, blockers: BaseGeometry) -> bool:
    return blockers.is_empty or not segment.intersects(blockers)


def _edge_cost(
    first: _GridKey,
    second: _GridKey,
    nodes: dict[_GridKey, tuple[float, float]],
    resolution: float,
) -> float:
    point_a = nodes[first]
    point_b = nodes[second]
    distance = hypot(point_b[0] - point_a[0], point_b[1] - point_a[1])
    return distance if distance > 0 else resolution


def _reconstruct_route_points(
    *,
    field: _RouteField,
    target_key: _GridKey,
    actual_start: tuple[float, float],
    actual_target: tuple[float, float],
) -> tuple[tuple[float, float], ...]:
    keys: list[_GridKey] = []
    current: _GridKey | None = target_key
    while current is not None:
        keys.append(current)
        current = field.previous.get(current)
    keys.reverse()
    points = [actual_start]
    points.extend(field.nodes[key] for key in keys if field.nodes[key] != actual_start)
    if points[-1] != actual_target:
        points.append(actual_target)
    return tuple(points)


def _route_budget_tolerance(resolution: float) -> float:
    return min(0.05, resolution * 0.05) + MOVEMENT_ROUTING_TOLERANCE_INCHES


def _envelope_cache_key(
    *,
    packet: MapPacket,
    start_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    movement_profile_id: str,
    routing_resolution: float,
) -> _EnvelopeCacheKey:
    return (
        _packet_geometry_key(packet),
        (round(start_center[0], 6), round(start_center[1], 6)),
        round(base_diameter, 6),
        round(move_distance, 6),
        movement_profile_id,
        round(routing_resolution, 6),
    )


def _packet_geometry_key(packet: MapPacket) -> _PacketGeometryKey:
    features = tuple(
        tuple((round(x, 6), round(y, 6)) for x, y in feature.footprint)
        for feature in packet.dense_features
        if feature.blocks_los
    )
    return (packet.id, round(packet.board.width, 6), round(packet.board.height, 6), features)


def _geometry_digest(geometry: BaseGeometry) -> str:
    return hashlib.sha256(geometry.buffer(0).wkb).hexdigest()


def _cache_put[CacheKey: Hashable, CacheValue](
    cache: MutableMapping[CacheKey, CacheValue],
    key: CacheKey,
    value: CacheValue,
) -> None:
    if len(cache) >= _CACHE_LIMIT:
        first_key = next(iter(cache))
        cache.pop(first_key, None)
    cache[key] = value
