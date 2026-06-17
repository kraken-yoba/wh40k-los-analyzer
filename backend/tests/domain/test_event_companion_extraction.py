from hashlib import sha256
from pathlib import Path

import fitz
import pytest
from fortyk_los_backend.domain.extraction import extract_event_companion_layout
from fortyk_los_backend.domain.models import CanonicalLayout, TerrainCategory, ValidationStatus

REPO_ROOT = Path(__file__).resolve().parents[3]
OFFICIAL_EVENT_COMPANION = REPO_ROOT / "data" / "pdfs" / "event_companion.pdf"
OFFICIAL_EVENT_COMPANION_SHA256 = (
    "0e26f6586929e7ec4c50c6a17d240ed794bb7b6c654d1d9664fb908abc606a19"
)


def test_extract_event_companion_layout_from_synthetic_vector_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "synthetic-event-layout.pdf"
    _write_synthetic_event_layout_pdf(pdf_path)

    layout = extract_event_companion_layout(
        pdf_path,
        page_number=1,
        source_document_id="synthetic-event-companion",
    )

    assert layout.layout_id == "event-companion-page-1"
    assert layout.name == "Layout A"
    assert layout.board.width == 44.0
    assert layout.board.height == 60.0
    assert layout.provenance.extraction_method == "event-companion-vector-v1"
    assert layout.provenance.source_document_id == "synthetic-event-companion"
    assert layout.validation_status == ValidationStatus.WARNING
    assert len(layout.terrain_features) == 2
    assert {feature.label for feature in layout.terrain_features} == {"AB", "CD"}
    assert layout.blockers == ()
    assert {
        feature.label: feature.terrain_category for feature in layout.terrain_features
    } == {
        "AB": TerrainCategory.DENSE,
        "CD": TerrainCategory.LIGHT,
    }
    assert _all_footprint_corners_are_on_inch_grid(layout)
    record_codes = {record.code for record in layout.validation_records}
    assert "terrain_footprint_grid_snap_verified" in record_codes

    deployments = {deployment.zone_id: deployment for deployment in layout.deployments}
    attacker_y_values = [point.y for point in deployments["attacker"].area.points]
    defender_y_values = [point.y for point in deployments["defender"].area.points]
    assert min(attacker_y_values) == pytest.approx(40.0)
    assert max(attacker_y_values) == pytest.approx(60.0)
    assert min(defender_y_values) == pytest.approx(0.0)
    assert max(defender_y_values) == pytest.approx(20.0)


