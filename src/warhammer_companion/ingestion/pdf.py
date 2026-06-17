from __future__ import annotations

import importlib
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any, cast

from PIL import Image

PdfPath = str | PathLike[str]


@dataclass(frozen=True)
class RenderedPage:
    page_index: int
    dpi: int
    width_px: int
    height_px: int
    image: Image.Image


def pdf_page_count(path: PdfPath) -> int:
    document = _open_document(path)
    try:
        return int(document.page_count)
    finally:
        document.close()


def page_text(path: PdfPath, *, page_index: int) -> str:
    document = _open_document(path)
    try:
        page = document.load_page(page_index)
        return str(page.get_text("text"))
    finally:
        document.close()


def render_pdf_page(path: PdfPath, *, page_index: int, dpi: int = 200) -> RenderedPage:
    if dpi <= 0:
        raise ValueError("dpi must be positive")

    fitz = _fitz()
    document = _open_document(path)
    try:
        page = document.load_page(page_index)
        scale = dpi / 72.0
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            colorspace=fitz.csRGB,
            alpha=False,
        )
        image = Image.frombytes("RGB", (int(pixmap.width), int(pixmap.height)), pixmap.samples)
        return RenderedPage(
            page_index=page_index,
            dpi=dpi,
            width_px=int(pixmap.width),
            height_px=int(pixmap.height),
            image=image,
        )
    finally:
        document.close()


def _open_document(path: PdfPath) -> Any:
    return _fitz().open(Path(path))


def _fitz() -> Any:
    return cast(Any, importlib.import_module("fitz"))
