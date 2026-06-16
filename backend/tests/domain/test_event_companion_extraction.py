from hashlib import sha256
from pathlib import Path

import fitz
import pytest
from fortyk_los_backend.domain.extraction import extract_event_companion_layout
from fortyk_los_backend.domain.models import CanonicalLayout, ValidationStatus

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
    record_codes = {record.code for record in layout.validation_records}
    assert "placement_proxy_not_los_ready" in record_codes
    assert "terrain_measurement_crosscheck_pending" in record_codes

    deployments = {deployment.zone_id: deployment for deployment in layout.deployments}
    attacker_y_values = [point.y for point in deployments["attacker"].area.points]
    defender_y_values = [point.y for point in deployments["defender"].area.points]
    assert min(attacker_y_values) == pytest.approx(40.0)
    assert max(attacker_y_values) == pytest.approx(60.0)
    assert min(defender_y_values) == pytest.approx(0.0)
    assert max(defender_y_values) == pytest.approx(20.0)


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
    assert len(layout.terrain_features) == 16
    assert layout.blockers == ()
    assert _bounds_by_zone(layout) == {
        "attacker": pytest.approx((0.0, 40.02, 44.0, 59.95), abs=0.01),
        "defender": pytest.approx((0.0, 0.0, 44.0, 19.91), abs=0.01),
    }
    assert _rounded_feature_summaries(layout) == [
        ("terrain-01", "CD", (13.97, 42.48, 21.62, 54.12)),
        ("terrain-02", "Terrain 02", (26.33, 47.13, 32.94, 51.51)),
        ("terrain-03", "EF/GH", (32.4, 35.38, 40.05, 47.02)),
        ("terrain-04", "Terrain 04", (2.02, 42.84, 12.05, 46.61)),
        ("terrain-05", "Terrain 05", (21.04, 39.99, 27.09, 42.78)),
        ("terrain-06", "Terrain 06", (8.13, 31.98, 12.5, 38.61)),
        ("terrain-07", "AB", (15.78, 26.89, 27.8, 35.02)),
        ("terrain-08", "AB", (16.21, 24.89, 28.22, 33.02)),
        ("terrain-09", "Terrain 09", (4.02, 29.45, 10.07, 32.25)),
        ("terrain-10", "Terrain 10", (33.94, 27.72, 39.99, 30.51)),
        ("terrain-11", "Terrain 11", (31.51, 21.35, 35.88, 27.99)),
        ("terrain-12", "EF/GH", (3.94, 12.9, 11.59, 24.53)),
        ("terrain-13", "Terrain 13", (16.97, 17.18, 23.02, 19.98)),
        ("terrain-14", "CD", (22.4, 5.83, 30.05, 17.46)),
        ("terrain-15", "Terrain 15", (31.91, 13.26, 41.94, 17.03)),
        ("terrain-16", "Terrain 16", (10.99, 8.5, 17.6, 12.88)),
    ]
    record_codes = {record.code for record in layout.validation_records}
    assert {
        "deployment_depth_measurement_crosscheck",
        "placement_proxy_not_los_ready",
        "terrain_label_review_required",
        "terrain_measurement_crosscheck_pending",
    }.issubset(record_codes)


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


def _write_synthetic_event_layout_pdf(pdf_path: Path) -> None:
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
        fitz.Rect(220, 260, 270, 310),
        color=(0.137, 0.122, 0.125),
        fill=(0.820, 0.826, 0.832),
        width=0.3,
    )
    page.insert_text((158, 185), "AB")
    page.insert_text((238, 285), "CD")
    document.save(pdf_path)
