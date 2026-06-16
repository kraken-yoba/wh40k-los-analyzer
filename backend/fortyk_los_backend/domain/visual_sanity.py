from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

import cv2
import fitz
import numpy as np
from numpy.typing import NDArray

from fortyk_los_backend.domain.extraction import (
    ATTACKER_FILL,
    BLACK_STROKE,
    BOARD_HEIGHT_INCHES,
    BOARD_WIDTH_INCHES,
    DEFENDER_FILL,
    TERRAIN_FILL,
    BoardTransform,
    PdfRect,
    _find_board_rect,
    extract_event_companion_layout,
)
from fortyk_los_backend.domain.models import CanonicalLayout, PolygonGeometry

RASTER_ZOOM = 2.0
COLOR_TOLERANCE_8BIT = 35
MASK_CLOSE_KERNEL_SIZE = 7
MASK_CLOSE_ITERATIONS = 2
BOARD_ALIGNMENT_TOLERANCE_INCHES = 0.25
DEPLOYMENT_ALIGNMENT_TOLERANCE_INCHES = 1.25
TERRAIN_ALIGNMENT_TOLERANCE_INCHES = 1.25


class VisualSanityStatus(StrEnum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class VisualSanityCheck:
    code: str
    status: VisualSanityStatus
    expected_count: int
    observed_count: int
    match_count: int
    max_residual_inches: float | None
    message: str


@dataclass(frozen=True)
class EventCompanionVisualSanityReport:
    layout_id: str
    source_page: int
    extraction_method: str
    status: VisualSanityStatus
    checks: tuple[VisualSanityCheck, ...]
    vision_advisory: dict[str, str]
    layout: CanonicalLayout


def run_event_companion_visual_sanity(
    pdf_path: Path,
    *,
    page_number: int,
    layout: CanonicalLayout | None = None,
) -> EventCompanionVisualSanityReport:
    extracted_layout = layout or extract_event_companion_layout(pdf_path, page_number=page_number)
    with fitz.open(pdf_path) as document:
        page = document[page_number - 1]
        drawings = list(page.get_drawings())
        board_rect = _find_board_rect(drawings)
        raster = _render_page_rgb(page)

    checks = (
        _board_alignment_check(raster, board_rect),
        _deployment_alignment_check(raster, board_rect, extracted_layout),
        _terrain_alignment_check(raster, board_rect, extracted_layout),
    )
    return EventCompanionVisualSanityReport(
        layout_id=extracted_layout.layout_id,
        source_page=page_number,
        extraction_method="event-companion-cv-sanity-v1",
        status=_overall_status(checks),
        checks=checks,
        vision_advisory={
            "status": "not_run",
            "reason": "Optional vision-model review is advisory and is not canonical geometry.",
            "input": "deterministic_cv_shape_alignment_report",
        },
        layout=extracted_layout,
    )


def _board_alignment_check(
    raster: NDArray[np.uint8],
    board_rect: PdfRect,
) -> VisualSanityCheck:
    observed = _detect_colored_rects(
        raster,
        BLACK_STROKE,
        min_area=board_rect.area * 0.45,
        max_area=None,
    )
    board_aspect = board_rect.width / board_rect.height
    candidates = [
        rect
        for rect in observed
        if rect.width > 0
        and rect.height > 0
        and abs((rect.width / rect.height) - board_aspect) < 0.08
    ]
    detected = max(candidates, key=lambda rect: rect.area) if candidates else None
    return _single_rect_check(
        code="board_raster_alignment",
        expected=board_rect,
        observed=detected,
        board_rect=board_rect,
        tolerance_inches=BOARD_ALIGNMENT_TOLERANCE_INCHES,
    )


def _deployment_alignment_check(
    raster: NDArray[np.uint8],
    board_rect: PdfRect,
    layout: CanonicalLayout,
) -> VisualSanityCheck:
    expected: list[PdfRect] = []
    observed: list[PdfRect] = []
    fill_by_zone = {"attacker": ATTACKER_FILL, "defender": DEFENDER_FILL}
    for deployment in layout.deployments:
        expected_rect = _polygon_to_pdf_rect(deployment.area, board_rect)
        expected.append(expected_rect)
        fill = fill_by_zone.get(deployment.zone_id)
        if fill is None:
            continue
        detected = _detect_colored_rect_near(
            raster,
            fill,
            expected_rect,
            inflate_pdf=8.0,
            min_pixel_count=100,
        )
        if detected is not None:
            observed.append(detected)
    return _multi_rect_check(
        code="deployment_raster_alignment",
        expected=tuple(expected),
        observed=tuple(observed),
        board_rect=board_rect,
        tolerance_inches=DEPLOYMENT_ALIGNMENT_TOLERANCE_INCHES,
    )


def _terrain_alignment_check(
    raster: NDArray[np.uint8],
    board_rect: PdfRect,
    layout: CanonicalLayout,
) -> VisualSanityCheck:
    expected: list[PdfRect] = []
    observed: list[PdfRect] = []
    for feature in layout.terrain_features:
        expected_rect = _polygon_to_pdf_rect(feature.footprint, board_rect)
        expected.append(expected_rect)
        detected = _detect_colored_rect_near(
            raster,
            TERRAIN_FILL,
            expected_rect,
            inflate_pdf=7.0,
            min_pixel_count=20,
        )
        if detected is not None:
            observed.append(detected)
    return _multi_rect_check(
        code="terrain_raster_alignment",
        expected=tuple(expected),
        observed=tuple(observed),
        board_rect=board_rect,
        tolerance_inches=TERRAIN_ALIGNMENT_TOLERANCE_INCHES,
    )


def _single_rect_check(
    *,
    code: str,
    expected: PdfRect,
    observed: PdfRect | None,
    board_rect: PdfRect,
    tolerance_inches: float,
) -> VisualSanityCheck:
    if observed is None:
        return VisualSanityCheck(
            code=code,
            status=VisualSanityStatus.FAILED,
            expected_count=1,
            observed_count=0,
            match_count=0,
            max_residual_inches=None,
            message="Expected raster shape was not detected.",
        )
    residual = _rect_residual_inches(expected, observed, board_rect)
    status = (
        VisualSanityStatus.PASSED
        if residual <= tolerance_inches
        else VisualSanityStatus.WARNING
    )
    return VisualSanityCheck(
        code=code,
        status=status,
        expected_count=1,
        observed_count=1,
        match_count=1,
        max_residual_inches=round(residual, 4),
        message=_residual_message(residual, tolerance_inches),
    )


def _multi_rect_check(
    *,
    code: str,
    expected: tuple[PdfRect, ...],
    observed: tuple[PdfRect, ...],
    board_rect: PdfRect,
    tolerance_inches: float,
) -> VisualSanityCheck:
    residuals = _match_residuals(expected, observed, board_rect)
    max_residual = max(residuals) if residuals else None
    count_matches = len(expected) == len(observed)
    residual_matches = max_residual is not None and max_residual <= tolerance_inches
    status = (
        VisualSanityStatus.PASSED
        if count_matches and residual_matches
        else VisualSanityStatus.WARNING
    )
    return VisualSanityCheck(
        code=code,
        status=status,
        expected_count=len(expected),
        observed_count=len(observed),
        match_count=len(residuals),
        max_residual_inches=round(max_residual, 4) if max_residual is not None else None,
        message=_residual_message(max_residual, tolerance_inches),
    )


def _match_residuals(
    expected: tuple[PdfRect, ...],
    observed: tuple[PdfRect, ...],
    board_rect: PdfRect,
) -> list[float]:
    remaining_observed = list(observed)
    residuals: list[float] = []
    for expected_rect in sorted(expected, key=lambda rect: (rect.y0, rect.x0, rect.y1, rect.x1)):
        if not remaining_observed:
            break
        best_index, best_rect = min(
            enumerate(remaining_observed),
            key=lambda item: _rect_residual_inches(expected_rect, item[1], board_rect),
        )
        best_residual = _rect_residual_inches(expected_rect, best_rect, board_rect)
        residuals.append(best_residual)
        remaining_observed.pop(best_index)
    return residuals


def _rect_residual_inches(expected: PdfRect, observed: PdfRect, board_rect: PdfRect) -> float:
    x_scale = BOARD_WIDTH_INCHES / board_rect.width
    y_scale = BOARD_HEIGHT_INCHES / board_rect.height
    residuals = (
        abs(expected.x0 - observed.x0) * x_scale,
        abs(expected.x1 - observed.x1) * x_scale,
        abs(expected.y0 - observed.y0) * y_scale,
        abs(expected.y1 - observed.y1) * y_scale,
    )
    return max(residuals)


def _residual_message(residual: float | None, tolerance_inches: float) -> str:
    if residual is None:
        return "No raster shape match was available for residual calculation."
    if residual <= tolerance_inches:
        return f"Raster shape residual {residual:.2f} in is within tolerance."
    return f"Raster shape residual {residual:.2f} in exceeds tolerance {tolerance_inches:.2f} in."


def _overall_status(checks: tuple[VisualSanityCheck, ...]) -> VisualSanityStatus:
    statuses = {check.status for check in checks}
    if VisualSanityStatus.FAILED in statuses:
        return VisualSanityStatus.FAILED
    if VisualSanityStatus.WARNING in statuses:
        return VisualSanityStatus.WARNING
    return VisualSanityStatus.PASSED


def _render_page_rgb(page: Any) -> NDArray[np.uint8]:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(RASTER_ZOOM, RASTER_ZOOM), alpha=False)
    return np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
        pixmap.height,
        pixmap.width,
        pixmap.n,
    )[:, :, :3]


