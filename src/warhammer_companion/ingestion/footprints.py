from __future__ import annotations

import importlib
import json
from collections.abc import Iterable, Sequence
from os import PathLike
from pathlib import Path
from typing import Any, cast

import cv2
import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel, Field
from shapely.geometry import Polygon

from warhammer_companion.ingestion.pdf import pdf_page_count, render_pdf_page

Point = tuple[float, float]
BBox = tuple[float, float, float, float]
ImageInput = Image.Image | np.ndarray[Any, np.dtype[np.uint8]]
FootprintPath = str | PathLike[str]

DEFAULT_FOOTPRINT_LIBRARY_PATH = Path("data/processed/footprint-library.json")
DEFAULT_FOOTPRINT_REVIEW_DIR = Path("data/processed/review/footprints")


class FootprintTemplate(BaseModel):
    id: str
    label: str
    footprint: list[Point]
    approx_width_inches: float = Field(ge=0)
    approx_height_inches: float = Field(ge=0)
    source_page: int = Field(ge=1)
    source_bbox: BBox
    source_units: str = "pixels"
    source_pixels_per_inch: float | None = Field(default=None, gt=0)
    source_points_per_inch: float | None = Field(default=None, gt=0)
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)

    def polygon(self) -> Polygon:
        return Polygon(self.footprint)


class FootprintLibrary(BaseModel):
    schema_version: int = 1
    source_pdf: str | None = None
    templates: list[FootprintTemplate]
    output_path: str | None = Field(default=None, exclude=True)


def segment_green_outline(image: ImageInput) -> np.ndarray[Any, np.dtype[np.uint8]]:
    rgb = _rgb_array(image)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    lower_green = np.array([35, 45, 35], dtype=np.uint8)
    upper_green = np.array([95, 255, 255], dtype=np.uint8)
    mask = cast(np.ndarray[Any, np.dtype[np.uint8]], cv2.inRange(hsv, lower_green, upper_green))
    kernel = np.ones((3, 3), dtype=np.uint8)
    return cast(
        np.ndarray[Any, np.dtype[np.uint8]],
        cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel),
    )


def find_green_outline_contours(
    image: ImageInput,
    *,
    min_contour_area_px: float = 250.0,
) -> list[np.ndarray[Any, np.dtype[np.int32]]]:
    if min_contour_area_px < 0:
        raise ValueError("min_contour_area_px must be non-negative")

    mask = segment_green_outline(image)
    contours_raw, _hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [
        cast(np.ndarray[Any, np.dtype[np.int32]], contour)
        for contour in contours_raw
        if float(cv2.contourArea(contour)) >= min_contour_area_px
    ]
    return sorted(contours, key=_contour_sort_key)


def extract_footprint_templates(
    image: ImageInput,
    *,
    source_page: int,
    pixels_per_inch: float,
    snap_increment_inches: float = 0.25,
    simplify_tolerance_px: float = 3.0,
    min_contour_area_px: float = 250.0,
    low_confidence_area_px: float = 1200.0,
    id_prefix: str | None = None,
) -> list[FootprintTemplate]:
    if source_page < 1:
        raise ValueError("source_page must be one-based")
    if pixels_per_inch <= 0:
        raise ValueError("pixels_per_inch must be positive")
    if snap_increment_inches <= 0:
        raise ValueError("snap_increment_inches must be positive")
    if simplify_tolerance_px < 0:
        raise ValueError("simplify_tolerance_px must be non-negative")
    if low_confidence_area_px < 0:
        raise ValueError("low_confidence_area_px must be non-negative")

    prefix = id_prefix or f"page-{source_page}"
    contours = find_green_outline_contours(image, min_contour_area_px=min_contour_area_px)
    templates: list[FootprintTemplate] = []
    for index, contour in enumerate(contours, start=1):
        templates.append(
            _template_from_contour(
                contour,
                template_id=f"{prefix}-footprint-{index}",
                label=f"Footprint {index}",
                source_page=source_page,
                pixels_per_inch=pixels_per_inch,
                snap_increment_inches=snap_increment_inches,
                simplify_tolerance_px=simplify_tolerance_px,
                low_confidence_area_px=low_confidence_area_px,
            )
        )
    return templates


