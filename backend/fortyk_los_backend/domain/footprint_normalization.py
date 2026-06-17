from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol, cast

import fitz
import numpy as np
from numpy.typing import NDArray

from fortyk_los_backend.domain.extraction import (
    BOARD_HEIGHT_INCHES,
    BOARD_WIDTH_INCHES,
    TERRAIN_FILL,
    PdfRect,
    _find_board_rect,
    extract_event_companion_layout,
)
from fortyk_los_backend.domain.models import CanonicalLayout, TerrainFeature
from fortyk_los_backend.domain.visual_sanity import (
    _detect_colored_rect_near,
    _polygon_to_pdf_rect,
    _render_page_rgb,
)

FOOTPRINT_NORMALIZATION_METHOD = "terrain-footprint-normalization-v1"
FOOTPRINT_DIMENSION_TOLERANCE_INCHES = 1.25
FOOTPRINT_DIMENSION_AMBIGUITY_INCHES = 0.25


class FootprintNormalizationStatus(StrEnum):
    PASSED = "passed"
    WARNING = "warning"
    UNAVAILABLE = "unavailable"


class NormalizedFootprintMatchStatus(StrEnum):
    MATCHED = "matched"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class FootprintSizeOption:
    option_id: str
    width_inches: float
    height_inches: float
    count: int
    feature_ids: tuple[str, ...]


@dataclass(frozen=True)
class DetectedFootprintElement:
    element_id: str
    feature_id: str
    bounds_inches: tuple[float, float, float, float]
    width_inches: float
    height_inches: float
    area_square_inches: float


@dataclass(frozen=True)
class FootprintNormalizationMatch:
    feature_id: str
    element_id: str
    option_id: str
    score: float
    width_delta_inches: float
    height_delta_inches: float
    dimension_delta_inches: float
    rotation_degrees: int
    status: NormalizedFootprintMatchStatus
    review_reason: str


@dataclass(frozen=True)
class TerrainFootprintNormalizationReport:
    layout_id: str
    source_document_id: str
    source_page: int
    extraction_method: str
    status: FootprintNormalizationStatus
    options: tuple[FootprintSizeOption, ...]
    detected_elements: tuple[DetectedFootprintElement, ...]
    matches: tuple[FootprintNormalizationMatch, ...]
    warning_codes: tuple[str, ...]


class _DetectedFootprintLike(Protocol):
    feature_id: str
    element_id: str
    width_inches: float
    height_inches: float


def run_terrain_footprint_normalization(
    pdf_path: Path,
    *,
    page_number: int,
    layout: CanonicalLayout | None = None,
) -> TerrainFootprintNormalizationReport:
    extracted_layout = layout or extract_event_companion_layout(pdf_path, page_number=page_number)
    with fitz.open(pdf_path) as document:
        page = document[page_number - 1]
        board_rect = _find_board_rect(list(page.get_drawings()))
        raster = _render_page_rgb(page)

    options = footprint_size_options_from_layout(extracted_layout)
    detected_elements = detect_terrain_footprint_elements(
        raster,
        board_rect,
        extracted_layout,
    )
    matches = match_detected_footprints_to_options(detected_elements, options)
    warning_codes = _normalization_warning_codes(options, detected_elements, matches)
    return TerrainFootprintNormalizationReport(
        layout_id=extracted_layout.layout_id,
        source_document_id=extracted_layout.provenance.source_document_id,
        source_page=page_number,
        extraction_method=FOOTPRINT_NORMALIZATION_METHOD,
        status=(
            FootprintNormalizationStatus.PASSED
            if not warning_codes
            else FootprintNormalizationStatus.WARNING
        ),
        options=options,
        detected_elements=detected_elements,
        matches=matches,
        warning_codes=warning_codes,
    )


def footprint_size_options_from_layout(
    layout: CanonicalLayout,
) -> tuple[FootprintSizeOption, ...]:
    grouped_features: dict[tuple[float, float], list[str]] = {}
    for feature in layout.terrain_features:
        width, height = _canonical_dimensions(_feature_dimensions(feature))
        grouped_features.setdefault((width, height), []).append(feature.feature_id)

    options: list[FootprintSizeOption] = []
    for width, height in sorted(grouped_features):
        feature_ids = tuple(sorted(grouped_features[(width, height)]))
        options.append(
            FootprintSizeOption(
                option_id=f"footprint-size-{_dimension_token(width)}x{_dimension_token(height)}",
                width_inches=width,
                height_inches=height,
                count=len(feature_ids),
                feature_ids=feature_ids,
            )
        )
    return tuple(options)


def detect_terrain_footprint_elements(
    raster: NDArray[np.uint8],
    board_rect: PdfRect,
    layout: CanonicalLayout,
) -> tuple[DetectedFootprintElement, ...]:
    elements: list[DetectedFootprintElement] = []
    for feature in layout.terrain_features:
        expected_rect = _polygon_to_pdf_rect(feature.footprint, board_rect)
        detected_rect = _detect_colored_rect_near(
            raster,
            TERRAIN_FILL,
            expected_rect,
            inflate_pdf=7.0,
            min_pixel_count=20,
        )
        if detected_rect is None:
            continue
        x_min, y_min, x_max, y_max = _pdf_rect_to_board_bounds(detected_rect, board_rect)
        width = round(x_max - x_min, 2)
        height = round(y_max - y_min, 2)
        if width <= 0.0 or height <= 0.0:
            continue
        elements.append(
            DetectedFootprintElement(
                element_id=f"terrain-image-{len(elements) + 1:02d}",
                feature_id=feature.feature_id,
                bounds_inches=(
                    round(x_min, 2),
                    round(y_min, 2),
                    round(x_max, 2),
                    round(y_max, 2),
                ),
                width_inches=width,
                height_inches=height,
                area_square_inches=round(width * height, 2),
            )
        )
    return tuple(elements)


