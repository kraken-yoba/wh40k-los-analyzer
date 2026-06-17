from types import SimpleNamespace

from fortyk_los_backend.domain.models import (
    Blocker,
    BlockerKind,
    Board,
    CanonicalLayout,
    LayoutProvenance,
    Point,
    PolygonGeometry,
    TerrainCategory,
    TerrainFeature,
    ValidationStatus,
)
from fortyk_los_backend.domain.terrain_reconciliation import MeasurementAnnotation


def test_reconciliation_passes_only_when_measurements_and_symmetry_pass() -> None:
    from fortyk_los_backend.domain.terrain_reconciliation import (
        reconcile_terrain_layout,
    )

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="Dense A",
                footprint=_rectangle(2.0, 4.0, 6.0, 8.0),
                terrain_category=TerrainCategory.DENSE,
            ),
            TerrainFeature(
                feature_id="terrain-02",
                label="Dense B",
                footprint=_rectangle(38.0, 52.0, 42.0, 56.0),
                terrain_category=TerrainCategory.DENSE,
            ),
        ),
        blockers=(
            Blocker(
                blocker_id="wall-01",
                feature_id="terrain-01",
                kind=BlockerKind.WALL,
                start=Point(x=2.0, y=4.0),
                end=Point(x=6.0, y=4.0),
            ),
            Blocker(
                blocker_id="wall-02",
                feature_id="terrain-02",
                kind=BlockerKind.WALL,
                start=Point(x=38.0, y=56.0),
                end=Point(x=42.0, y=56.0),
            ),
        ),
    )

    report = reconcile_terrain_layout(
        layout,
        measurements=(
            *_corner_measurements(2.0, 4.0, 6.0, 8.0),
            *_corner_measurements(38.0, 52.0, 42.0, 56.0),
        ),
    )

    assert report.status == "passed"
    assert report.measurement_status == "passed"
    assert report.symmetry_status == "passed"
    assert report.final_measurement_status == "passed"
    assert report.final_symmetry_status == "passed"
    assert report.warning_codes == ()
    assert report.process_steps == (
        "standard_terrain_options",
        "image_extraction",
        "grid_snap",
        "measurement_corner_check",
        "symmetry_candidate_check",
        "final_reconciliation",
    )
    option_summary = [
        (option.option_id, option.count, option.dense_feature_count)
        for option in report.standard_options
    ]
    assert option_summary == [
        ("footprint-size-04x04", 2, 2)
    ]
    assert report.standard_options[0].wall_segment_count == 2
    assert all(check.status == "passed" for check in report.measurement_checks)
    assert all(check.verified_corner_count == 4 for check in report.measurement_checks)


def test_reconciliation_proposes_self_centered_alternative_when_it_satisfies_measurements() -> None:
    from fortyk_los_backend.domain.terrain_reconciliation import (
        reconcile_terrain_layout,
    )

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-center",
                label="Dense Center",
                footprint=_rectangle(16.0, 27.0, 28.0, 35.0),
                terrain_category=TerrainCategory.DENSE,
            ),
        )
    )

    report = reconcile_terrain_layout(
        layout,
        measurements=(
            *_corner_measurements(16.0, 26.0, 28.0, 34.0),
        ),
    )

    assert report.status == "passed_with_alternatives"
    assert report.measurement_status == "warning"
    assert report.symmetry_status == "warning"
    assert report.final_measurement_status == "passed"
    assert report.final_symmetry_status == "passed"
    assert report.viable_alternative_count == 1
    assert report.unresolved_feature_ids == ()
    alternative_summary = [
        (candidate.feature_id, candidate.status, candidate.review_reason)
        for candidate in report.alternatives
    ]
    assert alternative_summary == [
        ("terrain-center", "viable", "self_center_satisfies_measurement_and_symmetry")
    ]
    assert report.alternatives[0].proposed_bounds_inches == (16.0, 26.0, 28.0, 34.0)
    assert report.alternatives[0].measurement_status == "passed"
    assert report.alternatives[0].symmetry_residual_inches == 0.0


