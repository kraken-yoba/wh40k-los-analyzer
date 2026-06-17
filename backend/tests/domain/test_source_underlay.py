from pathlib import Path

import fitz
from fortyk_los_backend.domain.source_underlay import render_event_companion_board_underlay


def test_event_companion_board_underlay_has_exact_requested_dimensions(tmp_path: Path) -> None:
    pdf_path = tmp_path / "event-layout.pdf"
    _write_non_integer_board_pdf(pdf_path)

    png = render_event_companion_board_underlay(
        pdf_path,
        page_number=1,
        width_px=880,
        height_px=1200,
    )

    image = fitz.Pixmap(png)
    assert image.width == 880
    assert image.height == 1200


def _write_non_integer_board_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=800, height=1000)
    board_width = 219.7
    board_height = board_width / (44.0 / 60.0)
    board = fitz.Rect(50.25, 60.5, 50.25 + board_width, 60.5 + board_height)
    page.draw_rect(board, color=(0.137, 0.122, 0.125), width=2.4)
    document.save(pdf_path)
