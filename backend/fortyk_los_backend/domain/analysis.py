from pydantic import Field, FiniteFloat, model_validator
from shapely.geometry import Point as ShapelyPoint

from fortyk_los_backend.domain.los import LineOfSightRequest, compute_point_los
from fortyk_los_backend.domain.models import (
    CanonicalBaseModel,
    CanonicalLayout,
    Point,
)


class Region(CanonicalBaseModel):
    x_min: FiniteFloat
    y_min: FiniteFloat
    x_max: FiniteFloat
    y_max: FiniteFloat

    @model_validator(mode="after")
    def validate_bounds(self) -> "Region":
        if self.x_min > self.x_max:
            raise ValueError("x_min must be less than or equal to x_max")
        if self.y_min > self.y_max:
            raise ValueError("y_min must be less than or equal to y_max")
        return self


class GridSpec(Region):
    step: FiniteFloat = Field(gt=0)


class HeatmapCell(CanonicalBaseModel):
    center: Point
    visible_source_count: int
    normalized_visibility: float
    no_data: bool


class FiringLaneHeatmap(CanonicalBaseModel):
    cells: tuple[HeatmapCell, ...]
    source_sample_count: int
    valid_source_count: int
    max_visible_source_count: int


class MovementExposureRequest(CanonicalBaseModel):
    deployment_zone_id: str
    movement_distance: FiniteFloat = Field(ge=0)
    threat_region: Region
    sample_step: FiniteFloat = Field(gt=0)


class ExposureCell(CanonicalBaseModel):
    center: Point
    exposed: bool


class MovementExposureResult(CanonicalBaseModel):
    reachable_sample_count: int
    exposed_sample_count: int
    exposed_fraction: float
    reachable_cells: tuple[ExposureCell, ...]


class TerrainCoverageRequest(CanonicalBaseModel):
    feature_id: str
    source_region: Region
    target_grid: GridSpec


class TerrainCoverageCell(CanonicalBaseModel):
    center: Point
    blocked_with_feature: bool
    blocked_without_feature: bool
    changed: bool


class TerrainCoverageResult(CanonicalBaseModel):
    feature_id: str
    blocked_with_feature_count: int
    blocked_without_feature_count: int
    coverage_delta: int
    cells: tuple[TerrainCoverageCell, ...]


def generate_firing_lane_heatmap(
    layout: CanonicalLayout,
    *,
    source_region: Region,
    target_grid: GridSpec,
    source_step: float | None = None,
) -> FiringLaneHeatmap:
    source_samples = _sample_region(source_region, source_step or target_grid.step)
    valid_source_samples = tuple(
        source for source in source_samples if _is_valid_analysis_point(layout, source)
    )
    target_samples = _sample_region(target_grid, target_grid.step)
    cells: list[HeatmapCell] = []

    for target in target_samples:
        if not _is_valid_analysis_point(layout, target):
            visible_count = 0
            no_data = True
        else:
            visible_count = sum(
                source == target
                or compute_point_los(
                    layout,
                    LineOfSightRequest(source=source, target=target),
                ).visible
                for source in valid_source_samples
            )
            no_data = not valid_source_samples
        normalized_visibility = (
            visible_count / len(valid_source_samples) if valid_source_samples else 0.0
        )
        cells.append(
            HeatmapCell(
                center=target,
                visible_source_count=visible_count,
                normalized_visibility=normalized_visibility,
                no_data=no_data,
            )
        )

    max_visible = max((cell.visible_source_count for cell in cells), default=0)
    return FiringLaneHeatmap(
        cells=tuple(cells),
        source_sample_count=len(source_samples),
        valid_source_count=len(valid_source_samples),
        max_visible_source_count=max_visible,
    )


def measure_deployment_exposure(
    layout: CanonicalLayout,
    request: MovementExposureRequest,
) -> MovementExposureResult:
    deployment = next(
        (zone for zone in layout.deployments if zone.zone_id == request.deployment_zone_id),
        None,
    )
    if deployment is None:
        raise ValueError(f"Deployment zone not found: {request.deployment_zone_id}")
    deployment_polygon = deployment.area.to_shapely()
    reachable_samples = [
        sample
        for sample in _sample_board(layout, request.sample_step)
        if deployment_polygon.distance(ShapelyPoint(sample.x, sample.y))
        <= request.movement_distance + 1e-9
        and _is_valid_analysis_point(layout, sample)
    ]
    threat_samples = _sample_region(request.threat_region, request.sample_step)
    reachable_cells: list[ExposureCell] = []
    for sample in reachable_samples:
        exposed = any(
            compute_point_los(layout, LineOfSightRequest(source=sample, target=threat)).visible
            for threat in threat_samples
            if sample != threat
        )
        reachable_cells.append(ExposureCell(center=sample, exposed=exposed))
    exposed_count = sum(cell.exposed for cell in reachable_cells)

    return MovementExposureResult(
        reachable_sample_count=len(reachable_samples),
        exposed_sample_count=exposed_count,
        exposed_fraction=exposed_count / len(reachable_samples) if reachable_samples else 0.0,
        reachable_cells=tuple(reachable_cells),
    )


def measure_terrain_coverage(
    layout: CanonicalLayout,
    request: TerrainCoverageRequest,
) -> TerrainCoverageResult:
    if request.feature_id not in {feature.feature_id for feature in layout.terrain_features}:
        raise ValueError(f"Terrain feature not found: {request.feature_id}")
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
    cells = _terrain_coverage_cells(layout, without_feature, source_samples, target_samples)
    return TerrainCoverageResult(
        feature_id=request.feature_id,
        blocked_with_feature_count=blocked_with,
        blocked_without_feature_count=blocked_without,
        coverage_delta=blocked_with - blocked_without,
        cells=cells,
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


def _is_valid_analysis_point(layout: CanonicalLayout, point: Point) -> bool:
    if point.x < 0 or point.y < 0 or point.x > layout.board.width or point.y > layout.board.height:
        return False
    shapely_point = ShapelyPoint(point.x, point.y)
    if any(blocker.to_shapely().distance(shapely_point) <= 1e-9 for blocker in layout.blockers):
        return False
    return not _point_inside_movement_blocking_terrain(layout, point)


def _point_inside_movement_blocking_terrain(layout: CanonicalLayout, point: Point) -> bool:
    shapely_point = ShapelyPoint(point.x, point.y)
    return any(
        feature.footprint.to_shapely().covers(shapely_point)
        for feature in layout.terrain_features
        if feature.movement_blocking
    )


def _terrain_coverage_cells(
    layout: CanonicalLayout,
    without_feature: CanonicalLayout,
    source_samples: tuple[Point, ...],
    target_samples: tuple[Point, ...],
) -> tuple[TerrainCoverageCell, ...]:
    cells: list[TerrainCoverageCell] = []
    for target in target_samples:
        blocked_with = any(
            not compute_point_los(layout, LineOfSightRequest(source=source, target=target)).visible
            for source in source_samples
            if source != target
        )
        blocked_without = any(
            not compute_point_los(
                without_feature,
                LineOfSightRequest(source=source, target=target),
            ).visible
            for source in source_samples
            if source != target
        )
        cells.append(
            TerrainCoverageCell(
                center=target,
                blocked_with_feature=blocked_with,
                blocked_without_feature=blocked_without,
                changed=blocked_with != blocked_without,
            )
        )
    return tuple(cells)


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
