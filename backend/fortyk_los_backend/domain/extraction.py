from dataclasses import dataclass
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
COLOR_TOLERANCE = 0.035


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


def extract_event_companion_layout(
    pdf_path: Path,
    *,
    page_number: int,
    source_document_id: str = "event-companion-2026-06-12",
) -> CanonicalLayout:
    with fitz.open(pdf_path) as document:
        page = document[page_number - 1]
        drawings = list(page.get_drawings())
        words = list(page.get_text("words"))

    board_rect = _find_board_rect(drawings)
    transform = BoardTransform(board_rect)
    terrain_rects = _find_terrain_rects(drawings, board_rect)
    terrain_features = _terrain_features_from_rects(terrain_rects, transform, words)

    return CanonicalLayout(
        layout_id=f"event-companion-page-{page_number}",
        name=_layout_name(words, fallback=f"Event Companion Page {page_number}"),
        board=Board(width=BOARD_WIDTH_INCHES, height=BOARD_HEIGHT_INCHES),
        terrain_features=terrain_features,
        blockers=_footprint_perimeter_blockers(terrain_features),
        deployments=(
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
        ),
        provenance=LayoutProvenance(
            source_document_id=source_document_id,
            source_page=page_number,
            extraction_method="event-companion-vector-v1",
        ),
        validation_records=(
            ValidationRecord(
                code="event_companion_vector_extraction",
                severity=ValidationSeverity.INFO,
                message=(
                    "Board, deployment zones, and terrain placements extracted from PDF vectors."
                ),
            ),
            ValidationRecord(
                code="footprint_perimeter_los_proxy",
                severity=ValidationSeverity.WARNING,
                message=(
                    "Internal wall enrichment from the terrain footprint sheet is pending; "
                    "LOS blockers currently follow extracted terrain footprint perimeters."
                ),
            ),
        ),
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
) -> tuple[TerrainFeature, ...]:
    features: list[TerrainFeature] = []
    for index, rect in enumerate(terrain_rects, start=1):
        label = _nearest_feature_label(rect, words) or f"Terrain {index:02d}"
        features.append(
            TerrainFeature(
                feature_id=f"terrain-{index:02d}",
                label=label,
                footprint=transform.rect_to_polygon(rect),
            )
        )
    return tuple(features)


def _footprint_perimeter_blockers(
    terrain_features: tuple[TerrainFeature, ...],
) -> tuple[Blocker, ...]:
    blockers: list[Blocker] = []
    for feature in terrain_features:
        points = feature.footprint.points
        for index, (start, end) in enumerate(
            zip(points, (*points[1:], points[0]), strict=True),
            start=1,
        ):
            blockers.append(
                Blocker(
                    blocker_id=f"{feature.feature_id}-perimeter-{index}",
                    feature_id=feature.feature_id,
                    kind=BlockerKind.WALL,
                    start=start,
                    end=end,
                )
            )
    return tuple(blockers)


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
