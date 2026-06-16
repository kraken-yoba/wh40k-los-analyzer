from fortyk_los_backend.domain.analysis import (
    GridSpec,
    MovementExposureRequest,
    Region,
    TerrainCoverageRequest,
    generate_firing_lane_heatmap,
    measure_deployment_exposure,
    measure_terrain_coverage,
)
from fortyk_los_backend.domain.models import (
    Blocker,
    BlockerKind,
    Board,
    CanonicalLayout,
    DeploymentZone,
    LayoutProvenance,
    Point,
    PolygonGeometry,
    TerrainFeature,
    ValidationStatus,
)


def _rectangle(x_min: float, y_min: float, x_max: float, y_max: float) -> PolygonGeometry:
    return PolygonGeometry(
        points=(
            Point(x=x_min, y=y_min),
            Point(x=x_max, y=y_min),
            Point(x=x_max, y=y_max),
            Point(x=x_min, y=y_max),
        )
    )


def _layout() -> CanonicalLayout:
    return CanonicalLayout(
        layout_id="analysis-fixture",
        name="Analysis Fixture",
        board=Board(width=10.0, height=10.0),
        terrain_features=(
            TerrainFeature(
                feature_id="wall-feature",
                label="Wall Feature",
                footprint=_rectangle(4.0, 0.0, 6.0, 10.0),
            ),
        ),
        blockers=(
            Blocker(
                blocker_id="center-wall",
                feature_id="wall-feature",
                kind=BlockerKind.WALL,
                start=Point(x=5.0, y=0.0),
                end=Point(x=5.0, y=10.0),
            ),
        ),
        deployments=(
            DeploymentZone(
                zone_id="left-zone",
                label="Left Zone",
                area=_rectangle(0.0, 0.0, 2.0, 10.0),
            ),
        ),
        provenance=LayoutProvenance(
            source_document_id="synthetic",
            source_page=1,
            extraction_method="synthetic-fixture",
        ),
        validation_status=ValidationStatus.PASSED,
    )


def test_firing_lane_heatmap_counts_visible_source_positions() -> None:
    heatmap = generate_firing_lane_heatmap(
        _layout(),
        source_region=Region(x_min=1.0, y_min=5.0, x_max=9.0, y_max=5.0),
        target_grid=GridSpec(x_min=1.0, y_min=5.0, x_max=9.0, y_max=5.0, step=4.0),
    )

    cell_summaries = [
        (cell.center.x, cell.center.y, cell.visible_source_count) for cell in heatmap.cells
    ]

    assert cell_summaries == [
        (1.0, 5.0, 1),
        (5.0, 5.0, 0),
        (9.0, 5.0, 1),
    ]
    assert heatmap.max_visible_source_count == 1


def test_deployment_exposure_uses_movement_reachable_points() -> None:
    exposure = measure_deployment_exposure(
        _layout(),
        MovementExposureRequest(
            deployment_zone_id="left-zone",
            movement_distance=2.0,
            threat_region=Region(x_min=9.0, y_min=5.0, x_max=9.0, y_max=5.0),
            sample_step=2.0,
        ),
    )

    assert exposure.reachable_sample_count > 0
    assert exposure.exposed_sample_count == 0
    assert exposure.exposed_fraction == 0.0


def test_terrain_coverage_reports_visibility_delta_when_feature_removed() -> None:
    coverage = measure_terrain_coverage(
        _layout(),
        TerrainCoverageRequest(
            feature_id="wall-feature",
            source_region=Region(x_min=1.0, y_min=5.0, x_max=1.0, y_max=5.0),
            target_grid=GridSpec(x_min=9.0, y_min=5.0, x_max=9.0, y_max=5.0, step=1.0),
        ),
    )

    assert coverage.feature_id == "wall-feature"
    assert coverage.blocked_with_feature_count == 1
    assert coverage.blocked_without_feature_count == 0
    assert coverage.coverage_delta == 1
