import re
from dataclasses import dataclass
from enum import StrEnum
from math import hypot, isfinite, log
from pathlib import Path
from typing import Any

import fitz

from fortyk_los_backend.domain.models import (
    Blocker,
    BlockerKind,
    Board,
    CanonicalLayout,
    DeploymentZone,
    LayoutProvenance,
    Point,
    PolygonGeometry,
    TerrainCategory,
    TerrainFeature,
    ValidationRecord,
    ValidationSeverity,
    ValidationStatus,
)

BOARD_WIDTH_INCHES = 44.0
BOARD_HEIGHT_INCHES = 60.0
BOARD_ASPECT_RATIO = BOARD_WIDTH_INCHES / BOARD_HEIGHT_INCHES
BLACK_STROKE = (0.137, 0.122, 0.125)
ATTACKER_FILL = (0.618, 0.040, 0.056)
DEFENDER_FILL = (0.000, 0.241, 0.408)
TERRAIN_FILL = (0.820, 0.826, 0.832)
TERRAIN_FOOTPRINT_STROKE = (0.000, 0.660, 0.310)
DENSE_TERRAIN_FILLS = ((0.000, 0.452, 0.378),)
LIGHT_TERRAIN_FILLS = ((0.687, 0.253, 0.171),)
COLOR_TOLERANCE = 0.035
# Calibrated against the official terrain footprint PDF: large outline bounds are above
# 80,000 page units, while decorative green marks are tiny line fragments.
MIN_TERRAIN_FOOTPRINT_OUTLINE_AREA = 50_000.0
MIN_TERRAIN_CATEGORY_MARKER_AREA = 100.0
CUBIC_BEZIER_SEGMENTS = 8
FOOTPRINT_MATCH_AMBIGUITY_DELTA = 0.025
FOOTPRINT_MATCH_WEAK_DELTA = 0.25
INCH_ANNOTATION_RE = re.compile(r"^(?P<value>\d+(?:\.\d+)?)\"$")


@dataclass(frozen=True)
class PdfRect:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return self.width * self.height

    def contains(self, other: "PdfRect", *, tolerance: float = 0.0) -> bool:
        return (
            other.x0 >= self.x0 - tolerance
            and other.y0 >= self.y0 - tolerance
            and other.x1 <= self.x1 + tolerance
            and other.y1 <= self.y1 + tolerance
        )

    def inflate(self, amount: float) -> "PdfRect":
        return PdfRect(
            x0=self.x0 - amount,
            y0=self.y0 - amount,
            x1=self.x1 + amount,
            y1=self.y1 + amount,
        )

    def intersection_area(self, other: "PdfRect") -> float:
        x0 = max(self.x0, other.x0)
        y0 = max(self.y0, other.y0)
        x1 = min(self.x1, other.x1)
        y1 = min(self.y1, other.y1)
        if x1 <= x0 or y1 <= y0:
            return 0.0
        return (x1 - x0) * (y1 - y0)

    def iou(self, other: "PdfRect") -> float:
        intersection = self.intersection_area(other)
        union = self.area + other.area - intersection
        if union <= 0:
            return 0.0
        return intersection / union


@dataclass(frozen=True)
class BoardTransform:
    board_rect: PdfRect

    def point_to_board(self, x: float, y: float) -> Point:
        return Point(
            x=_clamp(
                (x - self.board_rect.x0) / self.board_rect.width * BOARD_WIDTH_INCHES,
                low=0.0,
                high=BOARD_WIDTH_INCHES,
            ),
            y=_clamp(
                (self.board_rect.y1 - y) / self.board_rect.height * BOARD_HEIGHT_INCHES,
                low=0.0,
                high=BOARD_HEIGHT_INCHES,
            ),
        )

    def rect_to_polygon(self, rect: PdfRect) -> PolygonGeometry:
        bottom_left = self.point_to_board(rect.x0, rect.y1)
        bottom_right = self.point_to_board(rect.x1, rect.y1)
        top_right = self.point_to_board(rect.x1, rect.y0)
        top_left = self.point_to_board(rect.x0, rect.y0)
        return PolygonGeometry(points=(bottom_left, bottom_right, top_right, top_left))


@dataclass(frozen=True)
class EventCompanionLayoutPage:
    layout_id: str
    name: str
    page_number: int