def match_detected_footprints_to_options(
    detected_elements: tuple[DetectedFootprintElement | dict[str, object], ...],
    options: tuple[FootprintSizeOption, ...],
) -> tuple[FootprintNormalizationMatch, ...]:
    if not options:
        return ()

    matches: list[FootprintNormalizationMatch] = []
    for element in detected_elements:
        feature_id, element_id, width, height = _detected_element_fields(element)
        scored_options = sorted(
            (_score_option(width, height, option) for option in options),
            key=lambda candidate: (candidate[0], candidate[3].option_id),
        )
        best = scored_options[0]
        second_delta = scored_options[1][0] if len(scored_options) > 1 else None
        dimension_delta, rotation_degrees, deltas, option = best
        status, review_reason = _match_status(dimension_delta, second_delta)
        matches.append(
            FootprintNormalizationMatch(
                feature_id=feature_id,
                element_id=element_id,
                option_id=option.option_id,
                score=round(
                    max(
                        0.0,
                        1.0
                        - dimension_delta
                        / max(option.width_inches, option.height_inches, 1.0),
                    ),
                    6,
                ),
                width_delta_inches=round(deltas[0], 4),
                height_delta_inches=round(deltas[1], 4),
                dimension_delta_inches=round(dimension_delta, 4),
                rotation_degrees=rotation_degrees,
                status=status,
                review_reason=review_reason,
            )
        )
    return tuple(matches)


def _pdf_rect_to_board_bounds(
    rect: PdfRect,
    board_rect: PdfRect,
) -> tuple[float, float, float, float]:
    x_min = (rect.x0 - board_rect.x0) / board_rect.width * BOARD_WIDTH_INCHES
    x_max = (rect.x1 - board_rect.x0) / board_rect.width * BOARD_WIDTH_INCHES
    y_min = (board_rect.y1 - rect.y1) / board_rect.height * BOARD_HEIGHT_INCHES
    y_max = (board_rect.y1 - rect.y0) / board_rect.height * BOARD_HEIGHT_INCHES
    return x_min, y_min, x_max, y_max


def _feature_dimensions(feature: TerrainFeature) -> tuple[float, float]:
    xs = [point.x for point in feature.footprint.points]
    ys = [point.y for point in feature.footprint.points]
    return round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2)


def _canonical_dimensions(dimensions: tuple[float, float]) -> tuple[float, float]:
    width, height = dimensions
    return (max(width, height), min(width, height))


def _dimension_token(value: float) -> str:
    rounded = int(round(value))
    return f"{rounded:02d}" if rounded < 10 else str(rounded)


def _detected_element_fields(
    element: DetectedFootprintElement | dict[str, object],
) -> tuple[str, str, float, float]:
    if isinstance(element, dict):
        width = element["width_inches"]
        height = element["height_inches"]
        if not isinstance(width, int | float) or not isinstance(height, int | float):
            raise TypeError("detected footprint dimensions must be numeric")
        return (
            str(element.get("feature_id", element["element_id"])),
            str(element["element_id"]),
            float(width),
            float(height),
        )
    typed = cast(_DetectedFootprintLike, element)
    return typed.feature_id, typed.element_id, typed.width_inches, typed.height_inches


def _score_option(
    width: float,
    height: float,
    option: FootprintSizeOption,
) -> tuple[float, int, tuple[float, float], FootprintSizeOption]:
    as_drawn = (abs(width - option.width_inches), abs(height - option.height_inches))
    rotated = (abs(width - option.height_inches), abs(height - option.width_inches))
    as_drawn_delta = max(as_drawn)
    rotated_delta = max(rotated)
    if rotated_delta < as_drawn_delta:
        return rotated_delta, 90, rotated, option
    return as_drawn_delta, 0, as_drawn, option


def _match_status(
    dimension_delta: float,
    second_delta: float | None,
) -> tuple[NormalizedFootprintMatchStatus, str]:
    if dimension_delta > FOOTPRINT_DIMENSION_TOLERANCE_INCHES:
        return (
            NormalizedFootprintMatchStatus.NEEDS_REVIEW,
            "dimension_delta_exceeds_tolerance",
        )
    if (
        second_delta is not None
        and abs(second_delta - dimension_delta) <= FOOTPRINT_DIMENSION_AMBIGUITY_INCHES
    ):
        return NormalizedFootprintMatchStatus.NEEDS_REVIEW, "ambiguous_size_match"
    return NormalizedFootprintMatchStatus.MATCHED, "dimension_match"


def _normalization_warning_codes(
    options: tuple[FootprintSizeOption, ...],
    detected_elements: tuple[DetectedFootprintElement, ...],
    matches: tuple[FootprintNormalizationMatch, ...],
) -> tuple[str, ...]:
    warning_codes: list[str] = []
    expected_count = sum(option.count for option in options)
    if expected_count != len(detected_elements):
        warning_codes.append("terrain_footprint_normalization_count_mismatch")
    if any(match.status != NormalizedFootprintMatchStatus.MATCHED for match in matches):
        warning_codes.append("terrain_footprint_normalization_match_review_required")
    return tuple(warning_codes)
