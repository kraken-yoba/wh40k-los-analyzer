import pytest
from fortyk_los_backend.domain.los import (
    BaseProfile,
    LineOfSightRequest,
    compute_base_aware_los,
    compute_point_los,
    is_legal_base_center,
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


def _layout_with_blockers(blockers: tuple[Blocker, ...]) -> CanonicalLayout:
    return CanonicalLayout(
        layout_id="los-fixture",
        name="LOS Fixture",
        board=Board(width=20.0, height=20.0),
        terrain_features=(
            TerrainFeature(
                feature_id="ruin-a",
                label="Ruin A",
                footprint=_rectangle(8.0, 0.0, 12.0, 20.0),
            ),
            TerrainFeature(
                feature_id="blocking-crater",
                label="Blocking Crater",
                footprint=_rectangle(1.0, 12.0, 3.0, 14.0),
                movement_blocking=True,
            ),
        ),
        blockers=blockers,
        deployments=(
            DeploymentZone(
                zone_id="source-zone",
                label="Source Zone",
                area=_rectangle(0.0, 0.0, 6.0, 20.0),
            ),
        ),
        provenance=LayoutProvenance(
            source_document_id="synthetic",
            source_page=1,
            extraction_method="synthetic-fixture",
        ),
        validation_status=ValidationStatus.PASSED,
    )


def _wall(blocker_id: str, start: Point, end: Point) -> Blocker:
    return Blocker(
        blocker_id=blocker_id,
        feature_id="ruin-a",
        kind=BlockerKind.WALL,
        start=start,
        end=end,
    )


def test_point_los_is_visible_when_no_blocker_intersects_segment() -> None:
    layout = _layout_with_blockers(
        (
            _wall("north-wall", Point(x=8.0, y=15.0), Point(x=12.0, y=15.0)),
        )
    )

    result = compute_point_los(
        layout,
        LineOfSightRequest(source=Point(x=2.0, y=2.0), target=Point(x=18.0, y=2.0)),
    )

    assert result.visible is True
    assert result.blocking_blocker_ids == ()


def test_point_los_is_blocked_by_crossing_wall() -> None:
    layout = _layout_with_blockers(
        (
            _wall("mid-wall", Point(x=10.0, y=0.0), Point(x=10.0, y=20.0)),
        )
    )

    result = compute_point_los(
        layout,
        LineOfSightRequest(source=Point(x=2.0, y=10.0), target=Point(x=18.0, y=10.0)),
    )

    assert result.visible is False
    assert result.blocking_blocker_ids == ("mid-wall",)


def test_point_los_blocks_tangent_contact_with_wall_endpoint() -> None:
    layout = _layout_with_blockers(
        (
            _wall("endpoint-wall", Point(x=10.0, y=10.0), Point(x=10.0, y=20.0)),
        )
    )

    result = compute_point_los(
        layout,
        LineOfSightRequest(source=Point(x=2.0, y=2.0), target=Point(x=18.0, y=18.0)),
    )

    assert result.visible is True
    assert result.blocking_blocker_ids == ()


def test_point_los_blocks_sealed_endpoint_contact() -> None:
    layout = _layout_with_blockers(
        (
            Blocker(
                blocker_id="sealed-endpoint-wall",
                feature_id="ruin-a",
                kind=BlockerKind.WALL,
                start=Point(x=10.0, y=10.0),
                end=Point(x=10.0, y=20.0),
                sealed_start=True,
            ),
        )
    )

    result = compute_point_los(
        layout,
        LineOfSightRequest(source=Point(x=2.0, y=2.0), target=Point(x=18.0, y=18.0)),
    )

    assert result.visible is False
    assert result.blocking_blocker_ids == ("sealed-endpoint-wall",)


def test_point_los_allows_contact_at_source_or_target_only() -> None:
    layout = _layout_with_blockers(
        (
            _wall("source-touch", Point(x=8.0, y=8.0), Point(x=8.0, y=12.0)),
        )
    )

    result = compute_point_los(
        layout,
        LineOfSightRequest(source=Point(x=8.0, y=8.0), target=Point(x=18.0, y=8.0)),
    )

    assert result.visible is True


def test_point_los_blocks_collinear_overlap() -> None:
    layout = _layout_with_blockers(
        (
            _wall("overlap-wall", Point(x=8.0, y=8.0), Point(x=12.0, y=8.0)),
        )
    )

    result = compute_point_los(
        layout,
        LineOfSightRequest(source=Point(x=2.0, y=8.0), target=Point(x=18.0, y=8.0)),
    )

    assert result.visible is False
    assert result.blocking_blocker_ids == ("overlap-wall",)


def test_point_los_rejects_source_outside_board() -> None:
    layout = _layout_with_blockers(())

    with pytest.raises(ValueError, match="source is outside board"):
        compute_point_los(
            layout,
            LineOfSightRequest(source=Point(x=-1.0, y=8.0), target=Point(x=18.0, y=8.0)),
        )


def test_base_center_legality_respects_board_and_movement_blocking_terrain() -> None:
    layout = _layout_with_blockers(())
    base = BaseProfile(diameter=2.0)

    assert is_legal_base_center(layout, Point(x=2.0, y=2.0), base) is True
    assert is_legal_base_center(layout, Point(x=0.5, y=2.0), base) is False
    assert is_legal_base_center(layout, Point(x=9.0, y=10.0), base) is True
    assert is_legal_base_center(layout, Point(x=2.0, y=13.0), base) is False


def test_base_aware_los_reports_sampling_metadata() -> None:
    layout = _layout_with_blockers(
        (
            _wall("mid-wall", Point(x=10.0, y=0.0), Point(x=10.0, y=8.0)),
        )
    )

    result = compute_base_aware_los(
        layout,
        LineOfSightRequest(source=Point(x=4.0, y=10.0), target=Point(x=16.0, y=10.0)),
        source_base=BaseProfile(diameter=2.0, boundary_sample_count=16),
        target_base=BaseProfile(diameter=2.0, boundary_sample_count=16),
    )

    assert result.visible is True
    assert result.sample_count == 289
    assert result.boundary_sample_count == 16
    assert result.method == "disk-sample-v1"


def test_base_profile_rejects_invalid_sampling_contract() -> None:
    with pytest.raises(ValueError):
        BaseProfile(diameter=float("inf"))

    with pytest.raises(ValueError):
        BaseProfile(diameter=1.0, boundary_sample_count=7)