@dataclass(frozen=True)
class TerrainFootprintOutline:
    footprint_id: str
    page_number: int
    bounds: tuple[float, float, float, float]
    path_command_count: int
    point_count: int


@dataclass(frozen=True)
class TerrainFootprintTemplate:
    template_id: str
    page_number: int
    bounds: tuple[float, float, float, float]
    aspect_ratio: float
    outline_path_command_count: int
    outline_point_count: int
    fragment_count: int
    normalized_outline_points: tuple[Point, ...]
    normalized_fragment_paths: tuple[tuple[Point, ...], ...]


class FootprintMatchStatus(StrEnum):
    CANDIDATE = "candidate"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class TerrainFootprintMatch:
    feature_id: str
    feature_label: str
    template_id: str
    score: float
    aspect_delta: float
    rotation_degrees: int
    status: FootprintMatchStatus
    review_reason: str


def list_event_companion_layout_pages(pdf_path: Path) -> tuple[EventCompanionLayoutPage, ...]:
    pages: list[EventCompanionLayoutPage] = []
    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            words = list(page.get_text("words"))
            name = _layout_name(words, fallback="")
            if not name:
                continue
            try:
                _find_board_rect(list(page.get_drawings()))
            except ValueError:
                continue
            pages.append(
                EventCompanionLayoutPage(
                    layout_id=f"event-companion-page-{page_index}",
                    name=name,
                    page_number=page_index,
                )
            )
    return tuple(pages)


def extract_terrain_footprint_outlines(pdf_path: Path) -> tuple[TerrainFootprintOutline, ...]:
    outlines: list[TerrainFootprintOutline] = []
    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            for outline_index, (_drawing_index, rect, drawing) in enumerate(
                _terrain_footprint_outline_candidates(_green_stroke_drawings(page)),
                start=1,
            ):
                outlines.append(
                    TerrainFootprintOutline(
                        footprint_id=f"terrain-footprint-p{page_index}-{outline_index:02d}",
                        page_number=page_index,
                        bounds=(rect.x0, rect.y0, rect.x1, rect.y1),
                        path_command_count=len(drawing.get("items", ())),
                        point_count=_drawing_point_count(drawing),
                    )
                )
    return tuple(outlines)


def extract_terrain_footprint_templates(pdf_path: Path) -> tuple[TerrainFootprintTemplate, ...]:
    templates: list[TerrainFootprintTemplate] = []
    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            green_drawings = _green_stroke_drawings(page)
            outline_candidates = _terrain_footprint_outline_candidates(green_drawings)
            fragment_assignments = _assign_fragments_to_outlines(green_drawings, outline_candidates)
            for template_index, (_drawing_index, rect, drawing) in enumerate(
                outline_candidates,
                start=1,
            ):
                normalized_fragments = tuple(
                    _normalize_points(_drawing_path_points(fragment_drawing), rect)
                    for _fragment_rect, fragment_drawing in fragment_assignments[template_index - 1]
                )
                templates.append(
                    TerrainFootprintTemplate(
                        template_id=f"terrain-footprint-p{page_index}-{template_index:02d}",
                        page_number=page_index,
                        bounds=(rect.x0, rect.y0, rect.x1, rect.y1),
                        aspect_ratio=rect.width / rect.height,
                        outline_path_command_count=len(drawing.get("items", ())),
                        outline_point_count=_drawing_point_count(drawing),
                        fragment_count=len(normalized_fragments),
                        normalized_outline_points=_normalize_points(
                            _drawing_path_points(drawing),
                            rect,
                        ),
                        normalized_fragment_paths=normalized_fragments,
                    )
                )
    return tuple(templates)


def match_terrain_features_to_footprints(
    layout: CanonicalLayout,
    templates: tuple[TerrainFootprintTemplate, ...],
) -> tuple[TerrainFootprintMatch, ...]:
    return _match_terrain_features_to_footprints(layout.terrain_features, templates)


def generate_terrain_blockers_from_footprint_matches(
    layout: CanonicalLayout,
    templates: tuple[TerrainFootprintTemplate, ...],
    matches: tuple[TerrainFootprintMatch, ...],
) -> tuple[Blocker, ...]:
    return _terrain_blockers_from_footprint_matches(layout.terrain_features, templates, matches)