def _detect_colored_rects(
    raster: NDArray[np.uint8],
    color: tuple[float, float, float],
    *,
    min_area: float,
    max_area: float | None,
) -> tuple[PdfRect, ...]:
    mask = _color_mask(raster, color)
    component_count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(
        mask,
        connectivity=8,
    )
    rects: list[PdfRect] = []
    for component_index in range(1, component_count):
        x, y, width, height, _area = stats[component_index]
        if width <= 0 or height <= 0:
            continue
        rect = PdfRect(
            x0=float(x) / RASTER_ZOOM,
            y0=float(y) / RASTER_ZOOM,
            x1=float(x + width) / RASTER_ZOOM,
            y1=float(y + height) / RASTER_ZOOM,
        )
        if rect.area < min_area:
            continue
        if max_area is not None and rect.area > max_area:
            continue
        rects.append(rect)
    return tuple(sorted(rects, key=lambda rect: (rect.y0, rect.x0, rect.y1, rect.x1)))


def _detect_colored_rect_near(
    raster: NDArray[np.uint8],
    color: tuple[float, float, float],
    expected: PdfRect,
    *,
    inflate_pdf: float,
    min_pixel_count: int,
) -> PdfRect | None:
    search_rect = expected.inflate(inflate_pdf)
    height, width = raster.shape[:2]
    x0 = max(0, int(search_rect.x0 * RASTER_ZOOM))
    y0 = max(0, int(search_rect.y0 * RASTER_ZOOM))
    x1 = min(width, int(search_rect.x1 * RASTER_ZOOM) + 1)
    y1 = min(height, int(search_rect.y1 * RASTER_ZOOM) + 1)
    if x1 <= x0 or y1 <= y0:
        return None
    mask = _color_mask(raster[y0:y1, x0:x1], color)
    ys, xs = np.nonzero(mask)
    if len(xs) < min_pixel_count:
        return None
    return PdfRect(
        x0=float(x0 + int(xs.min())) / RASTER_ZOOM,
        y0=float(y0 + int(ys.min())) / RASTER_ZOOM,
        x1=float(x0 + int(xs.max()) + 1) / RASTER_ZOOM,
        y1=float(y0 + int(ys.max()) + 1) / RASTER_ZOOM,
    )


