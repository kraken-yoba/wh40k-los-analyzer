from shapely.geometry import Point as ShapelyPoint

from fortyk_los_backend.domain.los import LineOfSightRequest, compute_point_los
from fortyk_los_backend.domain.models import (
    CanonicalBaseModel,
    CanonicalLayout,
    Point,
)


class Region(CanonicalBaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class GridSpec(Region):
    step: float


class HeatmapCell(CanonicalBaseModel):
    center: Point
    visible_source_count: int
    normalized_visibility: float


class FiringLaneHeatmap(CanonicalBaseModel):
    cells: tuple[HeatmapCell, ...]
    source_sample_count: int
    max_visible_source_count: int


class MovementExposureRequest(CanonicalBaseModel):
    deployment_zone_id: str
    movement_distance: float
    threat_region: Region
    sample_step: float


class MovementExposureResult(CanonicalBaseModel):
    reachable_sample_count: int
    exposed_sample_count: int
    exposed_fraction: float


class TerrainCoverageRequest(CanonicalBaseModel):
    feature_id: str
    source_region: Region
    target_grid: GridSpec


class TerrainCoverageResult(CanonicalBaseModel):
    feature_id: str
    blocked_with_feature_count: int
    blocked_without_feature_count: int
    coverage_delta: int


def generate_firing_lane_heatmap(
    layout: CanonicalLayout,
    *,
    source_region: Region,
    target_grid: GridSpec,
) -> FiringLaneHeatmap:
    source_samples = _sample_region(source_region, source_region.x_max - source_region.x_min or 1.0)
    target_samples = _sample_region(target_grid, target_grid.step)
    cells: list[HeatmapCell] = []

    for target in target_samples:
        if _point_inside_terrain(layout, target):
            visible_count = 0
        else:
            visible_count = sum(
                source == target
                or compute_point_los(
                    layout,
                    LineOfSightRequest(source=source, target=target),
                ).visible
                for source in source_samples
            )
        normalized_visibility = visible_count / len(source_samples) if source_samples else 0.0
        cells.append(
            HeatmapCell(
                center=target,
                visible_source_count=visible_count,
                normalized_visibility=normalized_visibility,
            )
        )

    max_visible = max((cell.visible_source_count for cell in cells), default=0)
    return FiringLaneHeatmap(
        cells=tuple(cells),
        source_sample_count=len(source_samples),
        max_visible_source_count=max_visible,
    )


def measure_deployment_exposure(
    layout: CanonicalLayout,
    request: MovementExposureRequest,
) -> MovementExposureResult:
    deployment = next(
        zone for zone in layout.deployments if zone.zone_id == request.deployment_zone_id
    )
    deployment_polygon = deployment.area.to_shapely()
    reachable_samples = [
        sample
        for sample in _sample_board(layout, request.sample_step)
        if deployment_polygon.distance(ShapelyPoint(sample.x, sample.y))
        <= request.movement_distance + 1e-9
    ]
    threat_samples = _sample_region(request.threat_region, request.sample_step)
    exposed_count = sum(
        any(
            compute_point_los(layout, LineOfSightRequest(source=sample, target=threat)).visible
            for threat in threat_samples
            if sample != threat
        )
        for sample in reachable_samples
    )

    return MovementExposureResult(
        reachable_sample_count=len(reachable_samples),
        exposed_sample_count=exposed_count,
        exposed_fraction=exposed_count / len(reachable_samples) if reachable_samples else 0.0,
    )


def measure_terrain_coverage(
    layout: CanonicalLayout,
    request: TerrainCoverageRequest,
) -> TerrainCoverageResult:
    source_samples = _sample_region(request.source_region, request.target_grid.step)
    target_samples = _sample_region(request.target_grid, request.target_grid.step)
    without_feature = layout.model_copy(
        update={
            "blockers": tuple(
                blocker for blocker in layout.blockers if blocker.feature_id != request.feature_id
            )
        }
    )

    blocked_with = _blocked_pair_count(layout, source_samples, target_samples)
    blocked_without = _blocked_pair_count(without_feature, source_samples, target_samples)
    return TerrainCoverageResult(
        feature_id=request.feature_id,
        blocked_with_feature_count=blocked_with,
        blocked_without_feature_count=blocked_without,
        coverage_delta=blocked_with - blocked_without,
    )


def _blocked_pair_count(
    layout: CanonicalLayout,
    source_samples: tuple[Point, ...],
    target_samples: tuple[Point, ...],
) -> int:
    return sum(
        not compute_point_los(layout, LineOfSightRequest(source=source, target=target)).visible
        for source in source_samples
        for target in target_samples
        if source != target
    )


def _sample_board(layout: CanonicalLayout, step: float) -> tuple[Point, ...]:
    return _sample_region(
        Region(x_min=0.0, y_min=0.0, x_max=layout.board.width, y_max=layout.board.height),
        step,
    )


def _point_inside_terrain(layout: CanonicalLayout, point: Point) -> bool:
    shapely_point = ShapelyPoint(point.x, point.y)
    return any(
        feature.footprint.to_shapely().covers(shapely_point)
        for feature in layout.terrain_features
    )


def _sample_region(region: Region, step: float) -> tuple[Point, ...]:
    xs = _sample_axis(region.x_min, region.x_max, step)
    ys = _sample_axis(region.y_min, region.y_max, step)
    return tuple(Point(x=x, y=y) for y in ys for x in xs)


def _sample_axis(start: float, stop: float, step: float) -> tuple[float, ...]:
    if step <= 0:
        raise ValueError("step must be positive")
    values: list[float] = []
    current = start
    while current <= stop + 1e-9:
        values.append(round(current, 4))
        current += step
    if not values or values[-1] != round(stop, 4):
        values.append(round(stop, 4))
    return tuple(values)