def extract_event_companion_layout(
    pdf_path: Path,
    *,
    page_number: int,
    source_document_id: str = "event-companion-2026-06-12",
    footprint_templates: tuple[TerrainFootprintTemplate, ...] = (),
) -> CanonicalLayout:
    with fitz.open(pdf_path) as document:
        page = document[page_number - 1]
        drawings = list(page.get_drawings())
        words = list(page.get_text("words"))

    board_rect = _find_board_rect(drawings)
    transform = BoardTransform(board_rect)
    terrain_rects = _find_terrain_rects(drawings, board_rect)
    terrain_features = _terrain_features_from_rects(terrain_rects, transform, words, drawings)
    deployments = (
        _deployment_zone(
            drawings,
            board_rect,
            transform,
            fill=ATTACKER_FILL,
            zone_id="attacker",
            label="Attacker",
        ),
        _deployment_zone(
            drawings,
            board_rect,
            transform,
            fill=DEFENDER_FILL,
            zone_id="defender",
            label="Defender",
        ),
    )
    footprint_matches = _match_terrain_features_to_footprints(
        terrain_features,
        footprint_templates,
    )
    blockers = _terrain_blockers_from_footprint_matches(
        terrain_features,
        footprint_templates,
        footprint_matches,
    )
    validation_records = _validation_records(
        terrain_features,
        deployments,
        words,
        footprint_matches,
        len(blockers),
    )

    return CanonicalLayout(
        layout_id=f"event-companion-page-{page_number}",
        name=_layout_name(words, fallback=f"Event Companion Page {page_number}"),
        board=Board(width=BOARD_WIDTH_INCHES, height=BOARD_HEIGHT_INCHES),
        terrain_features=terrain_features,
        blockers=blockers,
        deployments=deployments,
        provenance=LayoutProvenance(
            source_document_id=source_document_id,
            source_page=page_number,
            extraction_method="event-companion-vector-v1",
        ),
        validation_records=validation_records,
        validation_status=ValidationStatus.WARNING,
    )


def _find_board_rect(drawings: list[dict[str, Any]]) -> PdfRect:
    candidates: list[PdfRect] = []
    for drawing in drawings:
        if drawing.get("type") != "s" or not _color_matches(drawing.get("color"), BLACK_STROKE):
            continue
        rect = _pdf_rect(drawing["rect"])
        if rect.area < 50_000:
            continue
        aspect_ratio = rect.width / rect.height
        if abs(aspect_ratio - BOARD_ASPECT_RATIO) <= 0.035:
            candidates.append(rect)
    if not candidates:
        raise ValueError("Event Companion layout board rectangle not found")
    return max(candidates, key=lambda rect: rect.area)


def _deployment_zone(
    drawings: list[dict[str, Any]],
    board_rect: PdfRect,
    transform: BoardTransform,
    *,
    fill: tuple[float, float, float],
    zone_id: str,
    label: str,
) -> DeploymentZone:
    board_area = board_rect.area
    candidates = [
        _pdf_rect(drawing["rect"])
        for drawing in drawings
        if drawing.get("type") in {"f", "fs"}
        and _color_matches(drawing.get("fill"), fill)
        and board_rect.contains(_pdf_rect(drawing["rect"]), tolerance=2.0)
        and _pdf_rect(drawing["rect"]).area >= board_area * 0.1
    ]
    if not candidates:
        raise ValueError(f"{label} deployment zone not found")
    return DeploymentZone(
        zone_id=zone_id,
        label=label,
        area=transform.rect_to_polygon(max(candidates, key=lambda rect: rect.area)),
    )


def _find_terrain_rects(drawings: list[dict[str, Any]], board_rect: PdfRect) -> tuple[PdfRect, ...]:
    candidates = [
        _pdf_rect(drawing["rect"])
        for drawing in drawings
        if drawing.get("type") == "fs"
        and _color_matches(drawing.get("fill"), TERRAIN_FILL)
        and _color_matches(drawing.get("color"), BLACK_STROKE)
        and board_rect.contains(_pdf_rect(drawing["rect"]), tolerance=1.0)
        and 700 <= _pdf_rect(drawing["rect"]).area <= board_rect.area * 0.08
    ]
    return tuple(
        sorted(_dedupe_rects(candidates), key=lambda rect: (rect.y0, rect.x0, rect.y1, rect.x1))
    )