def test_reconciliation_keeps_asymmetric_features_unresolved_when_alternatives_fail() -> None:
    from fortyk_los_backend.domain.terrain_reconciliation import (
        MeasurementAnnotation,
        reconcile_terrain_layout,
    )

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-big",
                label="Dense Big",
                footprint=_rectangle(16.0, 27.0, 28.0, 35.0),
                terrain_category=TerrainCategory.DENSE,
            ),
            TerrainFeature(
                feature_id="terrain-small",
                label="Small",
                footprint=_rectangle(17.0, 17.0, 23.0, 20.0),
            ),
        )
    )

    report = reconcile_terrain_layout(
        layout,
        measurements=(
            *_corner_measurements(16.0, 26.0, 28.0, 34.0),
            MeasurementAnnotation(value=19.0, x=19.0, y=28.0),
            MeasurementAnnotation(value=28.0, x=19.0, y=28.0),
        ),
    )

    assert report.status == "warning"
    assert report.final_measurement_status == "warning"
    assert report.final_symmetry_status == "warning"
    assert "terrain_reconciliation_unresolved_asymmetry" in report.warning_codes
    assert "terrain-small" in report.unresolved_feature_ids
    candidates_by_feature = {candidate.feature_id: candidate for candidate in report.alternatives}
    assert candidates_by_feature["terrain-big"].status == "viable"
    assert candidates_by_feature["terrain-small"].status == "rejected"
    assert candidates_by_feature["terrain-small"].review_reason == "candidate_not_on_inch_grid"


def test_reconciliation_does_not_use_unrelated_measurement_labels_for_a_corner() -> None:
    from fortyk_los_backend.domain.terrain_reconciliation import (
        MeasurementAnnotation,
        reconcile_terrain_layout,
    )

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="A",
                footprint=_rectangle(2.0, 4.0, 6.0, 8.0),
            ),
            TerrainFeature(
                feature_id="terrain-02",
                label="B",
                footprint=_rectangle(38.0, 52.0, 42.0, 56.0),
            ),
        )
    )

    report = reconcile_terrain_layout(
        layout,
        measurements=(
            MeasurementAnnotation(value=2.0, x=38.0, y=52.0),
            MeasurementAnnotation(value=4.0, x=42.0, y=56.0),
        ),
    )

    check_by_id = {check.feature_id: check for check in report.measurement_checks}
    assert check_by_id["terrain-01"].status == "warning"
    assert check_by_id["terrain-01"].verified_corner_count == 0


def test_reconciliation_requires_distinct_measurements_for_equal_corner_offsets() -> None:
    from fortyk_los_backend.domain.terrain_reconciliation import (
        MeasurementAnnotation,
        reconcile_terrain_layout,
    )

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="A",
                footprint=_rectangle(4.0, 4.0, 8.0, 8.0),
            ),
        )
    )

    report = reconcile_terrain_layout(
        layout,
        measurements=(
            MeasurementAnnotation(value=4.0, x=4.0, y=4.0),
        ),
    )

    assert report.measurement_checks[0].status == "warning"
    assert report.measurement_checks[0].verified_corner_count == 0


def test_standard_options_can_use_source_dimension_catalog_instead_of_current_layout() -> None:
    from fortyk_los_backend.domain.terrain_reconciliation import (
        SourceFootprintDimension,
        standard_terrain_options_from_layout,
    )

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-small",
                label="Small mistaken extraction",
                footprint=_rectangle(17.0, 17.0, 23.0, 20.0),
            ),
        )
    )

    options = standard_terrain_options_from_layout(
        layout,
        template_matches=(
            SimpleNamespace(
                feature_id="terrain-small",
                template_id="template-a",
                status="candidate",
            ),
        ),
        source_dimensions=(
            SourceFootprintDimension(
                template_id="template-a",
                width_inches=12.0,
                height_inches=8.0,
                evidence_count=9,
            ),
        ),
    )

    assert [(option.width_inches, option.height_inches) for option in options] == [
        (12.0, 8.0)
    ]
    assert options[0].source_kind == "source_catalog"
    assert options[0].dimension_evidence_count == 9


def test_review_required_template_matches_do_not_create_source_catalog_options() -> None:
    from fortyk_los_backend.domain.terrain_reconciliation import (
        SourceFootprintDimension,
        standard_terrain_options_from_layout,
    )

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-small",
                label="Small mistaken extraction",
                footprint=_rectangle(17.0, 17.0, 23.0, 20.0),
            ),
        )
    )

    options = standard_terrain_options_from_layout(
        layout,
        template_matches=(
            SimpleNamespace(
                feature_id="terrain-small",
                template_id="template-a",
                status="needs_review",
            ),
        ),
        templates=(
            SimpleNamespace(
                template_id="template-a",
                normalized_fragment_paths=((Point(x=0.0, y=0.0), Point(x=1.0, y=1.0)),),
            ),
        ),
        source_dimensions=(
            SourceFootprintDimension(
                template_id="template-a",
                width_inches=12.0,
                height_inches=8.0,
                evidence_count=9,
            ),
        ),
    )

    assert [(option.width_inches, option.height_inches) for option in options] == [
        (6.0, 3.0)
    ]
    assert options[0].source_kind == "layout_geometry"
    assert options[0].dimension_evidence_count == 1
    assert options[0].wall_segment_count == 0


