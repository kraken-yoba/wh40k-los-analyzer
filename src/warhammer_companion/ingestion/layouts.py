from __future__ import annotations

import importlib
import json
import re
from collections.abc import Iterable, Sequence
from os import PathLike
from pathlib import Path
from typing import Any, Literal, cast

import cv2
import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel, Field
from shapely.geometry import MultiPolygon, Polygon

from warhammer_companion.ingestion.coordinates import BoardTransform, image_to_board_point
from warhammer_companion.ingestion.official_features import (
    OfficialFeatureCode as OfficialFeatureCode,
)
from warhammer_companion.ingestion.official_features import (
    extract_official_feature_labels,
)
from warhammer_companion.ingestion.pdf import pdf_page_count, render_pdf_page

Point = tuple[float, float]
BBox = tuple[float, float, float, float]
LayoutPath = str | PathLike[str]
LayoutElementKind = Literal["deployment", "terrain_area", "terrain_feature"]
FeatureType = Literal["dense", "light"]
WallSide = Literal["left", "right", "top", "bottom"]
FeatureProfile = Literal[
    "light_area",
    "ruined_wall_section",
    "ruined_wall_l",
    "ruined_wall_u",
    "ruined_wall_perimeter",
    "container_or_solid",
    "solid_los_blocker",
    "floor_or_platform",
    "unknown_dense",
]

DEFAULT_LAYOUT_LIBRARY_PATH = Path("data/processed/layout-library.json")
DEFAULT_LAYOUT_REVIEW_DIR = Path("data/processed/review/layouts")
DEFAULT_LAYOUT_START_PAGE = 9
DEFAULT_LAYOUT_END_PAGE = 53

BOARD_WIDTH_INCHES = 44.0
BOARD_HEIGHT_INCHES = 60.0

DARK_STROKE = (0.137, 0.122, 0.125)
RED_DEPLOYMENT = (0.618, 0.04, 0.056)
BLUE_DEPLOYMENT = (0.0, 0.241, 0.408)
TERRAIN_GREY = (0.82, 0.826, 0.832)
_NO_MATCH = object()


class LayoutElement(BaseModel):
    id: str
    label: str
    kind: LayoutElementKind
    feature_type: FeatureType | None = None
    feature_profile: FeatureProfile | None = None
    feature_wall_sides: list[WallSide] | None = None
    official_feature_code: OfficialFeatureCode | None = None
    terrain_area_id: str | None = None
    source_role: str | None = None
    footprint: list[Point]
    source_page: int = Field(ge=1)
    source_bbox: BBox
    source_drawing_index: int | None = Field(default=None, ge=0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)

    def polygon(self) -> Polygon:
        return Polygon(self.footprint)


class ExtractedLayout(BaseModel):
    id: str
    name: str
    source_pdf: str | None = None
    source_page: int = Field(ge=1)
    layout_code: str | None = None
    board_rect: BBox
    board_width_inches: float = BOARD_WIDTH_INCHES
    board_height_inches: float = BOARD_HEIGHT_INCHES
    deployment_zones: list[LayoutElement]
    terrain_areas: list[LayoutElement]
    terrain_features: list[LayoutElement]
    warnings: list[str] = Field(default_factory=list)

    def board_transform(self) -> BoardTransform:
        return BoardTransform(
            self.board_rect,
            board_width_inches=self.board_width_inches,
            board_height_inches=self.board_height_inches,
        )


class LayoutLibrary(BaseModel):
    schema_version: int = 1
    source_pdf: str | None = None
    layouts: list[ExtractedLayout]
    output_path: str | None = Field(default=None, exclude=True)


def default_layout_pages(pdf_path: LayoutPath) -> list[int]:
    page_count = pdf_page_count(pdf_path)
    end_page = min(DEFAULT_LAYOUT_END_PAGE, page_count)
    if end_page < DEFAULT_LAYOUT_START_PAGE:
        return []
    return list(range(DEFAULT_LAYOUT_START_PAGE, end_page + 1))


