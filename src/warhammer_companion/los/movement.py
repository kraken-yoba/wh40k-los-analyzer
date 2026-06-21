from __future__ import annotations

from math import hypot

from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.movement import MovementDiagnosticReason, MovementEndpointDiagnostic


def movement_envelope(
    packet: MapPacket,
    *,
    start_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
) -> BaseGeometry:
    _require_positive("base_diameter", base_diameter)
    _require_positive("move_distance", move_distance)
    base_radius = base_diameter / 2.0
    board_center_region = _board_center_region(packet, base_radius)
    dense_collision_regions = dense_movement_collision_regions(packet, base_radius)

    envelope = Point(start_center).buffer(move_distance).intersection(board_center_region)
    if not dense_collision_regions.is_empty:
        envelope = envelope.difference(dense_collision_regions)
    return envelope.buffer(0)


def movement_endpoint_diagnostic(
    packet: MapPacket,
    *,
    start_center: tuple[float, float],
    target_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
) -> MovementEndpointDiagnostic:
    _require_positive("base_diameter", base_diameter)
    _require_positive("move_distance", move_distance)
    base_radius = base_diameter / 2.0
    board_center_region = _board_center_region(packet, base_radius)
    dense_collision_regions = dense_movement_collision_regions(packet, base_radius)
    dense_blockers = _dense_movement_blockers(packet)

    distance = hypot(target_center[0] - start_center[0], target_center[1] - start_center[1])
    within_distance = distance <= move_distance + 1e-9
    start_within_board = board_center_region.covers(Point(start_center))
    target_within_board = board_center_region.covers(Point(target_center))
    within_board = start_within_board and target_within_board
    target_clear = not dense_collision_regions.covers(Point(target_center))
    swept_path = swept_base_path(
        start_center=start_center,
        target_center=target_center,
        base_diameter=base_diameter,
    )
    corridor_clear = dense_blockers.is_empty or not swept_path.intersects(dense_blockers)
    clear_of_dense_features = target_clear and corridor_clear

    reasons: list[MovementDiagnosticReason] = []
    if not within_distance:
        reasons.append(
            MovementDiagnosticReason(
                reason_id="target-outside-move-distance",
                detail="Target center is farther than the selected movement distance.",
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
    if not target_clear:
        reasons.append(
            MovementDiagnosticReason(
                reason_id="dense-feature-target-collision",
                detail="Target base overlaps a dense feature in the 2D estimate.",
            )
        )
    if target_clear and not corridor_clear:
        reasons.append(
            MovementDiagnosticReason(
                reason_id="dense-feature-swept-corridor",
                detail="Straight swept circular base corridor crosses a dense feature.",
            )
        )

    return MovementEndpointDiagnostic(
        distance=round(distance, 6),
        within_distance=within_distance,
        within_board=within_board,
        clear_of_dense_features=clear_of_dense_features,
        estimated_reachable=not reasons,
        reasons=tuple(reasons),
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


def dense_movement_collision_regions(packet: MapPacket, base_radius: float) -> BaseGeometry:
    if base_radius < 0:
        raise ValueError("base_radius must be non-negative")
    dense_blockers = _dense_movement_blockers(packet)
    if dense_blockers.is_empty:
        return Polygon()
    return dense_blockers.buffer(base_radius)


def _dense_movement_blockers(packet: MapPacket) -> BaseGeometry:
    blockers = [feature.polygon() for feature in packet.dense_features if feature.blocks_los]
    return unary_union(blockers) if blockers else Polygon()


def _board_center_region(packet: MapPacket, base_radius: float) -> Polygon:
    if base_radius < 0:
        raise ValueError("base_radius must be non-negative")
    min_x = min(base_radius, packet.board.width / 2.0)
    max_x = max(packet.board.width - base_radius, min_x)
    min_y = min(base_radius, packet.board.height / 2.0)
    max_y = max(packet.board.height - base_radius, min_y)
    return box(min_x, min_y, max_x, max_y)


def _require_positive(field_name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
