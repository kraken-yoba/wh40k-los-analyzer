from pathlib import Path

import fitz
import pytest
from fortyk_los_backend.domain.extraction import extract_event_companion_layout
from fortyk_los_backend.domain.models import ValidationStatus

REPO_ROOT = Path(__file__).resolve().parents[3]
OFFICIAL_EVENT_COMPANION = REPO_ROOT / "data" / "pdfs" / "event_companion.pdf"


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
    assert len(layout.blockers) == 8

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
    layout = extract_event_companion_layout(OFFICIAL_EVENT_COMPANION, page_number=9)

    assert layout.name == "Layout A"
    assert layout.provenance.source_document_id == "event-companion-2026-06-12"
    assert layout.provenance.source_page == 9
    assert len(layout.deployments) == 2
    assert len(layout.terrain_features) >= 10
    assert len(layout.blockers) == len(layout.terrain_features) * 4
    assert any(
        record.code == "footprint_perimeter_los_proxy" for record in layout.validation_records
    )


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
