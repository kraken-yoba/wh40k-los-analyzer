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
    matches = _one_to_one_symmetry_matches(layout)
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


def _one_to_one_symmetry_matches(layout: CanonicalLayout) -> tuple[TerrainSymmetryMatch, ...]:
    features = layout.terrain_features
    if not features:
        return ()

    residuals = {
        (feature.feature_id, candidate.feature_id): _bounds_residual(
            _rotated_bounds(_feature_bounds(feature), layout),
            _feature_bounds(candidate),
        )
        for feature in features
        for candidate in features
        if _features_equivalent_for_symmetry(feature, candidate)
    }
    pair_candidates: list[tuple[float, str, str]] = []
    for first_index, first in enumerate(features):
        for second in features[first_index:]:
            residual = max(
                residuals.get((first.feature_id, second.feature_id), float("inf")),
                residuals.get((second.feature_id, first.feature_id), float("inf")),
            )
            if residual <= SYMMETRY_TOLERANCE_INCHES:
                pair_candidates.append((residual, first.feature_id, second.feature_id))

    assigned = _maximum_symmetry_assignment(
        tuple(feature.feature_id for feature in features),
        tuple(sorted(pair_candidates)),
    )

    matches: list[TerrainSymmetryMatch] = []
    for feature in features:
        assignment = assigned.get(feature.feature_id)
        if assignment is not None:
            mirrored_feature_id, residual = assignment
            matches.append(
                TerrainSymmetryMatch(
                    feature_id=feature.feature_id,
                    mirrored_feature_id=mirrored_feature_id,
                    residual_inches=round(residual, 4),
                    status=TerrainSymmetryMatchStatus.MATCHED,
                )
            )
            continue
        best_feature_id, best_residual = _best_unassigned_candidate(feature, layout, residuals)
        matches.append(
            TerrainSymmetryMatch(
                feature_id=feature.feature_id,
                mirrored_feature_id=best_feature_id,
                residual_inches=round(best_residual, 4),
                status=TerrainSymmetryMatchStatus.UNMATCHED,
            )
        )
    return tuple(matches)


def _maximum_symmetry_assignment(
    feature_ids: tuple[str, ...],
    pair_candidates: tuple[tuple[float, str, str], ...],
) -> dict[str, tuple[str, float]]:
    index_by_feature_id = {
        feature_id: index
        for index, feature_id in enumerate(feature_ids)
    }
    candidates_by_index: dict[int, list[tuple[int, float]]] = {
        index: [] for index in range(len(feature_ids))
    }
    for residual, first_id, second_id in pair_candidates:
        first_index = index_by_feature_id[first_id]
        second_index = index_by_feature_id[second_id]
        candidates_by_index[first_index].append((second_index, residual))
        if second_index != first_index:
            candidates_by_index[second_index].append((first_index, residual))

    memo: dict[int, tuple[int, float, tuple[tuple[int, int, float], ...]]] = {}

    def solve(mask: int) -> tuple[int, float, tuple[tuple[int, int, float], ...]]:
        if mask == (1 << len(feature_ids)) - 1:
            return 0, 0.0, ()
        if mask in memo:
            return memo[mask]

        first_unassigned = next(
            index
            for index in range(len(feature_ids))
            if not mask & (1 << index)
        )
        best = solve(mask | (1 << first_unassigned))
        for partner_index, residual in candidates_by_index[first_unassigned]:
            if mask & (1 << partner_index):
                continue
            next_mask = mask | (1 << first_unassigned) | (1 << partner_index)
            matched_increment = 1 if partner_index == first_unassigned else 2
            matched_count, residual_sum, pairs = solve(next_mask)
            candidate = (
                matched_count + matched_increment,
                residual_sum + residual,
                (
                    (
                        min(first_unassigned, partner_index),
                        max(first_unassigned, partner_index),
                        residual,
                    ),
                    *pairs,
                ),
            )
            if _assignment_score(candidate) > _assignment_score(best):
                best = candidate
        memo[mask] = best
        return best

    _matched_count, _residual_sum, pairs = solve(0)
    assigned: dict[str, tuple[str, float]] = {}
    for first_index, second_index, residual in pairs:
        first_id = feature_ids[first_index]
        second_id = feature_ids[second_index]
        assigned[first_id] = (second_id, residual)
        if second_id != first_id:
            assigned[second_id] = (first_id, residual)
    return assigned


def _assignment_score(
    assignment: tuple[int, float, tuple[tuple[int, int, float], ...]],
) -> tuple[int, float, tuple[tuple[int, int], ...]]:
    matched_count, residual_sum, pairs = assignment
    return (
        matched_count,
        -residual_sum,
        tuple((-first_index, -second_index) for first_index, second_index, _ in pairs),
    )


def _best_unassigned_candidate(
    feature: TerrainFeature,
    layout: CanonicalLayout,
    residuals: dict[tuple[str, str], float],
) -> tuple[str | None, float]:
    candidates = [
        (candidate.feature_id, residuals.get((feature.feature_id, candidate.feature_id)))
        for candidate in layout.terrain_features
    ]
    finite_candidates = [
        (feature_id, residual)
        for feature_id, residual in candidates
        if residual is not None
    ]
    if not finite_candidates:
        return None, float("inf")
    feature_id, residual = min(finite_candidates, key=lambda item: (item[1], item[0]))
    return feature_id, residual


def _features_equivalent_for_symmetry(first: TerrainFeature, second: TerrainFeature) -> bool:
    first_width, first_height = _feature_dimensions(first)
    second_width, second_height = _feature_dimensions(second)
    return (
        first.terrain_category == second.terrain_category
        and abs(max(first_width, first_height) - max(second_width, second_height))
        <= SYMMETRY_TOLERANCE_INCHES
        and abs(min(first_width, first_height) - min(second_width, second_height))
        <= SYMMETRY_TOLERANCE_INCHES
    )


def _feature_dimensions(feature: TerrainFeature) -> tuple[float, float]:
    x_min, y_min, x_max, y_max = _feature_bounds(feature)
    return x_max - x_min, y_max - y_min


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