def _terrain_features_from_rects(
    terrain_rects: tuple[PdfRect, ...],
    transform: BoardTransform,
    words: list[tuple[Any, ...]],
    drawings: list[dict[str, Any]] | None = None,
) -> tuple[TerrainFeature, ...]:
    features: list[TerrainFeature] = []
    terrain_categories = _terrain_categories_from_drawings(terrain_rects, drawings or [])
    for index, rect in enumerate(terrain_rects, start=1):
        label = _nearest_feature_label(rect, words) or f"Terrain {index:02d}"
        features.append(
            TerrainFeature(
                feature_id=f"terrain-{index:02d}",
                label=label,
                footprint=transform.rect_to_polygon(rect),
                terrain_category=terrain_categories[index - 1],
            )
        )
    return tuple(features)


def _terrain_categories_from_drawings(
    terrain_rects: tuple[PdfRect, ...],
    drawings: list[dict[str, Any]],
) -> tuple[TerrainCategory, ...]:
    return tuple(
        _terrain_category_from_drawings(terrain_rect, drawings) for terrain_rect in terrain_rects
    )


def _terrain_category_from_drawings(
    terrain_rect: PdfRect,
    drawings: list[dict[str, Any]],
) -> TerrainCategory:
    has_dense_marker = False
    has_light_marker = False
    for drawing in drawings:
        if "rect" not in drawing:
            continue
        marker_rect = _pdf_rect(drawing["rect"])
        if marker_rect.area < MIN_TERRAIN_CATEGORY_MARKER_AREA:
            continue
        if not _marker_overlaps_terrain_rect(marker_rect, terrain_rect):
            continue
        fill = drawing.get("fill")
        if any(_color_matches(fill, dense_fill) for dense_fill in DENSE_TERRAIN_FILLS):
            has_dense_marker = True
        if any(_color_matches(fill, light_fill) for light_fill in LIGHT_TERRAIN_FILLS):
            has_light_marker = True
    if has_dense_marker:
        return TerrainCategory.DENSE
    if has_light_marker:
        return TerrainCategory.LIGHT
    return TerrainCategory.UNKNOWN


def _marker_overlaps_terrain_rect(marker_rect: PdfRect, terrain_rect: PdfRect) -> bool:
    if terrain_rect.contains(marker_rect, tolerance=2.0):
        return True
    return terrain_rect.intersection_area(marker_rect) >= marker_rect.area * 0.2


def _layout_name(words: list[tuple[Any, ...]], *, fallback: str) -> str:
    for index, word in enumerate(words):
        text = str(word[4]).upper()
        if text == "LAYOUT" and index + 1 < len(words):
            next_word = str(words[index + 1][4]).upper()
            if len(next_word) == 1 and next_word.isalpha():
                return f"Layout {next_word}"
    return fallback


def _nearest_feature_label(rect: PdfRect, words: list[tuple[Any, ...]]) -> str | None:
    search_rect = rect.inflate(8.0)
    labels: list[str] = []
    for word in words:
        x0, y0, x1, y1, text = word[:5]
        if str(text) not in {"AB", "CD", "EF", "GH"}:
            continue
        center_x = (float(x0) + float(x1)) / 2
        center_y = (float(y0) + float(y1)) / 2
        inside_label_region = (
            search_rect.x0 <= center_x <= search_rect.x1
            and search_rect.y0 <= center_y <= search_rect.y1
        )
        if inside_label_region:
            labels.append(str(text))
    return "/".join(sorted(set(labels))) if labels else None


def _dedupe_rects(rects: list[PdfRect]) -> list[PdfRect]:
    kept: list[PdfRect] = []
    for rect in sorted(rects, key=lambda candidate: candidate.area, reverse=True):
        if all(rect.iou(existing) < 0.85 for existing in kept):
            kept.append(rect)
    return kept


