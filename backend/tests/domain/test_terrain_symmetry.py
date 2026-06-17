from fortyk_los_backend.domain.models import (
    Board,
    CanonicalLayout,
    LayoutProvenance,
    Point,
    PolygonGeometry,
    TerrainFeature,
    ValidationStatus,
)


def test_terrain_symmetry_passes_for_rotationally_symmetric_features() -> None:
    from fortyk_los_backend.domain.terrain_symmetry import analyze_terrain_symmetry

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="A",
                footprint=_rectangle(2.0, 3.0, 6.0, 7.0),
            ),
            TerrainFeature(
                feature_id="terrain-02",
                label="B",
                footprint=_rectangle(38.0, 53.0, 42.0, 57.0),
            ),
        )
    )

    report = analyze_terrain_symmetry(layout)

    assert report.status == "passed"
    assert report.extraction_method == "terrain-symmetry-v1"
    assert report.symmetry_kind == "rotational_180"
    assert report.feature_count == 2
    assert report.matched_feature_count == 2
    assert report.unmatched_feature_ids == ()
    assert report.max_residual_inches == 0.0
    assert [(match.feature_id, match.mirrored_feature_id) for match in report.matches] == [
        ("terrain-01", "terrain-02"),
        ("terrain-02", "terrain-01"),
    ]


def test_terrain_symmetry_warns_for_asymmetric_features() -> None:
    from fortyk_los_backend.domain.terrain_symmetry import analyze_terrain_symmetry

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="A",
                footprint=_rectangle(2.0, 3.0, 6.0, 7.0),
            ),
            TerrainFeature(
                feature_id="terrain-02",
                label="B",
                footprint=_rectangle(22.0, 20.0, 30.0, 28.0),
            ),
        )
    )

    report = analyze_terrain_symmetry(layout)

    assert report.status == "warning"
    assert report.matched_feature_count == 0
    assert report.unmatched_feature_ids == ("terrain-01", "terrain-02")
    assert report.max_residual_inches is not None
    assert report.max_residual_inches > 1.0


def test_terrain_symmetry_requires_one_to_one_matching() -> None:
    from fortyk_los_backend.domain.terrain_symmetry import analyze_terrain_symmetry

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="A",
                footprint=_rectangle(2.0, 3.0, 6.0, 7.0),
            ),
            TerrainFeature(
                feature_id="terrain-02",
                label="B",
                footprint=_rectangle(38.0, 53.0, 42.0, 57.0),
            ),
            TerrainFeature(
                feature_id="terrain-03",
                label="Duplicate claimant",
                footprint=_rectangle(1.0, 3.0, 5.0, 7.0),
            ),
        )
    )

    report = analyze_terrain_symmetry(layout)

    assert report.status == "warning"
    assert report.matched_feature_count == 2
    assert report.unmatched_feature_ids == ("terrain-03",)


def test_terrain_symmetry_uses_global_maximum_matching_not_greedy_pairs() -> None:
    from fortyk_los_backend.domain.terrain_symmetry import analyze_terrain_symmetry

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-a",
                label="A",
                footprint=_rectangle(5.0, 5.0, 7.0, 7.0),
            ),
            TerrainFeature(
                feature_id="terrain-b",
                label="B",
                footprint=_rectangle(37.0, 53.0, 39.0, 55.0),
            ),
            TerrainFeature(
                feature_id="terrain-c",
                label="C",
                footprint=_rectangle(38.2, 53.0, 40.2, 55.0),
            ),
            TerrainFeature(
                feature_id="terrain-d",
                label="D",
                footprint=_rectangle(6.2, 5.0, 8.2, 7.0),
            ),
        )
    )

    report = analyze_terrain_symmetry(layout)

    assert report.status == "passed"
    assert report.matched_feature_count == 4
    assert report.unmatched_feature_ids == ()
    matches = {match.feature_id: match.mirrored_feature_id for match in report.matches}
    assert matches == {
        "terrain-a": "terrain-c",
        "terrain-b": "terrain-d",
        "terrain-c": "terrain-a",
        "terrain-d": "terrain-b",
    }


def _layout_with_features(features: tuple[TerrainFeature, ...]) -> CanonicalLayout:
    return CanonicalLayout(
        layout_id="symmetry-layout",
        name="Symmetry Layout",
        board=Board(width=44.0, height=60.0),
        terrain_features=features,
        blockers=(),
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