def extract_footprint_templates_from_pdf(
    pdf_path: FootprintPath,
    *,
    pages: Iterable[int] | None = None,
    dpi: int = 200,
    pixels_per_inch: float | None = None,
    points_per_inch: float = 72.0,
    snap_increment_inches: float = 0.25,
    min_contour_area_px: float = 250.0,
    prefer_vector: bool = True,
) -> list[FootprintTemplate]:
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    if pixels_per_inch is not None and pixels_per_inch <= 0:
        raise ValueError("pixels_per_inch must be positive")

    page_numbers = (
        list(pages) if pages is not None else list(range(1, pdf_page_count(pdf_path) + 1))
    )
    templates_by_page: dict[int, list[FootprintTemplate]] = {}
    if prefer_vector:
        vector_templates = extract_vector_footprint_templates_from_pdf(
            pdf_path,
            pages=page_numbers,
            points_per_inch=points_per_inch,
            snap_increment_inches=snap_increment_inches,
        )
        for template in vector_templates:
            templates_by_page.setdefault(template.source_page, []).append(template)

    fallback_pixels_per_inch = float(pixels_per_inch if pixels_per_inch is not None else dpi)
    templates: list[FootprintTemplate] = []
    for source_page in page_numbers:
        if source_page in templates_by_page:
            templates.extend(templates_by_page[source_page])
            continue
        rendered = render_pdf_page(pdf_path, page_index=source_page - 1, dpi=dpi)
        templates.extend(
            extract_footprint_templates(
                rendered.image,
                source_page=source_page,
                pixels_per_inch=fallback_pixels_per_inch,
                snap_increment_inches=snap_increment_inches,
                min_contour_area_px=min_contour_area_px,
                id_prefix=f"page-{source_page}",
            )
        )
    return templates


def extract_vector_footprint_templates_from_pdf(
    pdf_path: FootprintPath,
    *,
    pages: Iterable[int] | None = None,
    points_per_inch: float = 72.0,
    snap_increment_inches: float = 0.25,
    simplify_tolerance_inches: float = 0.05,
    min_vector_items: int = 4,
    min_vector_width_pt: float = 60.0,
    min_vector_height_pt: float = 40.0,
    min_vector_area_sq_pt: float = 5000.0,
) -> list[FootprintTemplate]:
    if points_per_inch <= 0:
        raise ValueError("points_per_inch must be positive")
    if snap_increment_inches <= 0:
        raise ValueError("snap_increment_inches must be positive")
    if simplify_tolerance_inches < 0:
        raise ValueError("simplify_tolerance_inches must be non-negative")
    if min_vector_items < 1:
        raise ValueError("min_vector_items must be positive")

    fitz = _fitz()
    document = fitz.open(Path(pdf_path))
    try:
        page_numbers = (
            list(pages) if pages is not None else list(range(1, int(document.page_count) + 1))
        )
        templates: list[FootprintTemplate] = []
        for source_page in page_numbers:
            page = document.load_page(source_page - 1)
            page_templates = _extract_vector_templates_from_page(
                page,
                source_page=source_page,
                points_per_inch=points_per_inch,
                snap_increment_inches=snap_increment_inches,
                simplify_tolerance_inches=simplify_tolerance_inches,
                min_vector_items=min_vector_items,
                min_vector_width_pt=min_vector_width_pt,
                min_vector_height_pt=min_vector_height_pt,
                min_vector_area_sq_pt=min_vector_area_sq_pt,
            )
            templates.extend(page_templates)
        return templates
    finally:
        document.close()