def _validation_records(
    terrain_features: tuple[TerrainFeature, ...],
    deployments: tuple[DeploymentZone, ...],
    words: list[tuple[Any, ...]],
    footprint_matches: tuple[TerrainFootprintMatch, ...],
    blocker_count: int,
) -> tuple[ValidationRecord, ...]:
    records: list[ValidationRecord] = [
        ValidationRecord(
            code="event_companion_vector_extraction",
            severity=ValidationSeverity.INFO,
            message="Board, deployment zones, and terrain placements extracted from PDF vectors.",
        ),
        ValidationRecord(
            code="placement_proxy_not_los_ready",
            severity=ValidationSeverity.WARNING,
            message=(
                "Extracted terrain polygons are placement proxies from the Event Companion map; "
                "official footprint outlines and internal walls are not yet validated, so LOS "
                "analysis must remain blocked for this layout."
            ),
        ),
        ValidationRecord(
            code="terrain_measurement_crosscheck_pending",
            severity=ValidationSeverity.WARNING,
            message=(
                "Printed terrain offset annotations are not fully cross-checked against extracted "
                "terrain placement coordinates yet."
            ),
        ),
    ]

    inch_annotations = _inch_annotations(words)
    deployment_depths = tuple(_deployment_depth(deployment) for deployment in deployments)
    if all(_has_matching_annotation(depth, inch_annotations) for depth in deployment_depths):
        records.append(
            ValidationRecord(
                code="deployment_depth_measurement_crosscheck",
                severity=ValidationSeverity.INFO,
                message="Deployment-zone depths match printed inch annotations within tolerance.",
            )
        )
    else:
        records.append(
            ValidationRecord(
                code="deployment_depth_measurement_crosscheck_failed",
                severity=ValidationSeverity.WARNING,
                message="Deployment-zone depths did not match printed inch annotations.",
            )
        )

    low_confidence_labels = [
        feature.label
        for feature in terrain_features
        if feature.label.startswith("Terrain ") or "/" in feature.label
    ]
    if low_confidence_labels:
        records.append(
            ValidationRecord(
                code="terrain_label_review_required",
                severity=ValidationSeverity.WARNING,
                message=(
                    f"{len(low_confidence_labels)} terrain labels are fallback or ambiguous and "
                    "require review before relying on feature labels."
                ),
            )
        )
    records.extend(_footprint_match_validation_records(footprint_matches))
    records.extend(_footprint_blocker_validation_records(blocker_count))
    return tuple(records)


def _inch_annotations(words: list[tuple[Any, ...]]) -> tuple[float, ...]:
    annotations: list[float] = []
    for word in words:
        match = INCH_ANNOTATION_RE.match(str(word[4]))
        if match is not None:
            annotations.append(float(match.group("value")))
    return tuple(annotations)


def _deployment_depth(deployment: DeploymentZone) -> float:
    y_values = [point.y for point in deployment.area.points]
    return max(y_values) - min(y_values)


def _has_matching_annotation(value: float, annotations: tuple[float, ...]) -> bool:
    return any(abs(value - annotation) <= 0.25 for annotation in annotations)


def _footprint_match_validation_records(
    footprint_matches: tuple[TerrainFootprintMatch, ...],
) -> list[ValidationRecord]:
    if not footprint_matches:
        return []
    return [
        ValidationRecord(
            code="terrain_footprint_match_candidates",
            severity=ValidationSeverity.INFO,
            message=(
                f"Generated {len(footprint_matches)} provisional terrain-footprint template "
                "matches from deterministic geometry signals."
            ),
        ),
        ValidationRecord(
            code="terrain_footprint_match_review_required",
            severity=ValidationSeverity.WARNING,
            message=(
                "Terrain-footprint template matches are provisional evidence and require "
                "review before accepting LOS blocker placement or wall semantics."
            ),
        ),
    ]


def _footprint_blocker_validation_records(blocker_count: int) -> list[ValidationRecord]:
    if blocker_count <= 0:
        return []
    return [
        ValidationRecord(
            code="terrain_footprint_blocker_candidates",
            severity=ValidationSeverity.INFO,
            message=(
                f"Generated {blocker_count} provisional Dense/Solid wall segments from matched "
                "official terrain-footprint fragments."
            ),
        ),
        ValidationRecord(
            code="terrain_footprint_blocker_review_required",
            severity=ValidationSeverity.WARNING,
            message=(
                "Dense terrain-footprint wall segments are deterministic provisional geometry "
                "and require review before enabling official-layout LOS analysis."
            ),
        ),
    ]


