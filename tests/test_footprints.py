from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest
from PIL import Image

from warhammer_companion.ingestion.footprints import (
    extract_footprint_templates,
    extract_footprint_templates_from_pdf,
    extract_vector_footprint_templates_from_pdf,
    find_green_outline_contours,
    segment_green_outline,
    write_footprint_library,
    write_official_footprint_artifacts,
    write_review_overlay,
)

GREEN = (0, 170, 0)
RED = (220, 0, 0)
WHITE = (255, 255, 255)


def test_green_outline_segmentation_finds_green_and_ignores_other_colours() -> None:
    image = _synthetic_outline_image([(20, 30, 100, 80)])
    pixels = np.asarray(image).copy()
    pixels[5:20, 5:20] = RED

    mask = segment_green_outline(Image.fromarray(pixels))
    contours = find_green_outline_contours(Image.fromarray(pixels), min_contour_area_px=20.0)

    assert mask[30, 20] == 255
    assert mask[10, 10] == 0
    assert len(contours) == 1


def test_extract_footprint_template_simplifies_outline_and_records_source_bbox() -> None:
    image = _synthetic_outline_image([(20, 30, 100, 80)])

    templates = extract_footprint_templates(
        image,
        source_page=2,
        pixels_per_inch=10.0,
        min_contour_area_px=20.0,
    )

    assert len(templates) == 1
    template = templates[0]
    assert template.id == "page-2-footprint-1"
    assert template.source_page == 2
    assert template.source_bbox == (20.0, 30.0, 100.0, 80.0)
    assert len(template.footprint) == 4
    assert template.polygon().bounds == pytest.approx((0.0, 0.0, 8.0, 5.0))
    assert template.approx_width_inches == 8.0
    assert template.approx_height_inches == 5.0
    assert template.confidence == pytest.approx(1.0)
    assert template.warnings == []


def test_extract_footprint_template_snaps_polygon_and_dimensions_to_quarter_inches() -> None:
    image = _synthetic_outline_image([(20, 30, 96, 82)])

    templates = extract_footprint_templates(
        image,
        source_page=1,
        pixels_per_inch=10.0,
        snap_increment_inches=0.25,
        min_contour_area_px=20.0,
    )

    template = templates[0]
    assert template.approx_width_inches == 7.5
    assert template.approx_height_inches == 5.25
    assert template.polygon().bounds == pytest.approx((0.0, 0.0, 7.5, 5.25))


def test_small_contours_are_returned_with_confidence_warning() -> None:
    image = _synthetic_outline_image([(10, 10, 22, 22)], width=40, height=40)

    templates = extract_footprint_templates(
        image,
        source_page=1,
        pixels_per_inch=10.0,
        min_contour_area_px=10.0,
        low_confidence_area_px=500.0,
    )

    assert len(templates) == 1
    assert templates[0].confidence < 0.8
    assert "small-source-contour" in templates[0].warnings


def test_write_footprint_library_persists_templates_with_provenance(tmp_path: Path) -> None:
    image = _synthetic_outline_image([(20, 30, 100, 80)])
    templates = extract_footprint_templates(
        image,
        source_page=3,
        pixels_per_inch=10.0,
        min_contour_area_px=20.0,
    )

    output_path = tmp_path / "footprint-library.json"
    library = write_footprint_library(templates, output_path, source_pdf="official.pdf")

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert library.output_path == str(output_path)
    assert payload["schema_version"] == 1
    assert payload["source_pdf"] == "official.pdf"
    assert payload["templates"][0]["source_page"] == 3
    assert payload["templates"][0]["source_bbox"] == [20.0, 30.0, 100.0, 80.0]


def test_write_review_overlay_marks_extracted_source_bbox(tmp_path: Path) -> None:
    image = _synthetic_outline_image([(20, 30, 100, 80)])
    templates = extract_footprint_templates(
        image,
        source_page=1,
        pixels_per_inch=10.0,
        min_contour_area_px=20.0,
    )

    overlay_path = tmp_path / "review" / "page-1.png"
    write_review_overlay(image, templates, overlay_path)

    assert overlay_path.exists()
    overlay = Image.open(overlay_path)
    assert overlay.size == image.size
    overlay_pixels = np.asarray(overlay)
    assert np.any(np.all(overlay_pixels == np.array([0, 90, 230]), axis=2))


