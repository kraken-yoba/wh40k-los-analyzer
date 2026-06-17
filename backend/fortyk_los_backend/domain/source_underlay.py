from pathlib import Path

import cv2
import fitz
import numpy as np

from fortyk_los_backend.domain.extraction import _find_board_rect

UNDERLAY_WIDTH_PX = 880
UNDERLAY_HEIGHT_PX = 1200


def render_event_companion_board_underlay(
    pdf_path: Path,
    *,
    page_number: int,
    width_px: int = UNDERLAY_WIDTH_PX,
    height_px: int = UNDERLAY_HEIGHT_PX,
) -> bytes:
    with fitz.open(pdf_path) as document:
        page = document[page_number - 1]
        board_rect = _find_board_rect(list(page.get_drawings()))
        clip = fitz.Rect(board_rect.x0, board_rect.y0, board_rect.x1, board_rect.y1)
        matrix = fitz.Matrix(width_px / board_rect.width, height_px / board_rect.height)
        pixmap = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
    if pixmap.width == width_px and pixmap.height == height_px:
        return bytes(pixmap.tobytes("png"))
    return _resize_pixmap_to_png(pixmap, width_px=width_px, height_px=height_px)


def _resize_pixmap_to_png(pixmap: fitz.Pixmap, *, width_px: int, height_px: int) -> bytes:
    raster = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
        pixmap.height,
        pixmap.width,
        pixmap.n,
    )[:, :, :3]
    resized = cv2.resize(raster, (width_px, height_px), interpolation=cv2.INTER_AREA)
    encoded, png = cv2.imencode(".png", cv2.cvtColor(resized, cv2.COLOR_RGB2BGR))
    if not encoded:
        raise ValueError("Could not encode source underlay PNG")
    return bytes(png.tobytes())