def extract_layouts_from_pdf(
    pdf_path: LayoutPath,
    *,
    pages: Iterable[int] | None = None,
    feature_dpi: int = 200,
) -> list[ExtractedLayout]:
    page_numbers = list(pages) if pages is not None else default_layout_pages(pdf_path)
    return [
        extract_layout_from_pdf(pdf_path, page_number=page_number, feature_dpi=feature_dpi)
        for page_number in page_numbers
    ]


def extract_layout_from_pdf(
    pdf_path: LayoutPath,
    *,
    page_number: int,
    feature_dpi: int = 200,
) -> ExtractedLayout:
    if page_number < 1:
        raise ValueError("page_number must be one-based")
    if feature_dpi <= 0:
        raise ValueError("feature_dpi must be positive")

    fitz = _fitz()
    document = fitz.open(Path(pdf_path))
    try:
        page = document.load_page(page_number - 1)
        drawings = list(page.get_drawings())
        board_rect = detect_board_rect(drawings)
        transform = BoardTransform(board_rect)
        board_polygon = _board_polygon()
        page_text = str(page.get_text("text"))
        layout_code = _layout_code(page_text)

        deployments = _extract_elements(
            drawings,
            transform,
            board_polygon=board_polygon,
            source_page=page_number,
            kind="deployment",
            color_roles=((RED_DEPLOYMENT, "attacker"), (BLUE_DEPLOYMENT, "defender")),
            min_area_pdf=1200.0,
        )
        terrain_areas = _extract_elements(
            drawings,
            transform,
            board_polygon=board_polygon,
            source_page=page_number,
            kind="terrain_area",
            color_roles=((TERRAIN_GREY, None),),
            min_area_pdf=750.0,
        )
        rendered = render_pdf_page(pdf_path, page_index=page_number - 1, dpi=feature_dpi)
        terrain_features = _extract_raster_features(
            rendered.image,
            terrain_areas,
            transform,
            source_page=page_number,
            pdf_point_scale=feature_dpi / 72.0,
        )
        official_features = extract_official_feature_labels(
            page,
            transform,
            terrain_areas,
            raster_features=terrain_features,
            source_page=page_number,
            element_factory=LayoutElement,
        )
        if official_features:
            official_area_ids = {
                feature.terrain_area_id
                for feature in official_features
                if feature.terrain_area_id is not None
            }
            terrain_features = [
                feature
                for feature in terrain_features
                if feature.feature_type != "dense"
                or feature.terrain_area_id not in official_area_ids
            ]
            terrain_features.extend(official_features)

        warnings: list[str] = []
        if len(deployments) < 2:
            warnings.append("fewer-than-two-deployment-zones")
        if not terrain_areas:
            warnings.append("no-terrain-areas-detected")
        if not terrain_features:
            warnings.append("no-terrain-features-detected")

        name = f"Official Layout {layout_code or page_number}"
        return ExtractedLayout(
            id=f"official-layout-page-{page_number}",
            name=name,
            source_pdf=str(pdf_path),
            source_page=page_number,
            layout_code=layout_code,
            board_rect=board_rect,
            deployment_zones=deployments,
            terrain_areas=terrain_areas,
            terrain_features=terrain_features,
            warnings=warnings,
        )
    finally:
        document.close()


def detect_board_rect(drawings: Sequence[Any]) -> BBox:
    candidates: list[tuple[float, float, BBox]] = []
    expected_aspect = BOARD_WIDTH_INCHES / BOARD_HEIGHT_INCHES
    for drawing in drawings:
        rect = drawing.get("rect")
        color = drawing.get("color")
        fill = drawing.get("fill")
        width = float(drawing.get("width") or 0.0)
        if rect is None or fill is not None:
            continue
        rect_width = float(rect.x1 - rect.x0)
        rect_height = float(rect.y1 - rect.y0)
        if rect_width <= 0 or rect_height <= 0:
            continue
        aspect = rect_width / rect_height
        area = rect_width * rect_height
        if width < 2.0 or area < 50_000 or abs(aspect - expected_aspect) > 0.03:
            continue
        if not _close_color(color, DARK_STROKE, tolerance=0.08):
            continue
        candidates.append((area, width, _rect_bbox(rect)))
    if not candidates:
        raise ValueError("Could not detect board rectangle")
    return max(candidates, key=lambda candidate: (candidate[1], candidate[0]))[2]


