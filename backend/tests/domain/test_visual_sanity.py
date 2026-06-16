from pathlib import Path

import fitz
from fortyk_los_backend.domain.models import CanonicalLayout
from fortyk_los_backend.domain.visual_sanity import run_event_companion_visual_sanity


def test_event_companion_visual_sanity_passes_for_matching_synthetic_layout(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "synthetic-event-layout.pdf"
    _write_synthetic_event_layout_pdf(pdf_path)

    report = run_event_companion_visual_sanity(pdf_path, page_number=1)

    checks_by_code = {check.code: check for check in report.checks}
    assert report.status == "passed"
    assert report.extraction_method == "event-companion-cv-sanity-v1"
    assert report.vision_advisory["status"] == "not_run"
    assert checks_by_code["board_raster_alignment"].status == "passed"
    assert checks_by_code["deployment_raster_alignment"].match_count == 2
    assert checks_by_code["terrain_raster_alignment"].match_count == 2
    terrain_residual = checks_by_code["terrain_raster_alignment"].max_residual_inches
    assert terrain_residual is not None
    assert terrain_residual <= 0.25


def test_event_companion_visual_sanity_warns_on_shifted_layout_geometry(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "synthetic-event-layout.pdf"
    _write_synthetic_event_layout_pdf(pdf_path)
    baseline = run_event_companion_visual_sanity(pdf_path, page_number=1).layout
    payload = baseline.model_dump(mode="json")
    payload["terrain_features"][0]["footprint"]["points"] = [
        {"x": point["x"] + 5.0, "y": point["y"]}
        for point in payload["terrain_features"][0]["footprint"]["points"]
    ]
    shifted_layout = CanonicalLayout.model_validate(payload)

    report = run_event_companion_visual_sanity(
        pdf_path,
        page_number=1,
        layout=shifted_layout,
    )

    terrain_check = {check.code: check for check in report.checks}["terrain_raster_alignment"]
    assert report.status == "warning"
    assert terrain_check.status == "warning"
    assert terrain_check.max_residual_inches is not None
    assert terrain_check.max_residual_inches > 1.0


def test_event_companion_visual_sanity_records_missing_raster_shape(
    tmp_path: Path,
) -> None:
    full_pdf_path = tmp_path / "synthetic-event-layout.pdf"
    pdf_path = tmp_path / "synthetic-event-layout-missing-terrain.pdf"
    _write_synthetic_event_layout_pdf(full_pdf_path)
    _write_single_terrain_event_layout_pdf(pdf_path)
    two_terrain_layout = run_event_companion_visual_sanity(full_pdf_path, page_number=1).layout

    report = run_event_companion_visual_sanity(
        pdf_path,
        page_number=1,
        layout=two_terrain_layout,
    )

    terrain_check = {check.code: check for check in report.checks}["terrain_raster_alignment"]
    assert report.status == "warning"
    assert terrain_check.status == "warning"
    assert terrain_check.expected_count == 2
    assert terrain_check.observed_count == 1


def _write_single_terrain_event_layout_pdf(pdf_path: Path) -> None:
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
    page.insert_text((158, 185), "AB")
    document.save(pdf_path)


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
        fitz.Rect(150, 190, 162, 202),
        color=(1.0, 1.0, 1.0),
        fill=(0.000, 0.452, 0.378),
        width=0.2,
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
    page.insert_text((158, 185), "AB")
    page.insert_text((238, 285), "CD")
    document.save(pdf_path)
