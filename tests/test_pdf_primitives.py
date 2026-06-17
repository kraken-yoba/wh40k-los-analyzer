from __future__ import annotations

from pathlib import Path

import fitz

from warhammer_companion.ingestion.pdf import (
    RenderedPage,
    page_text,
    pdf_page_count,
    render_pdf_page,
)


def _write_pdf(path: Path) -> None:
    document = fitz.open()
    try:
        first_page = document.new_page(width=144, height=72)
        first_page.insert_text((12, 24), "Alpha layout")
        first_page.draw_rect(
            fitz.Rect(0, 0, 144, 72),
            color=(1.0, 0.0, 0.0),
            fill=(1.0, 0.0, 0.0),
        )
        second_page = document.new_page(width=72, height=144)
        second_page.insert_text((12, 24), "Beta layout")
        document.save(path)
    finally:
        document.close()


def test_pdf_page_count_reads_synthetic_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "synthetic.pdf"
    _write_pdf(pdf_path)

    assert pdf_page_count(pdf_path) == 2


def test_page_text_extracts_text_for_selected_page(tmp_path: Path) -> None:
    pdf_path = tmp_path / "synthetic.pdf"
    _write_pdf(pdf_path)

    assert "Beta layout" in page_text(pdf_path, page_index=1)


def test_render_pdf_page_returns_rgb_image_with_expected_scale(tmp_path: Path) -> None:
    pdf_path = tmp_path / "synthetic.pdf"
    _write_pdf(pdf_path)

    rendered = render_pdf_page(pdf_path, page_index=0, dpi=144)

    assert isinstance(rendered, RenderedPage)
    assert rendered.page_index == 0
    assert rendered.dpi == 144
    assert rendered.width_px == 288
    assert rendered.height_px == 144
    assert rendered.image.mode == "RGB"
    assert rendered.image.size == (288, 144)
