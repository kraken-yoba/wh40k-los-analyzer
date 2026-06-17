from hashlib import sha256
from pathlib import Path

import fitz
import pytest
from fortyk_los_backend.domain.models import (
    Board,
    CanonicalLayout,
    LayoutProvenance,
    Point,
    PolygonGeometry,
    TerrainFeature,
    ValidationStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
OFFICIAL_EVENT_COMPANION = REPO_ROOT / "data" / "pdfs" / "event_companion.pdf"
OFFICIAL_EVENT_COMPANION_SHA256 = (
    "0e26f6586929e7ec4c50c6a17d240ed794bb7b6c654d1d9664fb908abc606a19"
)


def test_terrain_footprint_normalization_matches_raster_elements_to_size_options(
    tmp_path: Path,
) -> None:
    from fortyk_los_backend.domain.footprint_normalization import (
        run_terrain_footprint_normalization,
    )

    pdf_path = tmp_path / "synthetic-event-layout.pdf"
    _write_two_size_event_layout_pdf(pdf_path)

    report = run_terrain_footprint_normalization(pdf_path, page_number=1)

    assert report.status == "passed"
    assert report.extraction_method == "terrain-footprint-normalization-v1"
    option_dimensions = [
        (option.width_inches, option.height_inches, option.count) for option in report.options
    ]
    assert option_dimensions == [
        (10.0, 10.0, 1),
        (12.0, 8.0, 1),
    ]
    assert len(report.detected_elements) == 2
    assert [element.feature_id for element in report.detected_elements] == [
        "terrain-01",
        "terrain-02",
    ]
    assert [
        (match.feature_id, match.element_id, match.option_id, match.rotation_degrees, match.status)
        for match in report.matches
    ] == [
        ("terrain-01", "terrain-image-01", "footprint-size-10x10", 0, "matched"),
        ("terrain-02", "terrain-image-02", "footprint-size-12x08", 0, "matched"),
    ]
    assert min(match.score for match in report.matches) > 0.95


def test_footprint_size_options_canonicalize_rotated_dimensions() -> None:
    from fortyk_los_backend.domain.footprint_normalization import (
        footprint_size_options_from_layout,
    )

    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="A",
                footprint=_rectangle(0.0, 0.0, 8.0, 12.0),
            ),
            TerrainFeature(
                feature_id="terrain-02",
                label="B",
                footprint=_rectangle(16.0, 0.0, 28.0, 8.0),
            ),
        )
    )

    options = footprint_size_options_from_layout(layout)

    assert len(options) == 1
    assert options[0].option_id == "footprint-size-12x08"
    assert options[0].width_inches == 12.0
    assert options[0].height_inches == 8.0
    assert options[0].count == 2
    assert options[0].feature_ids == ("terrain-01", "terrain-02")


def test_terrain_footprint_normalization_allows_rotated_size_matches(
    tmp_path: Path,
) -> None:
    from fortyk_los_backend.domain.footprint_normalization import (
        FootprintSizeOption,
        match_detected_footprints_to_options,
    )

    options = (
        FootprintSizeOption(
            option_id="footprint-size-12x08",
            width_inches=12.0,
            height_inches=8.0,
            count=1,
            feature_ids=("terrain-01",),
        ),
    )
    detections = (
        {
            "element_id": "terrain-image-01",
            "feature_id": "terrain-rotated",
            "bounds_inches": (4.0, 8.0, 12.0, 20.0),
            "width_inches": 8.0,
            "height_inches": 12.0,
        },
    )

    matches = match_detected_footprints_to_options(detections, options)

    assert len(matches) == 1
    assert matches[0].feature_id == "terrain-rotated"
    assert matches[0].option_id == "footprint-size-12x08"
    assert matches[0].rotation_degrees == 90
    assert matches[0].status == "matched"
    assert matches[0].dimension_delta_inches == 0.0


def test_footprint_normalization_reports_tolerance_failures_before_ambiguity() -> None:
    from fortyk_los_backend.domain.footprint_normalization import (
        FootprintSizeOption,
        match_detected_footprints_to_options,
    )

    options = (
        FootprintSizeOption(
            option_id="footprint-size-12x08",
            width_inches=12.0,
            height_inches=8.0,
            count=1,
            feature_ids=("terrain-01",),
        ),
        FootprintSizeOption(
            option_id="footprint-size-12x09",
            width_inches=12.0,
            height_inches=9.0,
            count=1,
            feature_ids=("terrain-02",),
        ),
    )
    detections = (
        {
            "element_id": "terrain-image-01",
            "feature_id": "terrain-large",
            "bounds_inches": (0.0, 0.0, 16.0, 12.0),
            "width_inches": 16.0,
            "height_inches": 12.0,
        },
    )

    [match] = match_detected_footprints_to_options(detections, options)

    assert match.status == "needs_review"
    assert match.review_reason == "dimension_delta_exceeds_tolerance"