def write_layout_library(
    layouts: Sequence[ExtractedLayout],
    output_path: LayoutPath = DEFAULT_LAYOUT_LIBRARY_PATH,
    *,
    source_pdf: str | None = None,
) -> LayoutLibrary:
    path = Path(output_path)
    library = LayoutLibrary(source_pdf=source_pdf, layouts=list(layouts), output_path=str(path))
    payload = library.model_dump(mode="json", exclude_none=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return library


def write_official_layout_artifacts(
    pdf_path: LayoutPath,
    *,
    output_path: LayoutPath = DEFAULT_LAYOUT_LIBRARY_PATH,
    review_dir: LayoutPath = DEFAULT_LAYOUT_REVIEW_DIR,
    pages: Iterable[int] | None = None,
    dpi: int = 200,
) -> LayoutLibrary:
    page_numbers = list(pages) if pages is not None else default_layout_pages(pdf_path)
    layouts = extract_layouts_from_pdf(pdf_path, pages=page_numbers, feature_dpi=dpi)
    review_path = Path(review_dir)
    for layout in layouts:
        rendered = render_pdf_page(pdf_path, page_index=layout.source_page - 1, dpi=dpi)
        write_layout_review_overlay(
            rendered.image,
            layout,
            review_path / f"page-{layout.source_page}.png",
            pdf_point_scale=dpi / 72.0,
        )
    return write_layout_library(layouts, output_path, source_pdf=str(pdf_path))


def render_layout_review_overlay(
    image: Image.Image,
    layout: ExtractedLayout,
    *,
    pdf_point_scale: float = 1.0,
) -> Image.Image:
    overlay = image.convert("RGB")
    draw = ImageDraw.Draw(overlay, "RGBA")
    transform = layout.board_transform()
    _draw_board_rect(draw, transform, scale=pdf_point_scale)
    for element in layout.deployment_zones:
        _draw_element(draw, element, transform, scale=pdf_point_scale, fill=(22, 112, 224, 60))
    for element in layout.terrain_areas:
        _draw_element(draw, element, transform, scale=pdf_point_scale, fill=(220, 120, 20, 70))
    for element in layout.terrain_features:
        fill = (0, 180, 120, 100) if element.feature_type == "dense" else (220, 170, 20, 110)
        _draw_element(draw, element, transform, scale=pdf_point_scale, fill=fill)
    return overlay


def write_layout_review_overlay(
    image: Image.Image,
    layout: ExtractedLayout,
    output_path: LayoutPath,
    *,
    pdf_point_scale: float = 1.0,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    render_layout_review_overlay(image, layout, pdf_point_scale=pdf_point_scale).save(path)


def _extract_elements(
    drawings: Sequence[Any],
    transform: BoardTransform,
    *,
    board_polygon: Polygon,
    source_page: int,
    kind: LayoutElementKind,
    color_roles: Sequence[tuple[tuple[float, float, float], str | None]],
    min_area_pdf: float,
    confidence: float = 0.9,
    warning: str | None = None,
) -> list[LayoutElement]:
    elements: list[LayoutElement] = []
    for drawing_index, drawing in enumerate(drawings):
        rect = drawing.get("rect")
        fill = drawing.get("fill")
        if rect is None or fill is None:
            continue
        source_role = _matched_color_role(fill, color_roles)
        if source_role is _NO_MATCH:
            continue
        matched_role = cast(str | None, source_role)
        bbox = _rect_bbox(rect)
        area_pdf = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if area_pdf < min_area_pdf or not _intersects_bbox(bbox, transform.board_rect):
            continue
        polygon = _drawing_to_board_polygon(drawing, transform, fallback_bbox=bbox)
        clipped = _largest_polygon(polygon.intersection(board_polygon))
        if clipped.is_empty or clipped.area <= 0.05:
            continue
        footprint = _polygon_points(clipped)
        warnings = [warning] if warning else []
        stable_id_part = matched_role or kind
        ordinal = _next_role_ordinal(elements, matched_role)
        id_suffix = (
            stable_id_part if matched_role and ordinal == 1 else f"{stable_id_part}-{ordinal}"
        )
        label = (
            stable_id_part.replace("_", " ").title()
            if matched_role and ordinal == 1
            else f"{stable_id_part.replace('_', ' ').title()} {ordinal}"
        )
        elements.append(
            LayoutElement(
                id=f"page-{source_page}-{id_suffix}",
                label=label,
                kind=kind,
                source_role=matched_role,
                footprint=footprint,
                source_page=source_page,
                source_bbox=bbox,
                source_drawing_index=drawing_index,
                confidence=confidence,
                warnings=warnings,
            )
        )
    return elements


def _next_role_ordinal(elements: Sequence[LayoutElement], role: str | None) -> int:
    if role is None:
        return len(elements) + 1
    return sum(element.source_role == role for element in elements) + 1


def _extract_raster_features(
    image: Image.Image,
    terrain_areas: Sequence[LayoutElement],
    transform: BoardTransform,
    *,
    source_page: int,
    pdf_point_scale: float,
    min_area_sq_inches: float = 0.25,
) -> list[LayoutElement]:
    if pdf_point_scale <= 0:
        raise ValueError("pdf_point_scale must be positive")

    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    dense_mask = cast(
        np.ndarray[Any, np.dtype[np.uint8]],
        cv2.inRange(
            hsv,
            np.array([65, 45, 35], dtype=np.uint8),
            np.array([100, 255, 210], dtype=np.uint8),
        ),
    )
    light_mask = cast(
        np.ndarray[Any, np.dtype[np.uint8]],
        cv2.inRange(
            hsv,
            np.array([10, 45, 35], dtype=np.uint8),
            np.array([35, 255, 220], dtype=np.uint8),
        ),
    )
    feature_specs: tuple[tuple[FeatureType, np.ndarray[Any, np.dtype[np.uint8]]], ...] = (
        ("dense", dense_mask),
        ("light", light_mask),
    )
    kernel = np.ones((3, 3), dtype=np.uint8)
    board_area_px_per_sq_in = (
        transform.width_px * pdf_point_scale / transform.board_width_inches
    ) * (transform.height_px * pdf_point_scale / transform.board_height_inches)
    min_area_px = max(12.0, board_area_px_per_sq_in * min_area_sq_inches)
    board_polygon = _board_polygon()
    elements: list[LayoutElement] = []

    for terrain_area in terrain_areas:
        area_mask = _terrain_area_mask(rgb.shape[:2], terrain_area, transform, pdf_point_scale)
        area_polygon = terrain_area.polygon()
        for feature_type, mask in feature_specs:
            clipped_mask = cv2.bitwise_and(mask, area_mask)
            clipped_mask = cv2.morphologyEx(clipped_mask, cv2.MORPH_OPEN, kernel)
            contours_raw, _hierarchy = cv2.findContours(
                clipped_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            for contour in contours_raw:
                contour_array = cast(np.ndarray[Any, np.dtype[np.int32]], contour)
                contour_area = float(cv2.contourArea(contour_array))
                if contour_area < min_area_px:
                    continue
                polygon = _contour_to_board_polygon(contour_array, transform, pdf_point_scale)
                clipped = _largest_polygon(
                    polygon.intersection(area_polygon).intersection(board_polygon)
                )
                if clipped.is_empty or clipped.area <= 0.05:
                    continue
                feature_profile = _classify_feature_profile(feature_type, clipped)
                source_bbox = _contour_pdf_bbox(contour_array, pdf_point_scale)
                warnings = [
                    f"raster-{feature_type}-segmentation",
                    f"heuristic-{feature_type}-profile:{feature_profile}",
                ]
                elements.append(
                    LayoutElement(
                        id=f"page-{source_page}-terrain-feature-{len(elements) + 1}",
                        label=f"{feature_type.title()} Terrain Feature {len(elements) + 1}",
                        kind="terrain_feature",
                        feature_type=feature_type,
                        feature_profile=feature_profile,
                        terrain_area_id=terrain_area.id,
                        footprint=_polygon_points(clipped),
                        source_page=source_page,
                        source_bbox=source_bbox,
                        source_drawing_index=None,
                        confidence=0.7,
                        warnings=warnings,
                    )
                )
    return elements


def _classify_feature_profile(feature_type: FeatureType, polygon: Polygon) -> FeatureProfile:
    if feature_type == "light":
        return "light_area"

    min_x, min_y, max_x, max_y = polygon.bounds
    width = max_x - min_x
    height = max_y - min_y
    short_side = min(width, height)
    long_side = max(width, height)
    if short_side <= 0 or long_side <= 0:
        return "unknown_dense"

    aspect = long_side / short_side
    fill_ratio = polygon.area / max(width * height, 1e-9)
    if aspect >= 3.0 and short_side <= 2.0 and long_side >= 3.0:
        return "ruined_wall_section"
    if fill_ratio >= 0.55 and polygon.area >= 2.0 and aspect <= 3.0:
        return "container_or_solid"
    if polygon.area >= 0.75:
        return "solid_los_blocker"
    return "unknown_dense"


def _terrain_area_mask(
    image_shape: tuple[int, int],
    terrain_area: LayoutElement,
    transform: BoardTransform,
    pdf_point_scale: float,
) -> np.ndarray[Any, np.dtype[np.uint8]]:
    mask = np.zeros(image_shape, dtype=np.uint8)
    points = np.asarray(
        [
            _board_to_pdf_point(point, transform, scale=pdf_point_scale)
            for point in terrain_area.footprint
        ],
        dtype=np.int32,
    )
    if len(points) >= 3:
        cv2.fillPoly(mask, [points], 255)
    return mask


def _contour_to_board_polygon(
    contour: np.ndarray[Any, np.dtype[np.int32]],
    transform: BoardTransform,
    pdf_point_scale: float,
) -> Polygon:
    raw_points = contour.reshape((-1, 2))
    points = [
        image_to_board_point((float(x) / pdf_point_scale, float(y) / pdf_point_scale), transform)
        for x, y in raw_points
    ]
    if len(points) < 3:
        return Polygon()
    polygon = Polygon(points)
    if polygon.is_empty:
        return Polygon()
    if not polygon.is_valid:
        polygon = _largest_polygon(polygon.buffer(0))
    if polygon.is_empty or not polygon.is_valid:
        polygon = _largest_polygon(polygon.convex_hull)
    return _largest_polygon(polygon)


def _contour_pdf_bbox(
    contour: np.ndarray[Any, np.dtype[np.int32]],
    pdf_point_scale: float,
) -> BBox:
    x, y, width, height = cv2.boundingRect(contour)
    return (
        float(x) / pdf_point_scale,
        float(y) / pdf_point_scale,
        float(x + width) / pdf_point_scale,
        float(y + height) / pdf_point_scale,
    )


def _drawing_to_board_polygon(
    drawing: Any,
    transform: BoardTransform,
    *,
    fallback_bbox: BBox,
) -> Polygon:
    points = _points_from_drawing_items(drawing.get("items") or [])
    if len(points) < 3:
        points = _bbox_points(fallback_bbox)
    board_points = [image_to_board_point(point, transform) for point in points]
    polygon = Polygon(board_points)
    if polygon.is_empty:
        return Polygon()
    if not polygon.is_valid:
        repaired = polygon.buffer(0)
        polygon = _largest_polygon(repaired)
    if polygon.is_empty or not polygon.is_valid:
        polygon = _largest_polygon(polygon.convex_hull)
    return _largest_polygon(polygon)


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
            segment_points = _bbox_points(_rect_bbox(item[1]))
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
    points: list[Point] = []
    for index in range(steps + 1):
        t = index / steps
        inv = 1.0 - t
        x = inv**3 * p0[0] + 3 * inv**2 * t * p1[0] + 3 * inv * t**2 * p2[0] + t**3 * p3[0]
        y = inv**3 * p0[1] + 3 * inv**2 * t * p1[1] + 3 * inv * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, y))
    return points


def _draw_board_rect(draw: ImageDraw.ImageDraw, transform: BoardTransform, *, scale: float) -> None:
    left, top, right, bottom = transform.board_rect
    draw.rectangle(
        (left * scale, top * scale, right * scale, bottom * scale),
        outline=(0, 0, 0, 255),
        width=4,
    )


def _draw_element(
    draw: ImageDraw.ImageDraw,
    element: LayoutElement,
    transform: BoardTransform,
    *,
    scale: float,
    fill: tuple[int, int, int, int],
) -> None:
    points = [_board_to_pdf_point(point, transform, scale=scale) for point in element.footprint]
    if len(points) >= 3:
        draw.polygon(points, fill=fill, outline=(20, 30, 30, 220))


def _board_to_pdf_point(point: Point, transform: BoardTransform, *, scale: float) -> Point:
    x, y = point
    pdf_x = transform.left + x * transform.width_px / transform.board_width_inches
    pdf_y = transform.bottom - y * transform.height_px / transform.board_height_inches
    return (pdf_x * scale, pdf_y * scale)


def _largest_polygon(geometry: Any) -> Polygon:
    if isinstance(geometry, Polygon):
        return geometry
    if isinstance(geometry, MultiPolygon) and geometry.geoms:
        return max(geometry.geoms, key=lambda polygon: polygon.area)
    return Polygon()


def _polygon_points(polygon: Polygon) -> list[Point]:
    return [(round(float(x), 6), round(float(y), 6)) for x, y in polygon.exterior.coords[:-1]]


def _board_polygon() -> Polygon:
    return Polygon(
        [
            (0.0, 0.0),
            (BOARD_WIDTH_INCHES, 0.0),
            (BOARD_WIDTH_INCHES, BOARD_HEIGHT_INCHES),
            (0.0, BOARD_HEIGHT_INCHES),
        ]
    )


def _bbox_points(bbox: BBox) -> list[Point]:
    left, top, right, bottom = bbox
    return [(left, top), (right, top), (right, bottom), (left, bottom)]


def _rect_bbox(rect: Any) -> BBox:
    return (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1))


def _intersects_bbox(first: BBox, second: BBox) -> bool:
    return (
        first[0] < second[2]
        and first[2] > second[0]
        and first[1] < second[3]
        and first[3] > second[1]
    )


def _close_color(
    color: Any,
    target: tuple[float, float, float],
    *,
    tolerance: float,
) -> bool:
    return (
        bool(color)
        and len(color) >= 3
        and all(abs(float(color[index]) - target[index]) <= tolerance for index in range(3))
    )


def _matched_color_role(
    color: Any,
    color_roles: Sequence[tuple[tuple[float, float, float], str | None]],
) -> str | None | object:
    for target, role in color_roles:
        if _close_color(color, target, tolerance=0.03):
            return role
    return _NO_MATCH


def _layout_code(text: str) -> str | None:
    match = re.search(r"\bLAYOUT\s+([A-Z])\b", text)
    return match.group(1) if match else None


def _fitz() -> Any:
    return cast(Any, importlib.import_module("fitz"))