def _match_terrain_features_to_footprints(
    terrain_features: tuple[TerrainFeature, ...],
    templates: tuple[TerrainFootprintTemplate, ...],
) -> tuple[TerrainFootprintMatch, ...]:
    valid_templates = tuple(
        template for template in templates if _is_valid_template_aspect(template.aspect_ratio)
    )
    if not valid_templates:
        return ()
    matches: list[TerrainFootprintMatch] = []
    for feature in terrain_features:
        feature_aspect_ratio = _feature_aspect_ratio(feature)
        scored_templates = sorted(
            (
                (*_template_aspect_score(feature_aspect_ratio, template), template)
                for template in valid_templates
            ),
            key=lambda scored: (scored[0], scored[1], scored[2].template_id),
        )
        best_delta, rotation_degrees, best_template = scored_templates[0]
        second_delta = scored_templates[1][0] if len(scored_templates) > 1 else None
        status, review_reason = _footprint_match_status(feature, best_delta, second_delta)
        matches.append(
            TerrainFootprintMatch(
                feature_id=feature.feature_id,
                feature_label=feature.label,
                template_id=best_template.template_id,
                score=round(max(0.0, 1.0 - best_delta), 6),
                aspect_delta=round(best_delta, 6),
                rotation_degrees=rotation_degrees,
                status=status,
                review_reason=review_reason,
            )
        )
    return tuple(matches)


def _terrain_blockers_from_footprint_matches(
    terrain_features: tuple[TerrainFeature, ...],
    templates: tuple[TerrainFootprintTemplate, ...],
    matches: tuple[TerrainFootprintMatch, ...],
) -> tuple[Blocker, ...]:
    feature_by_id = {feature.feature_id: feature for feature in terrain_features}
    template_by_id = {template.template_id: template for template in templates}
    blockers: list[Blocker] = []
    for match in matches:
        feature = feature_by_id.get(match.feature_id)
        template = template_by_id.get(match.template_id)
        if feature is None or template is None:
            continue
        if feature.terrain_category != TerrainCategory.DENSE:
            continue
        feature_bounds = _feature_bounds(feature)
        for fragment_index, fragment_path in enumerate(template.normalized_fragment_paths, start=1):
            transformed_path = tuple(
                _template_point_to_feature(point, feature_bounds, match.rotation_degrees)
                for point in fragment_path
            )
            for segment_index, (start, end) in enumerate(
                zip(transformed_path, transformed_path[1:], strict=False),
                start=1,
            ):
                if _point_distance(start, end) <= 1e-6:
                    continue
                blockers.append(
                    Blocker(
                        blocker_id=(
                            f"{feature.feature_id}-footprint-wall-"
                            f"{fragment_index:02d}-{segment_index:02d}"
                        ),
                        feature_id=feature.feature_id,
                        kind=BlockerKind.WALL,
                        start=start,
                        end=end,
                    )
                )
    return tuple(blockers)


def _footprint_match_status(
    feature: TerrainFeature,
    best_delta: float,
    second_delta: float | None,
) -> tuple[FootprintMatchStatus, str]:
    if (
        second_delta is not None
        and abs(second_delta - best_delta) <= FOOTPRINT_MATCH_AMBIGUITY_DELTA
    ):
        return FootprintMatchStatus.NEEDS_REVIEW, "ambiguous_template_score"
    if best_delta > FOOTPRINT_MATCH_WEAK_DELTA:
        return FootprintMatchStatus.NEEDS_REVIEW, "weak_aspect_match"
    if feature.label.startswith("Terrain ") or "/" in feature.label:
        return FootprintMatchStatus.NEEDS_REVIEW, "low_confidence_feature_label"
    return FootprintMatchStatus.CANDIDATE, "best_aspect_match"


def _feature_aspect_ratio(feature: TerrainFeature) -> float:
    x_min, y_min, x_max, y_max = _feature_bounds(feature)
    return (x_max - x_min) / (y_max - y_min)


def _feature_bounds(feature: TerrainFeature) -> tuple[float, float, float, float]:
    xs = [point.x for point in feature.footprint.points]
    ys = [point.y for point in feature.footprint.points]
    return min(xs), min(ys), max(xs), max(ys)


def _template_aspect_score(
    feature_aspect_ratio: float,
    template: TerrainFootprintTemplate,
) -> tuple[float, int]:
    template_aspect_ratio = template.aspect_ratio
    as_drawn_delta = abs(log(feature_aspect_ratio / template_aspect_ratio))
    rotated_delta = abs(log(feature_aspect_ratio / (1.0 / template_aspect_ratio)))
    if rotated_delta < as_drawn_delta:
        return rotated_delta, 90
    return as_drawn_delta, 0