def write_footprint_library(
    templates: Sequence[FootprintTemplate],
    output_path: FootprintPath = DEFAULT_FOOTPRINT_LIBRARY_PATH,
    *,
    source_pdf: str | None = None,
) -> FootprintLibrary:
    path = Path(output_path)
    library = FootprintLibrary(
        source_pdf=source_pdf,
        templates=list(templates),
        output_path=str(path),
    )
    payload = library.model_dump(mode="json", exclude_none=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return library


def write_official_footprint_artifacts(
    pdf_path: FootprintPath,
    *,
    output_path: FootprintPath = DEFAULT_FOOTPRINT_LIBRARY_PATH,
    review_dir: FootprintPath = DEFAULT_FOOTPRINT_REVIEW_DIR,
    dpi: int = 200,
    pixels_per_inch: float | None = None,
    pages: Iterable[int] | None = None,
) -> FootprintLibrary:
    page_numbers = (
        list(pages) if pages is not None else list(range(1, pdf_page_count(pdf_path) + 1))
    )
    all_templates: list[FootprintTemplate] = []
    review_path = Path(review_dir)
    for source_page in page_numbers:
        page_templates = extract_footprint_templates_from_pdf(
            pdf_path,
            pages=[source_page],
            dpi=dpi,
            pixels_per_inch=pixels_per_inch,
        )
        rendered = render_pdf_page(pdf_path, page_index=source_page - 1, dpi=dpi)
        all_templates.extend(page_templates)
        write_review_overlay(
            rendered.image,
            page_templates,
            review_path / f"page-{source_page}.png",
            pdf_point_scale=dpi / 72.0,
        )
    return write_footprint_library(all_templates, output_path, source_pdf=str(pdf_path))


def render_review_overlay(
    image: ImageInput,
    templates: Sequence[FootprintTemplate],
    *,
    pdf_point_scale: float | None = None,
) -> Image.Image:
    overlay = _pil_image(image).convert("RGB")
    draw = ImageDraw.Draw(overlay)
    for template in templates:
        left, top, right, bottom = template.source_bbox
        scale = pdf_point_scale if template.source_units == "pdf_points" else None
        if scale is not None:
            left *= scale
            top *= scale
            right *= scale
            bottom *= scale
        draw.rectangle((left, top, right, bottom), outline=(220, 0, 0), width=3)
        polygon_points = _review_polygon_points(template, scale=scale)
        if len(polygon_points) >= 3:
            draw.line(polygon_points + [polygon_points[0]], fill=(0, 90, 230), width=3)
        draw.text((left + 3, max(0.0, top - 12.0)), template.id, fill=(220, 0, 0))
    return overlay


def write_review_overlay(
    image: ImageInput,
    templates: Sequence[FootprintTemplate],
    output_path: FootprintPath,
    *,
    pdf_point_scale: float | None = None,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    render_review_overlay(image, templates, pdf_point_scale=pdf_point_scale).save(path)


def _extract_vector_templates_from_page(
    page: Any,
    *,
    source_page: int,
    points_per_inch: float,
    snap_increment_inches: float,
    simplify_tolerance_inches: float,
    min_vector_items: int,
    min_vector_width_pt: float,
    min_vector_height_pt: float,
    min_vector_area_sq_pt: float,
) -> list[FootprintTemplate]:
    candidates: list[tuple[BBox, int, Any]] = []
    page_rect = page.rect
    for drawing_index, drawing in enumerate(page.get_drawings()):
        rect = drawing.get("rect")
        items = drawing.get("items") or []
        if rect is None:
            continue
        if not _is_green_stroke(drawing):
            continue
        has_rect_item = any(item and item[0] == "re" for item in items)
        if len(items) < min_vector_items and not has_rect_item:
            continue
        if _touches_page_registration_marks(rect, page_rect):
            continue

        width = float(rect.x1 - rect.x0)
        height = float(rect.y1 - rect.y0)
        area = width * height
        if (
            width < min_vector_width_pt
            or height < min_vector_height_pt
            or area < min_vector_area_sq_pt
        ):
            continue

        candidates.append((_rect_bbox(rect), drawing_index, drawing))

    templates: list[FootprintTemplate] = []
    for index, (bbox, drawing_index, drawing) in enumerate(
        sorted(candidates, key=lambda candidate: (candidate[0][1], candidate[0][0])),
        start=1,
    ):
        points = _points_from_drawing_items(drawing.get("items") or [])
        templates.append(
            _template_from_pdf_points(
                points,
                template_id=f"page-{source_page}-footprint-{index}",
                label=f"Official footprint {source_page}.{index}",
                source_page=source_page,
                source_bbox=bbox,
                points_per_inch=points_per_inch,
                snap_increment_inches=snap_increment_inches,
                simplify_tolerance_inches=simplify_tolerance_inches,
                drawing_index=drawing_index,
            )
        )
    return templates


def _template_from_pdf_points(
    points: Sequence[Point],
    *,
    template_id: str,
    label: str,
    source_page: int,
    source_bbox: BBox,
    points_per_inch: float,
    snap_increment_inches: float,
    simplify_tolerance_inches: float,
    drawing_index: int,
) -> FootprintTemplate:
    warnings: list[str] = [f"pdf-vector-drawing-{drawing_index}"]
    confidence = 0.95
    local_points = _local_pdf_points(
        points,
        source_bbox=source_bbox,
        points_per_inch=points_per_inch,
        snap_increment_inches=snap_increment_inches,
    )
    if len(local_points) < 3:
        warnings.append("invalid-vector-path")
        confidence = 0.35
        local_points = _bbox_points(source_bbox, points_per_inch, snap_increment_inches)

    polygon = Polygon(local_points)
    if polygon.is_empty or not polygon.is_valid:
        warnings.append("repaired-invalid-polygon")
        confidence = min(confidence, 0.75)
        polygon = _polygon_from_repaired_geometry(polygon)
    if simplify_tolerance_inches > 0:
        simplified = polygon.simplify(simplify_tolerance_inches, preserve_topology=True)
        if isinstance(simplified, Polygon) and not simplified.is_empty:
            polygon = simplified

    width = _snap_value((source_bbox[2] - source_bbox[0]) / points_per_inch, snap_increment_inches)
    height = _snap_value((source_bbox[3] - source_bbox[1]) / points_per_inch, snap_increment_inches)
    return FootprintTemplate(
        id=template_id,
        label=label,
        footprint=_polygon_footprint_points(polygon),
        approx_width_inches=width,
        approx_height_inches=height,
        source_page=source_page,
        source_bbox=source_bbox,
        source_units="pdf_points",
        source_points_per_inch=points_per_inch,
        confidence=confidence,
        warnings=warnings,
    )


def _review_polygon_points(template: FootprintTemplate, *, scale: float | None) -> list[Point]:
    left, _top, _right, bottom = template.source_bbox
    if template.source_units == "pdf_points":
        points_per_inch = template.source_points_per_inch or 72.0
        points = [
            (left + x * points_per_inch, bottom - y * points_per_inch)
            for x, y in template.footprint
        ]
        if scale is not None:
            return [(x * scale, y * scale) for x, y in points]
        return points
    pixels_per_inch = template.source_pixels_per_inch or 1.0
    return [
        (left + x * pixels_per_inch, bottom - y * pixels_per_inch) for x, y in template.footprint
    ]


def _fitz() -> Any:
    return cast(Any, importlib.import_module("fitz"))


def _is_green_stroke(drawing: Any) -> bool:
    color = drawing.get("color")
    return _is_green_tuple(color)


def _is_green_tuple(color: Any) -> bool:
    if not color or len(color) < 3:
        return False
    red, green, blue = float(color[0]), float(color[1]), float(color[2])
    return green > 0.45 and red < 0.25 and blue < 0.45


def _touches_page_registration_marks(rect: Any, page_rect: Any, *, margin: float = 30.0) -> bool:
    return (
        float(rect.x0) <= float(page_rect.x0) + margin
        or float(rect.y0) <= float(page_rect.y0) + margin
        or float(rect.x1) >= float(page_rect.x1) - margin
        or float(rect.y1) >= float(page_rect.y1) - margin
    )


def _rect_bbox(rect: Any) -> BBox:
    return (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1))


def _points_from_drawing_items(items: Sequence[Any], *, curve_steps: int = 8) -> list[Point]:
    points: list[Point] = []
    for item in items:
        if not item:
            continue
        operator = item[0]
        segment_points: list[Point] = []
        if operator == "l" and len(item) >= 3:
            segment_points = [_point_tuple(item[1]), _point_tuple(item[2])]
        elif operator == "c" and len(item) >= 5:
            segment_points = _cubic_bezier_points(
                _point_tuple(item[1]),
                _point_tuple(item[2]),
                _point_tuple(item[3]),
                _point_tuple(item[4]),
                steps=curve_steps,
            )
        elif operator == "re" and len(item) >= 2:
            rect = item[1]
            segment_points = [
                (float(rect.x0), float(rect.y0)),
                (float(rect.x1), float(rect.y0)),
                (float(rect.x1), float(rect.y1)),
                (float(rect.x0), float(rect.y1)),
            ]
        for point in segment_points:
            if not points or points[-1] != point:
                points.append(point)
    if len(points) > 1 and points[0] == points[-1]:
        points.pop()
    return points


def _point_tuple(point: Any) -> Point:
    return (float(point.x), float(point.y))


def _cubic_bezier_points(
    p0: Point,
    p1: Point,
    p2: Point,
    p3: Point,
    *,
    steps: int,
) -> list[Point]:
    if steps < 1:
        raise ValueError("steps must be positive")
    points: list[Point] = []
    for index in range(steps + 1):
        t = index / steps
        inv = 1.0 - t
        x = inv**3 * p0[0] + 3 * inv**2 * t * p1[0] + 3 * inv * t**2 * p2[0] + t**3 * p3[0]
        y = inv**3 * p0[1] + 3 * inv**2 * t * p1[1] + 3 * inv * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, y))
    return points


