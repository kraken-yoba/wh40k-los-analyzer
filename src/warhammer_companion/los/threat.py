from __future__ import annotations

from math import isfinite

from shapely.geometry import Point, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.threat import (
    ThreatDiceOutcome,
    ThreatProjectionRegion,
    coerce_threat_mode,
)
from warhammer_companion.los.movement import movement_envelope


def threat_projection(
    packet: MapPacket,
    *,
    source_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    threat_range: float,
    mode: str,
) -> BaseGeometry:
    regions = threat_projection_regions(
        packet,
        source_center=source_center,
        base_diameter=base_diameter,
        move_distance=move_distance,
        threat_range=threat_range,
        mode=mode,
    )
    if not regions:
        return _empty_geometry()
    return unary_union([region.geometry for region in regions]).buffer(0)


def threat_projection_regions(
    packet: MapPacket,
    *,
    source_center: tuple[float, float],
    base_diameter: float,
    move_distance: float,
    threat_range: float,
    mode: str,
) -> tuple[ThreatProjectionRegion, ...]:
    _require_finite_point("source_center", source_center)
    _require_non_negative("move_distance", move_distance)
    _require_non_negative("threat_range", threat_range)
    _require_positive("base_diameter", base_diameter)
    threat_mode = coerce_threat_mode(mode)
    board = _board_region(packet)
    base_radius = base_diameter / 2.0
    distribution = threat_distribution(
        mode=threat_mode,
        move_distance=move_distance,
        threat_range=threat_range,
        base_diameter=base_diameter,
    )
    regions: list[ThreatProjectionRegion] = []
    for outcome in distribution:
        if threat_mode == "raw-range":
            region = Point(source_center).buffer(base_radius + threat_range).intersection(board)
        elif move_distance + outcome.variable_inches <= 0:
            region = Point(source_center).buffer(base_radius + threat_range).intersection(board)
        else:
            centers = movement_envelope(
                packet,
                start_center=source_center,
                base_diameter=base_diameter,
                move_distance=move_distance + outcome.variable_inches,
            )
            region = centers.buffer(base_radius + threat_range).intersection(board)
        regions.append(ThreatProjectionRegion(outcome=outcome, geometry=region.buffer(0)))
    return tuple(regions)


def threat_distribution(
    *,
    mode: str,
    move_distance: float,
    threat_range: float,
    base_diameter: float,
) -> tuple[ThreatDiceOutcome, ...]:
    _require_non_negative("move_distance", move_distance)
    _require_non_negative("threat_range", threat_range)
    _require_positive("base_diameter", base_diameter)
    threat_mode = coerce_threat_mode(mode)
    base_radius = base_diameter / 2.0
    fixed_reach = (
        threat_range + base_radius
        if threat_mode == "raw-range"
        else move_distance + threat_range + base_radius
    )
    if threat_mode in {"raw-range", "fixed-move-plus-range"}:
        return (
            ThreatDiceOutcome(
                dice_label="fixed",
                variable_inches=0,
                numerator=1,
                denominator=1,
                probability=1.0,
                total_reach=fixed_reach,
            ),
        )
    if threat_mode == "d6-move-plus-range":
        return tuple(_outcome("D6", total, 1, 6, fixed_reach + total) for total in range(1, 7))
    counts = (1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1)
    return tuple(
        _outcome("2D6", total, count, 36, fixed_reach + total)
        for total, count in zip(range(2, 13), counts, strict=True)
    )


def threat_reach_probability(
    distribution: tuple[ThreatDiceOutcome, ...],
    *,
    threshold_inches: float,
) -> float:
    if not isfinite(threshold_inches):
        return 0.0
    return sum(
        outcome.probability for outcome in distribution if outcome.total_reach >= threshold_inches
    )


def target_threat_probability(
    regions: tuple[ThreatProjectionRegion, ...],
    *,
    target_point: tuple[float, float],
) -> float:
    _require_finite_point("target_point", target_point)
    point = Point(target_point)
    return min(
        1.0,
        sum(region.outcome.probability for region in regions if region.geometry.covers(point)),
    )


def _outcome(
    dice_label: str,
    variable_inches: int,
    numerator: int,
    denominator: int,
    total_reach: float,
) -> ThreatDiceOutcome:
    return ThreatDiceOutcome(
        dice_label=dice_label,
        variable_inches=variable_inches,
        numerator=numerator,
        denominator=denominator,
        probability=numerator / denominator,
        total_reach=total_reach,
    )


def _board_region(packet: MapPacket) -> BaseGeometry:
    return box(0.0, 0.0, packet.board.width, packet.board.height)


def _empty_geometry() -> BaseGeometry:
    return box(0.0, 0.0, 0.0, 0.0)


def _require_positive(field_name: str, value: float) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{field_name} must be a positive finite number")


def _require_non_negative(field_name: str, value: float) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative finite number")


def _require_finite_point(field_name: str, point: tuple[float, float]) -> None:
    if len(point) != 2 or not all(isfinite(value) for value in point):
        raise ValueError(f"{field_name} must contain two finite coordinates")