def _template_point_to_feature(
    point: Point,
    bounds: tuple[float, float, float, float],
    rotation_degrees: int,
) -> Point:
    x_min, y_min, x_max, y_max = bounds
    width = x_max - x_min
    height = y_max - y_min
    oriented_point = _orient_template_point(point, rotation_degrees)
    x = round(x_min + oriented_point.x * width, 4)
    y = round(y_max - oriented_point.y * height, 4)
    return Point(
        x=_clamp(x, low=x_min, high=x_max),
        y=_clamp(y, low=y_min, high=y_max),
    )


def _orient_template_point(point: Point, rotation_degrees: int) -> Point:
    if rotation_degrees == 90:
        return Point(
            x=_clamp(point.y, low=0.0, high=1.0),
            y=_clamp(1.0 - point.x, low=0.0, high=1.0),
        )
    return Point(
        x=_clamp(point.x, low=0.0, high=1.0),
        y=_clamp(point.y, low=0.0, high=1.0),
    )


def _point_distance(start: Point, end: Point) -> float:
    return hypot(end.x - start.x, end.y - start.y)


def _is_valid_template_aspect(aspect_ratio: float) -> bool:
    return isfinite(aspect_ratio) and aspect_ratio > 0.0


def _green_stroke_drawings(page: Any) -> list[tuple[int, PdfRect, dict[str, Any]]]:
    green_drawings: list[tuple[int, PdfRect, dict[str, Any]]] = []
    for drawing_index, drawing in enumerate(page.get_drawings()):
        if drawing.get("type") != "s":
            continue
        if not _color_matches(drawing.get("color"), TERRAIN_FOOTPRINT_STROKE):
            continue
        green_drawings.append((drawing_index, _pdf_rect(drawing["rect"]), drawing))
    return green_drawings


def _terrain_footprint_outline_candidates(
    green_drawings: list[tuple[int, PdfRect, dict[str, Any]]],
) -> list[tuple[int, PdfRect, dict[str, Any]]]:
    return sorted(
        [
            (drawing_index, rect, drawing)
            for drawing_index, rect, drawing in green_drawings
            if rect.area >= MIN_TERRAIN_FOOTPRINT_OUTLINE_AREA
            and len(drawing.get("items", ())) >= 1
        ],
        key=_terrain_footprint_candidate_sort_key,
    )


def _terrain_footprint_candidate_sort_key(
    candidate: tuple[int, PdfRect, dict[str, Any]],
) -> tuple[float, float, float, float, int, int, int]:
    drawing_index, rect, drawing = candidate
    return (
        rect.y0,
        rect.x0,
        rect.y1,
        rect.x1,
        len(drawing.get("items", ())),
        _drawing_point_count(drawing),
        drawing_index,
    )


def _assign_fragments_to_outlines(
    green_drawings: list[tuple[int, PdfRect, dict[str, Any]]],
    outline_candidates: list[tuple[int, PdfRect, dict[str, Any]]],
) -> tuple[tuple[tuple[PdfRect, dict[str, Any]], ...], ...]:
    outline_indexes = {drawing_index for drawing_index, _rect, _drawing in outline_candidates}
    assignments: list[list[tuple[PdfRect, dict[str, Any]]]] = [
        [] for _outline in outline_candidates
    ]
    for drawing_index, rect, drawing in green_drawings:
        if drawing_index in outline_indexes:
            continue
        containing_outlines: list[tuple[float, int]] = []
        center_x = (rect.x0 + rect.x1) / 2.0
        center_y = (rect.y0 + rect.y1) / 2.0
        for outline_index, (_outline_drawing_index, outline_rect, _outline_drawing) in enumerate(
            outline_candidates
        ):
            inflated_outline = outline_rect.inflate(2.0)
            if (
                _rect_contains_point(inflated_outline, center_x, center_y)
                and _fragment_fully_contained(rect, drawing, inflated_outline)
            ):
                containing_outlines.append((outline_rect.area, outline_index))
        if containing_outlines:
            _area, outline_index = min(containing_outlines)
            assignments[outline_index].append((rect, drawing))
    return tuple(
        tuple(sorted(assignment, key=lambda item: (item[0].y0, item[0].x0, item[0].y1, item[0].x1)))
        for assignment in assignments
    )