def _color_mask(
    raster: NDArray[np.uint8],
    color: tuple[float, float, float],
) -> NDArray[np.uint8]:
    target = np.array([round(component * 255) for component in color], dtype=np.uint8)
    delta = np.abs(raster.astype(np.int16) - target.astype(np.int16))
    mask: NDArray[np.uint8] = np.asarray(
        np.all(delta <= COLOR_TOLERANCE_8BIT, axis=2),
        dtype=np.uint8,
    )
    kernel = np.ones((MASK_CLOSE_KERNEL_SIZE, MASK_CLOSE_KERNEL_SIZE), dtype=np.uint8)
    return cast(
        NDArray[np.uint8],
        cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=MASK_CLOSE_ITERATIONS),
    )


def _polygon_to_pdf_rect(polygon: PolygonGeometry, board_rect: PdfRect) -> PdfRect:
    transform = BoardTransform(board_rect)
    pdf_points = tuple(
        _board_point_to_pdf_rect_space(point.x, point.y, transform)
        for point in polygon.points
    )
    xs = [point[0] for point in pdf_points]
    ys = [point[1] for point in pdf_points]
    return PdfRect(x0=min(xs), y0=min(ys), x1=max(xs), y1=max(ys))


def _board_point_to_pdf_rect_space(
    x: float,
    y: float,
    transform: BoardTransform,
) -> tuple[float, float]:
    board_rect = transform.board_rect
    return (
        board_rect.x0 + (x / BOARD_WIDTH_INCHES) * board_rect.width,
        board_rect.y1 - (y / BOARD_HEIGHT_INCHES) * board_rect.height,
    )