def test_terrain_footprint_normalization_ignores_gray_context_outside_feature_windows(
    tmp_path: Path,
) -> None:
    from fortyk_los_backend.domain.footprint_normalization import (
        run_terrain_footprint_normalization,
    )

    pdf_path = tmp_path / "synthetic-event-layout-context.pdf"
    _write_event_layout_pdf_with_gray_context(pdf_path)

    report = run_terrain_footprint_normalization(pdf_path, page_number=1)

    assert report.status == "passed"
    assert len(report.options) == 2
    assert len(report.detected_elements) == 2
    assert len(report.matches) == 2
    assert not report.warning_codes


@pytest.mark.skipif(
    not OFFICIAL_EVENT_COMPANION.exists(),
    reason="official Event Companion PDF is kept in the local gitignored cache",
)
def test_terrain_footprint_normalization_from_cached_official_page_9() -> None:
    from fortyk_los_backend.domain.footprint_normalization import (
        run_terrain_footprint_normalization,
    )

    assert sha256(OFFICIAL_EVENT_COMPANION.read_bytes()).hexdigest() == (
        OFFICIAL_EVENT_COMPANION_SHA256
    )

    report = run_terrain_footprint_normalization(OFFICIAL_EVENT_COMPANION, page_number=9)

    assert report.source_document_id == "event-companion-2026-06-12"
    assert report.layout_id == "event-companion-page-9"
    assert report.status == "warning"
    assert [(option.option_id, option.count, option.feature_ids) for option in report.options] == [
        ("footprint-size-06x03", 3, ("terrain-07", "terrain-08", "terrain-11")),
        ("footprint-size-07x04", 1, ("terrain-09",)),
        ("footprint-size-07x05", 3, ("terrain-02", "terrain-05", "terrain-14")),
        ("footprint-size-10x04", 2, ("terrain-04", "terrain-13")),
        ("footprint-size-11x08", 1, ("terrain-12",)),
        ("footprint-size-12x08", 4, ("terrain-01", "terrain-03", "terrain-06", "terrain-10")),
    ]
    assert len(report.detected_elements) == 14
    assert len(report.matches) == 14
    assert [element.feature_id for element in report.detected_elements[:3]] == [
        "terrain-01",
        "terrain-02",
        "terrain-03",
    ]
    assert report.warning_codes == ("terrain_footprint_normalization_match_review_required",)


def _write_two_size_event_layout_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=500, height=700)
    board = fitz.Rect(100, 100, 320, 400)
    page.insert_text((220, 80), "LAYOUT A")
    page.draw_rect(board, color=(0.137, 0.122, 0.125), width=2.4)
    page.draw_rect(fitz.Rect(100, 100, 320, 200), color=None, fill=(0.618, 0.040, 0.056))
    page.draw_rect(fitz.Rect(100, 300, 320, 400), color=None, fill=(0.000, 0.241, 0.408))
    page.draw_rect(
        fitz.Rect(140, 160, 190, 210),
        color=(0.137, 0.122, 0.125),
        fill=(0.820, 0.826, 0.832),
        width=0.3,
    )
    page.draw_rect(
        fitz.Rect(150, 190, 162, 202),
        color=(1.0, 1.0, 1.0),
        fill=(0.000, 0.452, 0.378),
        width=0.2,
    )
    page.draw_rect(
        fitz.Rect(220, 260, 280, 300),
        color=(0.137, 0.122, 0.125),
        fill=(0.820, 0.826, 0.832),
        width=0.3,
    )
    page.draw_rect(
        fitz.Rect(230, 270, 242, 282),
        color=None,
        fill=(0.687, 0.253, 0.171),
    )
    page.insert_text((158, 185), "AB")
    page.insert_text((238, 285), "CD")
    document.save(pdf_path)


def _layout_with_features(features: tuple[TerrainFeature, ...]) -> CanonicalLayout:
    return CanonicalLayout(
        layout_id="normalization-layout",
        name="Normalization Layout",
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


def _write_event_layout_pdf_with_gray_context(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=500, height=700)
    board = fitz.Rect(100, 100, 320, 400)
    page.insert_text((220, 80), "LAYOUT A")
    page.draw_rect(board, color=(0.137, 0.122, 0.125), width=2.4)
    page.draw_rect(fitz.Rect(100, 100, 320, 200), color=None, fill=(0.618, 0.040, 0.056))
    page.draw_rect(fitz.Rect(100, 300, 320, 400), color=None, fill=(0.000, 0.241, 0.408))
    page.draw_rect(fitz.Rect(20, 120, 340, 150), color=None, fill=(0.820, 0.826, 0.832))
    page.draw_rect(
        fitz.Rect(140, 160, 190, 210),
        color=(0.137, 0.122, 0.125),
        fill=(0.820, 0.826, 0.832),
        width=0.3,
    )
    page.draw_rect(
        fitz.Rect(220, 260, 280, 300),
        color=(0.137, 0.122, 0.125),
        fill=(0.820, 0.826, 0.832),
        width=0.3,
    )
    page.insert_text((158, 185), "AB")
    page.insert_text((238, 285), "CD")
    document.save(pdf_path)