def test_extract_event_companion_layout_prefers_dense_when_markers_overlap(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "synthetic-event-layout-conflicting-category.pdf"
    _write_synthetic_event_layout_pdf(pdf_path, conflict_first_feature_category=True)

    layout = extract_event_companion_layout(
        pdf_path,
        page_number=1,
        source_document_id="synthetic-event-companion",
    )

    categories_by_label = {
        feature.label: feature.terrain_category for feature in layout.terrain_features
    }
    assert categories_by_label["AB"] == TerrainCategory.DENSE
    assert categories_by_label["CD"] == TerrainCategory.LIGHT


def test_extract_event_companion_layout_removes_overlapping_duplicate_candidates(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "synthetic-event-layout-overlap.pdf"
    _write_synthetic_event_layout_pdf(pdf_path, include_overlapping_duplicate=True)

    layout = extract_event_companion_layout(
        pdf_path,
        page_number=1,
        source_document_id="synthetic-event-companion",
    )

    assert len(layout.terrain_features) == 2
    assert _all_footprint_corners_are_on_inch_grid(layout)
    assert _overlapping_footprint_pairs(layout) == []
    record_by_code = {record.code: record for record in layout.validation_records}
    assert record_by_code["terrain_footprint_grid_snap_verified"].severity == "info"
    assert "terrain_footprint_overlap_duplicate_removed" in record_by_code


def test_extract_event_companion_layout_flags_unmatched_printed_measurements(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "synthetic-event-layout-bogus-measurement.pdf"
    _write_synthetic_event_layout_pdf(pdf_path, terrain_measurement_annotation='99"')

    layout = extract_event_companion_layout(
        pdf_path,
        page_number=1,
        source_document_id="synthetic-event-companion",
    )

    record_by_code = {record.code: record for record in layout.validation_records}
    assert "terrain_measurement_crosscheck" not in record_by_code
    assert record_by_code["terrain_measurement_crosscheck_failed"].severity == "warning"
    assert record_by_code["terrain_measurement_crosscheck_failed"].review_status == "unreviewed"


def test_extract_event_companion_layout_flags_high_snap_residual_without_measurements(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "synthetic-event-layout-off-grid.pdf"
    _write_synthetic_event_layout_pdf(pdf_path, off_grid_first_feature=True)

    layout = extract_event_companion_layout(
        pdf_path,
        page_number=1,
        source_document_id="synthetic-event-companion",
    )

    record_by_code = {record.code: record for record in layout.validation_records}
    assert "terrain_footprint_grid_snap_verified" not in record_by_code
    assert record_by_code["terrain_footprint_grid_snap_review_required"].severity == "warning"
    assert record_by_code["terrain_footprint_grid_snap_review_required"].review_status == (
        "unreviewed"
    )


@pytest.mark.skipif(
    not OFFICIAL_EVENT_COMPANION.exists(),
    reason="official Event Companion PDF is kept in the local gitignored cache",
)
def test_extract_event_companion_layout_from_cached_official_page_9() -> None:
    assert sha256(OFFICIAL_EVENT_COMPANION.read_bytes()).hexdigest() == (
        OFFICIAL_EVENT_COMPANION_SHA256
    )

    layout = extract_event_companion_layout(OFFICIAL_EVENT_COMPANION, page_number=9)

    assert layout.name == "Layout A"
    assert layout.provenance.source_document_id == "event-companion-2026-06-12"
    assert layout.provenance.source_page == 9
    assert len(layout.deployments) == 2
    assert len(layout.terrain_features) == 14
    assert layout.blockers == ()
    assert _all_footprint_corners_are_on_inch_grid(layout)
    assert _overlapping_footprint_pairs(layout) == []
    categories_by_id = {
        feature.feature_id: feature.terrain_category for feature in layout.terrain_features
    }
    assert {
        feature_id
        for feature_id, category in categories_by_id.items()
        if category == TerrainCategory.DENSE
    } == {"terrain-01", "terrain-03", "terrain-06", "terrain-10", "terrain-12"}
    assert any(category == TerrainCategory.UNKNOWN for category in categories_by_id.values())
    assert _bounds_by_zone(layout) == {
        "attacker": pytest.approx((0.0, 40.02, 44.0, 59.95), abs=0.01),
        "defender": pytest.approx((0.0, 0.0, 44.0, 19.91), abs=0.01),
    }
    assert _rounded_feature_summaries(layout) == [
        ("terrain-01", "CD", (14.0, 42.0, 22.0, 54.0)),
        ("terrain-02", "Terrain 02", (26.0, 47.0, 33.0, 52.0)),
        ("terrain-03", "EF/GH", (32.0, 35.0, 40.0, 47.0)),
        ("terrain-04", "Terrain 04", (2.0, 43.0, 12.0, 47.0)),
        ("terrain-05", "Terrain 05", (8.0, 32.0, 13.0, 39.0)),
        ("terrain-06", "AB", (16.0, 27.0, 28.0, 35.0)),
        ("terrain-07", "Terrain 07", (4.0, 29.0, 10.0, 32.0)),
        ("terrain-08", "Terrain 08", (34.0, 28.0, 40.0, 31.0)),
        ("terrain-09", "Terrain 09", (32.0, 21.0, 36.0, 28.0)),
        ("terrain-10", "EF/GH", (4.0, 13.0, 12.0, 25.0)),
        ("terrain-11", "Terrain 11", (17.0, 17.0, 23.0, 20.0)),
        ("terrain-12", "CD", (22.0, 6.0, 30.0, 17.0)),
        ("terrain-13", "Terrain 13", (32.0, 13.0, 42.0, 17.0)),
        ("terrain-14", "Terrain 14", (11.0, 8.0, 18.0, 13.0)),
    ]
    record_codes = {record.code for record in layout.validation_records}
    assert {
        "deployment_depth_measurement_crosscheck",
        "terrain_footprint_grid_snap_verified",
        "terrain_footprint_overlap_duplicate_removed",
        "terrain_label_review_required",
    }.issubset(record_codes)
    record_by_code = {record.code: record for record in layout.validation_records}
    assert "12/14 features" in record_by_code["terrain_measurement_crosscheck"].message
    assert "8 with two or more" in record_by_code["terrain_measurement_crosscheck"].message
    assert "placement_proxy_not_los_ready" not in record_codes
    assert "terrain_measurement_crosscheck_pending" not in record_codes


def _bounds_by_zone(layout: CanonicalLayout) -> dict[str, tuple[float, float, float, float]]:
    bounds = {}
    for deployment in layout.deployments:
        xs = [point.x for point in deployment.area.points]
        ys = [point.y for point in deployment.area.points]
        bounds[deployment.zone_id] = (min(xs), min(ys), max(xs), max(ys))
    return bounds


def _rounded_feature_summaries(
    layout: CanonicalLayout,
) -> list[tuple[str, str, tuple[float, float, float, float]]]:
    summaries = []
    for feature in layout.terrain_features:
        xs = [point.x for point in feature.footprint.points]
        ys = [point.y for point in feature.footprint.points]
        summaries.append(
            (
                feature.feature_id,
                feature.label,
                (round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)),
            )
        )
    return summaries


def _all_footprint_corners_are_on_inch_grid(layout: CanonicalLayout) -> bool:
    return all(
        coordinate == pytest.approx(round(coordinate))
        for feature in layout.terrain_features
        for point in feature.footprint.points
        for coordinate in (point.x, point.y)
    )


def _overlapping_footprint_pairs(layout: CanonicalLayout) -> list[tuple[str, str]]:
    overlaps: list[tuple[str, str]] = []
    features = list(layout.terrain_features)
    for first_index, first_feature in enumerate(features):
        first_polygon = first_feature.footprint.to_shapely()
        for second_feature in features[first_index + 1 :]:
            if first_polygon.intersection(second_feature.footprint.to_shapely()).area > 1e-6:
                overlaps.append((first_feature.feature_id, second_feature.feature_id))
    return overlaps


def _write_synthetic_event_layout_pdf(
    pdf_path: Path,
    *,
    conflict_first_feature_category: bool = False,
    include_overlapping_duplicate: bool = False,
    off_grid_first_feature: bool = False,
    terrain_measurement_annotation: str | None = None,
) -> None:
    document = fitz.open()
    page = document.new_page(width=500, height=700)
    board = fitz.Rect(100, 100, 320, 400)
    page.insert_text((220, 80), "LAYOUT A")
    page.draw_rect(board, color=(0.137, 0.122, 0.125), width=2.4)
    page.draw_rect(fitz.Rect(100, 100, 320, 200), color=None, fill=(0.618, 0.040, 0.056))
    page.draw_rect(fitz.Rect(100, 300, 320, 400), color=None, fill=(0.000, 0.241, 0.408))
    first_feature_rect = (
        fitz.Rect(142, 158, 192, 208)
        if off_grid_first_feature
        else fitz.Rect(140, 160, 190, 210)
    )
    page.draw_rect(
        first_feature_rect,
        color=(0.137, 0.122, 0.125),
        fill=(0.820, 0.826, 0.832),
        width=0.3,
    )
    if include_overlapping_duplicate:
        page.draw_rect(
            fitz.Rect(160, 180, 210, 230),
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
    if conflict_first_feature_category:
        page.draw_rect(
            fitz.Rect(164, 190, 176, 202),
            color=None,
            fill=(0.687, 0.253, 0.171),
        )
    page.draw_rect(
        fitz.Rect(220, 260, 270, 310),
        color=(0.137, 0.122, 0.125),
        fill=(0.820, 0.826, 0.832),
        width=0.3,
    )
    page.draw_rect(
        fitz.Rect(230, 270, 242, 282),
        color=None,
        fill=(0.687, 0.253, 0.171),
    )
    if terrain_measurement_annotation is not None:
        page.insert_text((25, 80), terrain_measurement_annotation)
    page.insert_text((158, 185), "AB")
    page.insert_text((238, 285), "CD")
    document.save(pdf_path)