def test_reconciliation_cycles_standard_size_options_for_asymmetric_features() -> None:
    from fortyk_los_backend.domain.terrain_reconciliation import (
        StandardTerrainFootprintOption,
        reconcile_terrain_layout,
    )

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-small",
                label="Small mistaken extraction",
                footprint=_rectangle(17.0, 17.0, 23.0, 20.0),
            ),
        )
    )

    report = reconcile_terrain_layout(
        layout,
        measurements=(
            *_corner_measurements(16.0, 26.0, 28.0, 34.0),
        ),
        standard_options=(
            StandardTerrainFootprintOption(
                option_id="footprint-size-12x08",
                width_inches=12.0,
                height_inches=8.0,
                count=1,
                dense_feature_count=0,
                wall_segment_count=0,
                feature_ids=("terrain-small",),
                template_ids=("terrain-footprint-p1-01",),
            ),
        ),
    )

    assert report.status == "passed_with_alternatives"
    assert report.final_measurement_status == "passed"
    assert report.final_symmetry_status == "passed"
    assert report.alternatives[0].option_id == "footprint-size-12x08"
    assert report.alternatives[0].proposed_bounds_inches == (16.0, 26.0, 28.0, 34.0)
    assert report.alternatives[0].review_reason == (
        "standard_option_satisfies_measurement_and_symmetry"
    )


def test_reconciliation_cycles_mirrored_partner_alternatives() -> None:
    from fortyk_los_backend.domain.terrain_reconciliation import (
        StandardTerrainFootprintOption,
        reconcile_terrain_layout,
    )

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-anchor",
                label="Anchor",
                footprint=_rectangle(2.0, 4.0, 6.0, 8.0),
                terrain_category=TerrainCategory.DENSE,
            ),
            TerrainFeature(
                feature_id="terrain-misplaced",
                label="Misplaced",
                footprint=_rectangle(20.0, 20.0, 24.0, 24.0),
                terrain_category=TerrainCategory.DENSE,
            ),
        )
    )

    report = reconcile_terrain_layout(
        layout,
        measurements=(
            *_corner_measurements(2.0, 4.0, 6.0, 8.0),
            *_corner_measurements(38.0, 52.0, 42.0, 56.0),
        ),
        standard_options=(
            StandardTerrainFootprintOption(
                option_id="source-footprint-size-04x04",
                width_inches=4.0,
                height_inches=4.0,
                count=2,
                dense_feature_count=2,
                wall_segment_count=0,
                feature_ids=("terrain-anchor", "terrain-misplaced"),
                template_ids=("template-a",),
                dimension_evidence_count=12,
                source_kind="source_catalog",
            ),
        ),
    )

    viable = [
        alternative
        for alternative in report.alternatives
        if alternative.status == "viable"
    ]
    assert report.status == "passed_with_alternatives"
    assert report.final_measurement_status == "passed"
    assert report.final_symmetry_status == "passed"
    assert report.unresolved_feature_ids == ()
    assert len(viable) == 1
    assert viable[0].alternative_kind == "mirror_partner:terrain-anchor"
    assert viable[0].proposed_bounds_inches == (38.0, 52.0, 42.0, 56.0)
    assert viable[0].review_reason == "mirror_partner_satisfies_measurement_and_symmetry"


def _corner_measurements(
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
) -> tuple[MeasurementAnnotation, ...]:
    board_width = 44.0
    board_height = 60.0
    left = x_min
    right = board_width - x_max
    bottom = y_min
    top = board_height - y_max
    return (
        MeasurementAnnotation(value=left, x=x_min, y=y_min),
        MeasurementAnnotation(value=bottom, x=x_min, y=y_min),
        MeasurementAnnotation(value=right, x=x_max, y=y_min),
        MeasurementAnnotation(value=bottom, x=x_max, y=y_min),
        MeasurementAnnotation(value=right, x=x_max, y=y_max),
        MeasurementAnnotation(value=top, x=x_max, y=y_max),
        MeasurementAnnotation(value=left, x=x_min, y=y_max),
        MeasurementAnnotation(value=top, x=x_min, y=y_max),
    )


def _layout_with_features(
    features: tuple[TerrainFeature, ...],
    *,
    blockers: tuple[Blocker, ...] = (),
) -> CanonicalLayout:
    return CanonicalLayout(
        layout_id="reconciliation-layout",
        name="Reconciliation Layout",
        board=Board(width=44.0, height=60.0),
        terrain_features=features,
        blockers=blockers,
        deployments=(),
        provenance=LayoutProvenance(
            source_document_id="synthetic",
            source_page=1,
            extraction_method="synthetic",
        ),
        validation_status=ValidationStatus.PASSED,
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
