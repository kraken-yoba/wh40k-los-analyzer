from __future__ import annotations

import math

Point = tuple[float, float]

AXIS_ALIGNED_TOLERANCE_INCHES = 0.1
DEPLOYMENT_ARC_SEGMENT_INCHES = 0.25


def smooth_deployment_footprint(points: list[Point]) -> list[Point]:
    if len(points) < 5:
        return points
    smoothed = [points[0]]
    index = 0
    while index < len(points) - 1:
        if _is_axis_aligned_segment(points[index], points[index + 1]):
            smoothed.append(points[index + 1])
            index += 1
            continue

        run_start = index
        while index < len(points) - 1 and not _is_axis_aligned_segment(
            points[index], points[index + 1]
        ):
            index += 1
        run_points = points[run_start : index + 1]
        smoothed.extend(_circular_arc_points(run_points)[1:])
    return smoothed


def _is_axis_aligned_segment(start: Point, end: Point) -> bool:
    return (
        abs(start[0] - end[0]) <= AXIS_ALIGNED_TOLERANCE_INCHES
        or abs(start[1] - end[1]) <= AXIS_ALIGNED_TOLERANCE_INCHES
    )


def _circular_arc_points(points: list[Point]) -> list[Point]:
    if len(points) < 3:
        return points
    circle = _circle_from_three_points(points[0], points[len(points) // 2], points[-1])
    if circle is None:
        return points
    center, radius = circle
    if radius < 0.5 or radius > 60:
        return points

    start_angle = _angle(center, points[0])
    mid_angle = _angle(center, points[len(points) // 2])
    end_angle = _angle(center, points[-1])
    ccw_span = (end_angle - start_angle) % math.tau
    if _angle_is_on_ccw_arc(start_angle, mid_angle, end_angle):
        direction = 1.0
        span = ccw_span
    else:
        direction = -1.0
        span = (start_angle - end_angle) % math.tau
    if span <= 0 or span > math.pi:
        return points

    steps = max(
        len(points) - 1,
        int(math.ceil((radius * span) / DEPLOYMENT_ARC_SEGMENT_INCHES)),
    )
    return [
        (
            center[0] + radius * math.cos(start_angle + direction * span * step / steps),
            center[1] + radius * math.sin(start_angle + direction * span * step / steps),
        )
        for step in range(steps + 1)
    ]


def _circle_from_three_points(a: Point, b: Point, c: Point) -> tuple[Point, float] | None:
    ax, ay = a
    bx, by = b
    cx, cy = c
    determinant = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(determinant) <= 1e-9:
        return None
    ux = (
        (ax * ax + ay * ay) * (by - cy)
        + (bx * bx + by * by) * (cy - ay)
        + (cx * cx + cy * cy) * (ay - by)
    ) / determinant
    uy = (
        (ax * ax + ay * ay) * (cx - bx)
        + (bx * bx + by * by) * (ax - cx)
        + (cx * cx + cy * cy) * (bx - ax)
    ) / determinant
    radius = math.hypot(ax - ux, ay - uy)
    return ((ux, uy), radius)


def _angle(center: Point, point: Point) -> float:
    return math.atan2(point[1] - center[1], point[0] - center[0])


def _angle_is_on_ccw_arc(start: float, angle: float, end: float) -> bool:
    return ((angle - start) % math.tau) <= ((end - start) % math.tau)
