from math import cos, sin, tau
from typing import Literal

from pydantic import Field
from shapely.geometry import LineString
from shapely.geometry import Point as ShapelyPoint

from fortyk_los_backend.domain.models import (
    GEOMETRY_EPSILON,
    CanonicalBaseModel,
    CanonicalLayout,
    Point,
)


class BaseProfile(CanonicalBaseModel):
    diameter: float = Field(gt=0)

    @property
    def radius(self) -> float:
        return self.diameter / 2.0


class LineOfSightRequest(CanonicalBaseModel):
    source: Point
    target: Point


class LineOfSightResult(CanonicalBaseModel):
    visible: bool
    blocking_blocker_ids: tuple[str, ...]
    method: str
    sample_count: int = 1


class BaseAwareLineOfSightResult(LineOfSightResult):
    method: Literal["disk-sample-v1"] = "disk-sample-v1"


def compute_point_los(layout: CanonicalLayout, request: LineOfSightRequest) -> LineOfSightResult:
    _require_point_inside_board(layout, request.source, "source")
    _require_point_inside_board(layout, request.target, "target")

    line = LineString([(request.source.x, request.source.y), (request.target.x, request.target.y)])
    blocking_ids: list[str] = []
    for blocker in layout.blockers:
        if _blocker_blocks_line(blocker.to_shapely(), line, request.source, request.target):
            blocking_ids.append(blocker.blocker_id)

    return LineOfSightResult(
        visible=not blocking_ids,
        blocking_blocker_ids=tuple(blocking_ids),
        method="point-segment-v1",
    )


def compute_base_aware_los(
    layout: CanonicalLayout,
    request: LineOfSightRequest,
    *,
    source_base: BaseProfile,
    target_base: BaseProfile,
) -> BaseAwareLineOfSightResult:
    if not is_legal_base_center(layout, request.source, source_base):
        raise ValueError("source base center is not legal")
    if not is_legal_base_center(layout, request.target, target_base):
        raise ValueError("target base center is not legal")

    source_samples = _base_samples(request.source, source_base)
    target_samples = _base_samples(request.target, target_base)
    sample_count = len(source_samples) * len(target_samples)
    all_blockers: set[str] = set()

    for source in source_samples:
        for target in target_samples:
            result = compute_point_los(layout, LineOfSightRequest(source=source, target=target))
            if result.visible:
                return BaseAwareLineOfSightResult(
                    visible=True,
                    blocking_blocker_ids=(),
                    sample_count=sample_count,
                )
            all_blockers.update(result.blocking_blocker_ids)

    return BaseAwareLineOfSightResult(
        visible=False,
        blocking_blocker_ids=tuple(sorted(all_blockers)),
        sample_count=sample_count,
    )


def is_legal_base_center(layout: CanonicalLayout, center: Point, base: BaseProfile) -> bool:
    radius = base.radius
    if (
        center.x - radius < -GEOMETRY_EPSILON
        or center.y - radius < -GEOMETRY_EPSILON
        or center.x + radius > layout.board.width + GEOMETRY_EPSILON
        or center.y + radius > layout.board.height + GEOMETRY_EPSILON
    ):
        return False

    base_disk = ShapelyPoint(center.x, center.y).buffer(radius, quad_segs=16)
    return not any(
        feature.footprint.to_shapely().intersects(base_disk)
        for feature in layout.terrain_features
    )


def _require_point_inside_board(layout: CanonicalLayout, point: Point, role: str) -> None:
    if point.x < 0 or point.y < 0 or point.x > layout.board.width or point.y > layout.board.height:
        raise ValueError(f"{role} is outside board")


def _blocker_blocks_line(
    blocker_line: LineString,
    line: LineString,
    source: Point,
    target: Point,
) -> bool:
    intersection = line.intersection(blocker_line)
    if intersection.is_empty:
        return False
    if intersection.geom_type == "Point":
        point = Point(x=intersection.x, y=intersection.y)
        return not (_same_point(point, source) or _same_point(point, target))
    return True


def _same_point(first: Point, second: Point) -> bool:
    return (
        abs(first.x - second.x) <= GEOMETRY_EPSILON
        and abs(first.y - second.y) <= GEOMETRY_EPSILON
    )


def _base_samples(center: Point, base: BaseProfile) -> tuple[Point, ...]:
    radius = base.radius
    samples = [center]
    for index in range(8):
        angle = tau * index / 8
        samples.append(
            Point(
                x=center.x + radius * cos(angle),
                y=center.y + radius * sin(angle),
            )
        )
    return tuple(samples)