def test_extract_vector_footprints_keeps_large_green_paths_and_ignores_fragments(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "footprints.pdf"
    fitz = _fitz()
    document = fitz.open()
    page = document.new_page(width=360, height=240)
    shape = page.new_shape()
    shape.draw_polyline(
        [
            fitz.Point(72, 72),
            fitz.Point(216, 72),
            fitz.Point(216, 144),
            fitz.Point(72, 144),
        ]
    )
    shape.finish(color=(0.0, 0.665, 0.309), width=2, closePath=True)
    shape.commit()
    page.draw_line(fitz.Point(20, 20), fitz.Point(35, 20), color=(0.0, 0.665, 0.309), width=2)
    document.save(pdf_path)
    document.close()

    templates = extract_vector_footprint_templates_from_pdf(pdf_path)

    assert len(templates) == 1
    template = templates[0]
    assert template.source_units == "pdf_points"
    assert template.source_bbox == (72.0, 72.0, 216.0, 144.0)
    assert template.approx_width_inches == 2.0
    assert template.approx_height_inches == 1.0
    assert template.polygon().bounds == pytest.approx((0.0, 0.0, 2.0, 1.0))
    assert template.confidence == pytest.approx(0.95)
    assert template.warnings == ["pdf-vector-drawing-0"]


def test_pdf_wrapper_uses_dpi_scale_for_forced_raster_fallback(tmp_path: Path) -> None:
    pdf_path = _mixed_vector_and_raster_pdf(tmp_path)

    templates = extract_footprint_templates_from_pdf(
        pdf_path,
        pages=[1],
        dpi=72,
        min_contour_area_px=20.0,
        prefer_vector=False,
    )

    assert len(templates) == 1
    template = templates[0]
    assert template.source_units == "pixels"
    assert template.source_pixels_per_inch == 72.0
    assert template.approx_width_inches == 2.0
    assert template.approx_height_inches == 1.0


def test_pdf_wrapper_falls_back_only_for_pages_without_vector_templates(
    tmp_path: Path,
) -> None:
    pdf_path = _mixed_vector_and_raster_pdf(tmp_path)

    templates = extract_footprint_templates_from_pdf(
        pdf_path,
        dpi=72,
        min_contour_area_px=20.0,
    )

    assert [template.source_page for template in templates] == [1, 2]
    assert [template.source_units for template in templates] == ["pdf_points", "pixels"]
    assert [template.approx_width_inches for template in templates] == [2.0, 2.0]
    assert [template.approx_height_inches for template in templates] == [1.0, 1.0]


def test_write_official_footprint_artifacts_uses_public_pdf_wrapper(
    tmp_path: Path,
) -> None:
    pdf_path = _mixed_vector_and_raster_pdf(tmp_path)
    output_path = tmp_path / "processed" / "footprint-library.json"
    review_dir = tmp_path / "review" / "footprints"

    library = write_official_footprint_artifacts(
        pdf_path,
        output_path=output_path,
        review_dir=review_dir,
        dpi=72,
    )

    assert output_path.exists()
    assert len(library.templates) == 2
    assert (review_dir / "page-1.png").exists()
    assert (review_dir / "page-2.png").exists()


def _synthetic_outline_image(
    boxes: list[tuple[int, int, int, int]],
    *,
    width: int = 140,
    height: int = 100,
    stroke: int = 3,
) -> Image.Image:
    pixels = np.full((height, width, 3), WHITE, dtype=np.uint8)
    for left, top, right, bottom in boxes:
        pixels[top : top + stroke, left : right + 1] = GREEN
        pixels[bottom - stroke + 1 : bottom + 1, left : right + 1] = GREEN
        pixels[top : bottom + 1, left : left + stroke] = GREEN
        pixels[top : bottom + 1, right - stroke + 1 : right + 1] = GREEN
    return Image.fromarray(pixels, mode="RGB")


def _mixed_vector_and_raster_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "mixed-footprints.pdf"
    raster_path = tmp_path / "raster-page.png"
    _synthetic_outline_image([(72, 72, 216, 144)], width=360, height=240, stroke=4).save(
        raster_path
    )

    fitz = _fitz()
    document = fitz.open()
    page_1 = document.new_page(width=360, height=240)
    shape = page_1.new_shape()
    shape.draw_polyline(
        [
            fitz.Point(72, 72),
            fitz.Point(216, 72),
            fitz.Point(216, 144),
            fitz.Point(72, 144),
        ]
    )
    shape.finish(color=(0.0, 0.665, 0.309), width=2, closePath=True)
    shape.commit()

    page_2 = document.new_page(width=360, height=240)
    page_2.insert_image(fitz.Rect(0, 0, 360, 240), filename=str(raster_path))
    document.save(pdf_path)
    document.close()
    return pdf_path


def _fitz() -> Any:
    return cast(Any, importlib.import_module("fitz"))