def _local_pdf_points(
    points: Sequence[Point],
    *,
    source_bbox: BBox,
    points_per_inch: float,
    snap_increment_inches: float,
) -> list[Point]:
    left, _top, _right, bottom = source_bbox
    local_points: list[Point] = []
    for x_pt, y_pt in points:
        point = (
            _snap_value((x_pt - left) / points_per_inch, snap_increment_inches),
            _snap_value((bottom - y_pt) / points_per_inch, snap_increment_inches),
        )
        if not local_points or local_points[-1] != point:
            local_points.append(point)
    if len(local_points) > 1 and local_points[0] == local_points[-1]:
        local_points.pop()
    return local_points


def _template_from_contour(
    contour: np.ndarray[Any, np.dtype[np.int32]],
    *,
    template_id: str,
    label: str,
    source_page: int,
    pixels_per_inch: float,
    snap_increment_inches: float,
    simplify_tolerance_px: float,
    low_confidence_area_px: float,
) -> FootprintTemplate:
    source_bbox = _contour_bbox(contour)
    area_px = float(cv2.contourArea(contour))
    warnings: list[str] = []
    confidence = 1.0

    if area_px < low_confidence_area_px:
        warnings.append("small-source-contour")
        confidence = min(confidence, 0.65)

    simplified = cast(
        np.ndarray[Any, np.dtype[np.int32]],
        cv2.approxPolyDP(contour, simplify_tolerance_px, True),
    )
    points = _local_snapped_points(
        simplified,
        source_bbox=source_bbox,
        pixels_per_inch=pixels_per_inch,
        snap_increment_inches=snap_increment_inches,
    )
    if len(points) < 3:
        warnings.append("invalid-simplified-contour")
        confidence = min(confidence, 0.35)
        points = _bbox_points(source_bbox, pixels_per_inch, snap_increment_inches)

    polygon = Polygon(points)
    if polygon.is_empty or not polygon.is_valid:
        warnings.append("repaired-invalid-polygon")
        confidence = min(confidence, 0.75)
        polygon = _polygon_from_repaired_geometry(polygon)

    footprint = _polygon_footprint_points(polygon)
    width = _snap_value((source_bbox[2] - source_bbox[0]) / pixels_per_inch, snap_increment_inches)
    height = _snap_value((source_bbox[3] - source_bbox[1]) / pixels_per_inch, snap_increment_inches)
    return FootprintTemplate(
        id=template_id,
        label=label,
        footprint=footprint,
        approx_width_inches=width,
        approx_height_inches=height,
        source_page=source_page,
        source_bbox=source_bbox,
        source_pixels_per_inch=pixels_per_inch,
        confidence=confidence,
        warnings=warnings,
    )


