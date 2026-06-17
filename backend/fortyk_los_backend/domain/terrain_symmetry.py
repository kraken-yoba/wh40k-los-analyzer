from dataclasses import dataclass
from enum import StrEnum

from fortyk_los_backend.domain.models import CanonicalLayout, TerrainFeature

TERRAIN_SYMMETRY_METHOD = "terrain-symmetry-v1"
SYMMETRY_TOLERANCE_INCHES = 1.25


class TerrainSymmetryStatus(StrEnum):
    PASSED = "passed"
    WARNING = "warning"


class TerrainSymmetryMatchStatus(StrEnum):
    MATCHED = "matched"
    UNMATCHED = "unmatched"


@dataclass(frozen=True)
class TerrainSymmetryMatch:
    feature_id: str
    mirrored_feature_id: str | None
    residual_inches: float
    status: TerrainSymmetryMatchStatus


@dataclass(frozen=True)
class TerrainSymmetryReport:
    layout_id: str
    source_document_id: str
    source_page: int
    extraction_method: str
    symmetry_kind: str
    status: TerrainSymmetryStatus
    feature_count: int
    matched_feature_count: int
    max_residual_inches: float | None
    unmatched_feature_ids: tuple[str, ...]
    matches: tuple[TerrainSymmetryMatch, ...]


def analyze_terrain_symmetry(layout: CanonicalLayout) -> TerrainSymmetryReport:
    matches = tuple(_feature_symmetry_match(feature, layout) for feature in layout.terrain_features)
    unmatched_feature_ids = tuple(
        match.feature_id
        for match in matches
        if match.status == TerrainSymmetryMatchStatus.UNMATCHED
    )
    max_residual = max((match.residual_inches for match in matches), default=None)
    return TerrainSymmetryReport(
        layout_id=layout.layout_id,
        source_document_id=layout.provenance.source_document_id,
        source_page=layout.provenance.source_page,
        extraction_method=TERRAIN_SYMMETRY_METHOD,
        symmetry_kind="rotational_180",
        status=(
            TerrainSymmetryStatus.PASSED
            if not unmatched_feature_ids
            else TerrainSymmetryStatus.WARNING
        ),
        feature_count=len(layout.terrain_features),
        matched_feature_count=len(layout.terrain_features) - len(unmatched_feature_ids),
        max_residual_inches=round(max_residual, 4) if max_residual is not None else None,
        unmatched_feature_ids=unmatched_feature_ids,
        matches=matches,
    )


def _feature_symmetry_match(
    feature: TerrainFeature,
    layout: CanonicalLayout,
) -> TerrainSymmetryMatch:
    mirrored_bounds = _rotated_bounds(_feature_bounds(feature), layout)
    candidates = [
        candidate
        for candidate in layout.terrain_features
        if candidate.feature_id != feature.feature_id or len(layout.terrain_features) == 1
    ]
    if not candidates:
        return TerrainSymmetryMatch(
            feature_id=feature.feature_id,
            mirrored_feature_id=None,
            residual_inches=float("inf"),
            status=TerrainSymmetryMatchStatus.UNMATCHED,
        )
    best_feature, best_residual = min(
        (
            (
                candidate,
                _bounds_residual(mirrored_bounds, _feature_bounds(candidate)),
            )
            for candidate in candidates
        ),
        key=lambda item: (item[1], item[0].feature_id),
    )
    status = (
        TerrainSymmetryMatchStatus.MATCHED
        if best_residual <= SYMMETRY_TOLERANCE_INCHES
        else TerrainSymmetryMatchStatus.UNMATCHED
    )
    return TerrainSymmetryMatch(
        feature_id=feature.feature_id,
        mirrored_feature_id=best_feature.feature_id,
        residual_inches=round(best_residual, 4),
        status=status,
    )


def _feature_bounds(feature: TerrainFeature) -> tuple[float, float, float, float]:
    xs = [point.x for point in feature.footprint.points]
    ys = [point.y for point in feature.footprint.points]
    return min(xs), min(ys), max(xs), max(ys)


def _rotated_bounds(
    bounds: tuple[float, float, float, float],
    layout: CanonicalLayout,
) -> tuple[float, float, float, float]:
    x_min, y_min, x_max, y_max = bounds
    return (
        layout.board.width - x_max,
        layout.board.height - y_max,
        layout.board.width - x_min,
        layout.board.height - y_min,
    )


def _bounds_residual(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    return max(
        abs(first_value - second_value)
        for first_value, second_value in zip(first, second, strict=True)
    )