def _rect_contains_point(rect: PdfRect, x: float, y: float) -> bool:
    return rect.x0 <= x <= rect.x1 and rect.y0 <= y <= rect.y1


def _fragment_fully_contained(
    fragment_rect: PdfRect,
    fragment_drawing: dict[str, Any],
    outline_rect: PdfRect,
) -> bool:
    if not outline_rect.contains(fragment_rect):
        return False
    return all(
        _rect_contains_point(outline_rect, x, y) for x, y in _drawing_path_points(fragment_drawing)
    )


def _normalize_points(
    points: tuple[tuple[float, float], ...],
    bounds: PdfRect,
) -> tuple[Point, ...]:
    return tuple(
        Point(
            x=_clamp((x - bounds.x0) / bounds.width, low=0.0, high=1.0),
            y=_clamp((y - bounds.y0) / bounds.height, low=0.0, high=1.0),
        )
        for x, y in points
    )


def _drawing_point_count(drawing: dict[str, Any]) -> int:
    return len(set(_drawing_path_points(drawing)))


def _drawing_path_points(drawing: dict[str, Any]) -> tuple[tuple[float, float], ...]:
    ordered_points: list[tuple[float, float]] = []
    for item in drawing.get("items", ()):
        if item[0] == "c":
            ordered_points.extend(_cubic_bezier_points(item[1:]))
            continue
        for value in item[1:]:
            ordered_points.extend(_pdf_points(value))
    return tuple(ordered_points)


def _cubic_bezier_points(values: tuple[Any, ...]) -> tuple[tuple[float, float], ...]:
    flattened_points = tuple(point for value in values for point in _pdf_points(value))
    if len(flattened_points) != 4:
        return flattened_points
    p0, p1, p2, p3 = flattened_points
    points: list[tuple[float, float]] = []
    for step in range(CUBIC_BEZIER_SEGMENTS + 1):
        t = step / CUBIC_BEZIER_SEGMENTS
        points.append(
            (
                _rounded_coordinate(_cubic_bezier_coordinate(p0[0], p1[0], p2[0], p3[0], t)),
                _rounded_coordinate(_cubic_bezier_coordinate(p0[1], p1[1], p2[1], p3[1], t)),
            )
        )
    return tuple(points)


def _cubic_bezier_coordinate(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    inverse_t = 1.0 - t
    return (
        inverse_t**3 * p0
        + 3.0 * inverse_t**2 * t * p1
        + 3.0 * inverse_t * t**2 * p2
        + t**3 * p3
    )


def _pdf_points(value: Any) -> tuple[tuple[float, float], ...]:
    if hasattr(value, "x") and hasattr(value, "y"):
        return ((_rounded_coordinate(value.x), _rounded_coordinate(value.y)),)
    if all(hasattr(value, attribute) for attribute in ("ul", "ur", "ll", "lr")):
        return (
            (_rounded_coordinate(value.ul.x), _rounded_coordinate(value.ul.y)),
            (_rounded_coordinate(value.ur.x), _rounded_coordinate(value.ur.y)),
            (_rounded_coordinate(value.ll.x), _rounded_coordinate(value.ll.y)),
            (_rounded_coordinate(value.lr.x), _rounded_coordinate(value.lr.y)),
        )
    if all(hasattr(value, attribute) for attribute in ("x0", "y0", "x1", "y1")):
        return (
            (_rounded_coordinate(value.x0), _rounded_coordinate(value.y0)),
            (_rounded_coordinate(value.x1), _rounded_coordinate(value.y0)),
            (_rounded_coordinate(value.x1), _rounded_coordinate(value.y1)),
            (_rounded_coordinate(value.x0), _rounded_coordinate(value.y1)),
        )
    return ()


def _rounded_coordinate(value: Any) -> float:
    return round(float(value), 3)


def _pdf_rect(rect: Any) -> PdfRect:
    return PdfRect(x0=float(rect.x0), y0=float(rect.y0), x1=float(rect.x1), y1=float(rect.y1))


def _color_matches(
    color: tuple[float, float, float] | None,
    expected: tuple[float, float, float],
) -> bool:
    if color is None or len(color) != len(expected):
        return False
    return all(
        abs(component - expected_component) <= COLOR_TOLERANCE
        for component, expected_component in zip(color, expected, strict=True)
    )


def _clamp(value: float, *, low: float, high: float) -> float:
    return min(max(value, low), high)