def _rgb_array(image: ImageInput) -> np.ndarray[Any, np.dtype[np.uint8]]:
    if isinstance(image, Image.Image):
        return np.asarray(image.convert("RGB"), dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("image array must have at least three channels")
    return np.asarray(image[:, :, :3], dtype=np.uint8)


def _pil_image(image: ImageInput) -> Image.Image:
    if isinstance(image, Image.Image):
        return image
    return Image.fromarray(_rgb_array(image), mode="RGB")


def _contour_sort_key(contour: np.ndarray[Any, np.dtype[np.int32]]) -> tuple[float, float]:
    left, top, _right, _bottom = _contour_bbox(contour)
    return (top, left)


def _contour_bbox(contour: np.ndarray[Any, np.dtype[np.int32]]) -> BBox:
    points = _contour_points(contour)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _contour_points(contour: np.ndarray[Any, np.dtype[np.int32]]) -> list[Point]:
    reshaped = contour.reshape((-1, 2))
    return [(float(point[0]), float(point[1])) for point in reshaped]


def _local_snapped_points(
    contour: np.ndarray[Any, np.dtype[np.int32]],
    *,
    source_bbox: BBox,
    pixels_per_inch: float,
    snap_increment_inches: float,
) -> list[Point]:
    left, _top, _right, bottom = source_bbox
    points: list[Point] = []
    for x_px, y_px in _contour_points(contour):
        point = (
            _snap_value((x_px - left) / pixels_per_inch, snap_increment_inches),
            _snap_value((bottom - y_px) / pixels_per_inch, snap_increment_inches),
        )
        if not points or points[-1] != point:
            points.append(point)
    if len(points) > 1 and points[0] == points[-1]:
        points.pop()
    return points


def _bbox_points(
    source_bbox: BBox,
    pixels_per_inch: float,
    snap_increment_inches: float,
) -> list[Point]:
    left, top, right, bottom = source_bbox
    width = _snap_value((right - left) / pixels_per_inch, snap_increment_inches)
    height = _snap_value((bottom - top) / pixels_per_inch, snap_increment_inches)
    return [(0.0, 0.0), (width, 0.0), (width, height), (0.0, height)]


def _polygon_footprint_points(polygon: Polygon) -> list[Point]:
    exterior = polygon.exterior.coords[:-1]
    return [(round(float(x), 6), round(float(y), 6)) for x, y in exterior]


def _polygon_from_repaired_geometry(polygon: Polygon) -> Polygon:
    repaired = polygon.convex_hull
    if isinstance(repaired, Polygon):
        return repaired
    return polygon


def _snap_value(value: float, increment: float) -> float:
    snapped = round(value / increment) * increment
    return round(snapped, 6)
