from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Any

from shapely.geometry import box

from fortyk_los_backend.domain.footprint_normalization import (
    FootprintSizeOption,
    footprint_size_options_from_layout,
)
from fortyk_los_backend.domain.models import CanonicalLayout, TerrainFeature
from fortyk_los_backend.domain.terrain_symmetry import (
    TerrainSymmetryMatch,
    TerrainSymmetryMatchStatus,
    TerrainSymmetryStatus,
    analyze_terrain_symmetry,
)

TERRAIN_RECONCILIATION_METHOD = "terrain-reconciliation-v1"
MEASUREMENT_TOLERANCE_INCHES = 0.25
MEASUREMENT_POSITION_TOLERANCE_INCHES = 2.0
GRID_TOLERANCE_INCHES = 1e-6
PROCESS_STEPS = (
    "standard_terrain_options",
    "image_extraction",
    "grid_snap",
    "measurement_corner_check",
    "symmetry_candidate_check",
    "final_reconciliation",
)


class TerrainReconciliationStatus(StrEnum):
    PASSED = "passed"
    PASSED_WITH_ALTERNATIVES = "passed_with_alternatives"
    WARNING = "warning"


class ReconciliationCheckStatus(StrEnum):
    PASSED = "passed"
    WARNING = "warning"
    UNAVAILABLE = "unavailable"


class ReconciliationAlternativeStatus(StrEnum):
    VIABLE = "viable"
    REJECTED = "rejected"


@dataclass(frozen=True)
class MeasurementAnnotation:
    value: float
    x: float
    y: float


@dataclass(frozen=True)
class SourceFootprintDimension:
    template_id: str
    width_inches: float
    height_inches: float
    evidence_count: int


@dataclass(frozen=True)
class StandardTerrainFootprintOption:
    option_id: str
    width_inches: float
    height_inches: float
    count: int
    dense_feature_count: int
    wall_segment_count: int
    feature_ids: tuple[str, ...]
    template_ids: tuple[str, ...] = ()
    dimension_evidence_count: int = 0
    source_kind: str = "layout_geometry"


@dataclass(frozen=True)
class FeatureMeasurementCheck:
    feature_id: str
    bounds_inches: tuple[float, float, float, float]
    edge_offsets_inches: tuple[float, float, float, float]
    matched_offsets_inches: tuple[float, ...]
    verified_corner_count: int
    status: ReconciliationCheckStatus
    review_reason: str


@dataclass(frozen=True)
class TerrainReconciliationAlternative:
    feature_id: str
    alternative_kind: str
    option_id: str | None
    proposed_bounds_inches: tuple[float, float, float, float]
    measurement_status: ReconciliationCheckStatus
    symmetry_residual_inches: float
    overlap_feature_ids: tuple[str, ...]
    status: ReconciliationAlternativeStatus
    review_reason: str


@dataclass(frozen=True)
class TerrainReconciliationReport:
    layout_id: str
    source_document_id: str
    source_page: int
    extraction_method: str
    status: TerrainReconciliationStatus
    measurement_status: ReconciliationCheckStatus
    symmetry_status: TerrainSymmetryStatus
    final_measurement_status: ReconciliationCheckStatus
    final_symmetry_status: TerrainSymmetryStatus
    standard_options: tuple[StandardTerrainFootprintOption, ...]
    measurement_checks: tuple[FeatureMeasurementCheck, ...]
    symmetry_matches: tuple[TerrainSymmetryMatch, ...]
    alternatives: tuple[TerrainReconciliationAlternative, ...]
    viable_alternative_count: int
    unresolved_feature_ids: tuple[str, ...]
    warning_codes: tuple[str, ...]
    process_steps: tuple[str, ...] = PROCESS_STEPS


def reconcile_terrain_layout(
    layout: CanonicalLayout,
    *,
    measurements: tuple[MeasurementAnnotation, ...] = (),
    standard_options: tuple[StandardTerrainFootprintOption, ...] | None = None,
) -> TerrainReconciliationReport:
    options = standard_options or standard_terrain_options_from_layout(layout)
    measurement_checks = tuple(
        _measurement_check(feature, layout, measurements)
        for feature in layout.terrain_features
    )
    measurement_status = _measurement_status(measurement_checks)
    symmetry_report = analyze_terrain_symmetry(layout)
    alternatives = tuple(
        _best_alternative_for_match(match, layout, measurements, options)
        for match in symmetry_report.matches
        if match.status == TerrainSymmetryMatchStatus.UNMATCHED
    )
    viable_alternative_feature_ids = {
        feature_id
        for alternative in alternatives
        if alternative.status == ReconciliationAlternativeStatus.VIABLE
        for feature_id in _resolved_feature_ids(alternative)
    }
    viable_alternative_count = sum(
        1
        for alternative in alternatives
        if alternative.status == ReconciliationAlternativeStatus.VIABLE
    )
    unresolved_feature_ids = tuple(
        match.feature_id
        for match in symmetry_report.matches
        if match.status == TerrainSymmetryMatchStatus.UNMATCHED
        and match.feature_id not in viable_alternative_feature_ids
    )
    final_measurement_status = _final_measurement_status(
        measurement_checks,
        alternatives,
    )
    final_symmetry_status = (
        TerrainSymmetryStatus.PASSED
        if symmetry_report.status == TerrainSymmetryStatus.PASSED or not unresolved_feature_ids
        else TerrainSymmetryStatus.WARNING
    )
    warning_codes = _warning_codes(
        final_measurement_status=final_measurement_status,
        final_symmetry_status=final_symmetry_status,
        unresolved_feature_ids=unresolved_feature_ids,
    )
    return TerrainReconciliationReport(
        layout_id=layout.layout_id,
        source_document_id=layout.provenance.source_document_id,
        source_page=layout.provenance.source_page,
        extraction_method=TERRAIN_RECONCILIATION_METHOD,
        status=_reconciliation_status(
            raw_measurement_status=measurement_status,
            raw_symmetry_status=symmetry_report.status,
            final_measurement_status=final_measurement_status,
            final_symmetry_status=final_symmetry_status,
            viable_alternative_count=viable_alternative_count,
        ),
        measurement_status=measurement_status,
        symmetry_status=symmetry_report.status,
        final_measurement_status=final_measurement_status,
        final_symmetry_status=final_symmetry_status,
        standard_options=options,
        measurement_checks=measurement_checks,
        symmetry_matches=symmetry_report.matches,
        alternatives=alternatives,
        viable_alternative_count=viable_alternative_count,
        unresolved_feature_ids=unresolved_feature_ids,
        warning_codes=warning_codes,
    )


def standard_terrain_options_from_layout(
    layout: CanonicalLayout,
    *,
    template_matches: Sequence[Any] = (),
    templates: Sequence[Any] = (),
    source_dimensions: Sequence[SourceFootprintDimension] = (),
) -> tuple[StandardTerrainFootprintOption, ...]:
    feature_by_id = {feature.feature_id: feature for feature in layout.terrain_features}
    blockers_by_feature_id: dict[str, int] = {}
    for blocker in layout.blockers:
        blockers_by_feature_id[blocker.feature_id] = blockers_by_feature_id.get(
            blocker.feature_id,
            0,
        ) + 1
    template_by_id = {
        template.template_id: template
        for template in templates
    }
    match_by_feature_id = {
        match.feature_id: match
        for match in template_matches
    }

    source_options = _standard_options_from_source_dimensions(
        layout,
        source_dimensions=source_dimensions,
        match_by_feature_id=match_by_feature_id,
        template_by_id=template_by_id,
    )
    if source_options:
        return source_options

    options: list[StandardTerrainFootprintOption] = []
    for option in footprint_size_options_from_layout(layout):
        option_features = tuple(feature_by_id[feature_id] for feature_id in option.feature_ids)
        dense_count = sum(
            1 for feature in option_features if feature.terrain_category == "dense"
        )
        template_ids = tuple(
            sorted(
                {
                    match_by_feature_id[feature.feature_id].template_id
                    for feature in option_features
                    if feature.feature_id in match_by_feature_id
                }
            )
        )
        template_wall_count = _template_wall_count(
            option_features,
            match_by_feature_id,
            template_by_id,
        )
        options.append(
            StandardTerrainFootprintOption(
                option_id=option.option_id,
                width_inches=option.width_inches,
                height_inches=option.height_inches,
                count=option.count,
                dense_feature_count=dense_count,
                wall_segment_count=template_wall_count
                or sum(
                    blockers_by_feature_id.get(feature.feature_id, 0)
                    for feature in option_features
                ),
                feature_ids=option.feature_ids,
                template_ids=template_ids,
                dimension_evidence_count=option.count,
                source_kind="layout_geometry",
            )
        )
    return tuple(options)


def _standard_options_from_source_dimensions(
    layout: CanonicalLayout,
    *,
    source_dimensions: Sequence[SourceFootprintDimension],
    match_by_feature_id: Mapping[str, Any],
    template_by_id: Mapping[str, Any],
) -> tuple[StandardTerrainFootprintOption, ...]:
    if not source_dimensions or not match_by_feature_id:
        return ()

    dimensions_by_template_id: dict[str, list[SourceFootprintDimension]] = {}
    for dimension in source_dimensions:
        dimensions_by_template_id.setdefault(dimension.template_id, []).append(dimension)

    feature_by_id = {feature.feature_id: feature for feature in layout.terrain_features}
    feature_ids_by_key: dict[tuple[float, float], set[str]] = {}
    template_ids_by_key: dict[tuple[float, float], set[str]] = {}
    evidence_count_by_key: dict[tuple[float, float], int] = {}
    evidence_seen: set[tuple[float, float, str]] = set()
    for feature in layout.terrain_features:
        match = match_by_feature_id.get(feature.feature_id)
        if match is None or not _match_is_candidate(match):
            continue
        for dimension in dimensions_by_template_id.get(match.template_id, ()):
            width = max(dimension.width_inches, dimension.height_inches)
            height = min(dimension.width_inches, dimension.height_inches)
            key = (round(width, 4), round(height, 4))
            feature_ids_by_key.setdefault(key, set()).add(feature.feature_id)
            template_ids_by_key.setdefault(key, set()).add(match.template_id)
            evidence_key = (key[0], key[1], dimension.template_id)
            if evidence_key not in evidence_seen:
                evidence_seen.add(evidence_key)
                evidence_count_by_key[key] = (
                    evidence_count_by_key.get(key, 0) + dimension.evidence_count
                )

    options: list[StandardTerrainFootprintOption] = []
    for width, height in sorted(feature_ids_by_key):
        key = (width, height)
        feature_ids = tuple(sorted(feature_ids_by_key[key]))
        template_ids = tuple(sorted(template_ids_by_key[key]))
        option_features = tuple(feature_by_id[feature_id] for feature_id in feature_ids)
        dense_count = sum(
            1 for feature in option_features if feature.terrain_category == "dense"
        )
        options.append(
            StandardTerrainFootprintOption(
                option_id=f"source-footprint-size-{width:05.1f}x{height:05.1f}",
                width_inches=width,
                height_inches=height,
                count=len(feature_ids),
                dense_feature_count=dense_count,
                wall_segment_count=_template_wall_count(
                    option_features,
                    match_by_feature_id,
                    dict(template_by_id),
                ),
                feature_ids=feature_ids,
                template_ids=template_ids,
                dimension_evidence_count=evidence_count_by_key.get(key, 0),
                source_kind="source_catalog",
            )
        )
    return tuple(options)


def _template_wall_count(
    option_features: tuple[TerrainFeature, ...],
    match_by_feature_id: Mapping[str, Any],
    template_by_id: Mapping[str, Any],
) -> int:
    count = 0
    for feature in option_features:
        if feature.terrain_category != "dense":
            continue
        match = match_by_feature_id.get(feature.feature_id)
        if match is None or not _match_is_candidate(match):
            continue
        template = template_by_id.get(match.template_id)
        if template is None:
            continue
        count += len(template.normalized_fragment_paths)
    return count


def _match_is_candidate(match: Any) -> bool:
    return str(getattr(match, "status", "")) == "candidate"


def _measurement_check(
    feature: TerrainFeature,
    layout: CanonicalLayout,
    measurements: tuple[MeasurementAnnotation, ...],
    *,
    bounds: tuple[float, float, float, float] | None = None,
) -> FeatureMeasurementCheck:
    feature_bounds = bounds or _feature_bounds(feature)
    edge_offsets = _edge_offsets(feature_bounds, layout)
    matched_offsets = _matched_corner_offsets(feature_bounds, layout, measurements)
    verified_corner_count = _verified_corner_count(feature_bounds, layout, measurements)
    if not measurements:
        status = ReconciliationCheckStatus.UNAVAILABLE
        review_reason = "measurement_annotations_unavailable"
    elif verified_corner_count == 4:
        status = ReconciliationCheckStatus.PASSED
        review_reason = "all_corner_offsets_match_positioned_measurements"
    else:
        status = ReconciliationCheckStatus.WARNING
        review_reason = "not_all_corner_offsets_match_positioned_measurements"
    return FeatureMeasurementCheck(
        feature_id=feature.feature_id,
        bounds_inches=_round_bounds(feature_bounds),
        edge_offsets_inches=_round_bounds(edge_offsets),
        matched_offsets_inches=matched_offsets,
        verified_corner_count=verified_corner_count,
        status=status,
        review_reason=review_reason,
    )


def _measurement_status(
    checks: tuple[FeatureMeasurementCheck, ...],
) -> ReconciliationCheckStatus:
    if not checks:
        return ReconciliationCheckStatus.UNAVAILABLE
    statuses = {check.status for check in checks}
    if ReconciliationCheckStatus.UNAVAILABLE in statuses:
        return ReconciliationCheckStatus.UNAVAILABLE
    if statuses == {ReconciliationCheckStatus.PASSED}:
        return ReconciliationCheckStatus.PASSED
    return ReconciliationCheckStatus.WARNING


def _final_measurement_status(
    measurement_checks: tuple[FeatureMeasurementCheck, ...],
    alternatives: tuple[TerrainReconciliationAlternative, ...],
) -> ReconciliationCheckStatus:
    viable_by_feature_id = {
        alternative.feature_id: alternative
        for alternative in alternatives
        if alternative.status == ReconciliationAlternativeStatus.VIABLE
    }
    final_statuses: list[ReconciliationCheckStatus] = []
    for check in measurement_checks:
        alternative = viable_by_feature_id.get(check.feature_id)
        final_statuses.append(
            alternative.measurement_status if alternative is not None else check.status
        )
    return _status_from_final_checks(tuple(final_statuses))


def _status_from_final_checks(
    statuses: tuple[ReconciliationCheckStatus, ...],
) -> ReconciliationCheckStatus:
    if not statuses:
        return ReconciliationCheckStatus.UNAVAILABLE
    if ReconciliationCheckStatus.UNAVAILABLE in statuses:
        return ReconciliationCheckStatus.UNAVAILABLE
    if all(status == ReconciliationCheckStatus.PASSED for status in statuses):
        return ReconciliationCheckStatus.PASSED
    return ReconciliationCheckStatus.WARNING


def _best_alternative_for_match(
    match: TerrainSymmetryMatch,
    layout: CanonicalLayout,
    measurements: tuple[MeasurementAnnotation, ...],
    standard_options: tuple[StandardTerrainFootprintOption, ...],
) -> TerrainReconciliationAlternative:
    feature = _feature_by_id(layout, match.feature_id)
    current_option = _option_for_dimensions(*_feature_dimensions(feature), standard_options)
    ordered_options = tuple(
        option
        for option in (
            *((current_option,) if current_option is not None else ()),
            *standard_options,
        )
        if option is not None
    )
    candidates = tuple(
        candidate
        for option in _dedupe_options(ordered_options)
        for candidate in _candidate_alternatives(feature, option, layout, measurements)
    )
    viable = tuple(
        candidate
        for candidate in candidates
        if candidate.status == ReconciliationAlternativeStatus.VIABLE
    )
    if viable:
        return viable[0]
    if candidates:
        return candidates[0]
    return _rejected_missing_option_alternative(feature, layout)


def _candidate_alternatives(
    feature: TerrainFeature,
    option: StandardTerrainFootprintOption,
    layout: CanonicalLayout,
    measurements: tuple[MeasurementAnnotation, ...],
) -> tuple[TerrainReconciliationAlternative, ...]:
    candidates = [
        _centered_alternative(feature, option, layout, measurements),
    ]
    candidates.extend(
        _mirrored_partner_alternative(feature, partner, option, layout, measurements)
        for partner in layout.terrain_features
        if partner.feature_id != feature.feature_id
        and partner.terrain_category == feature.terrain_category
    )
    return tuple(candidates)


def _resolved_feature_ids(
    alternative: TerrainReconciliationAlternative,
) -> tuple[str, ...]:
    if alternative.alternative_kind.startswith("mirror_partner:"):
        partner_id = alternative.alternative_kind.removeprefix("mirror_partner:")
        return tuple(sorted((alternative.feature_id, partner_id)))
    return (alternative.feature_id,)


def _centered_alternative(
    feature: TerrainFeature,
    option: StandardTerrainFootprintOption,
    layout: CanonicalLayout,
    measurements: tuple[MeasurementAnnotation, ...],
) -> TerrainReconciliationAlternative:
    current_dimensions = _feature_dimensions(feature)
    candidate_dimensions = _oriented_option_dimensions(option, current_dimensions)
    width, height = candidate_dimensions
    proposed_bounds = (
        (layout.board.width - width) / 2.0,
        (layout.board.height - height) / 2.0,
        (layout.board.width + width) / 2.0,
        (layout.board.height + height) / 2.0,
    )
    measurement_check = _measurement_check(
        feature,
        layout,
        measurements,
        bounds=proposed_bounds,
    )
    overlap_feature_ids = _overlap_feature_ids(
        proposed_bounds,
        layout,
        ignore_feature_id=feature.feature_id,
    )
    symmetry_residual = _bounds_residual(
        proposed_bounds,
        _rotated_bounds(proposed_bounds, layout),
    )
    status, review_reason = _alternative_status(
        proposed_bounds=proposed_bounds,
        measurement_check=measurement_check,
        symmetry_residual=symmetry_residual,
        overlap_feature_ids=overlap_feature_ids,
        option=option,
        current_dimensions=current_dimensions,
    )
    return TerrainReconciliationAlternative(
        feature_id=feature.feature_id,
        alternative_kind="self_center",
        option_id=option.option_id,
        proposed_bounds_inches=_round_bounds(proposed_bounds),
        measurement_status=measurement_check.status,
        symmetry_residual_inches=round(symmetry_residual, 4),
        overlap_feature_ids=overlap_feature_ids,
        status=status,
        review_reason=review_reason,
    )


def _mirrored_partner_alternative(
    feature: TerrainFeature,
    partner: TerrainFeature,
    option: StandardTerrainFootprintOption,
    layout: CanonicalLayout,
    measurements: tuple[MeasurementAnnotation, ...],
) -> TerrainReconciliationAlternative:
    partner_mirror_bounds = _rotated_bounds(_feature_bounds(partner), layout)
    candidate_dimensions = _oriented_option_dimensions(
        option,
        _bounds_dimensions(partner_mirror_bounds),
    )
    proposed_bounds = _bounds_from_center(
        _bounds_center(partner_mirror_bounds),
        candidate_dimensions,
    )
    measurement_check = _measurement_check(
        feature,
        layout,
        measurements,
        bounds=proposed_bounds,
    )
    overlap_feature_ids = _overlap_feature_ids(
        proposed_bounds,
        layout,
        ignore_feature_id=feature.feature_id,
    )
    symmetry_residual = _bounds_residual(
        _rotated_bounds(proposed_bounds, layout),
        _feature_bounds(partner),
    )
    status, review_reason = _alternative_status(
        proposed_bounds=proposed_bounds,
        measurement_check=measurement_check,
        symmetry_residual=symmetry_residual,
        overlap_feature_ids=overlap_feature_ids,
        option=option,
        current_dimensions=_feature_dimensions(feature),
    )
    if status == ReconciliationAlternativeStatus.VIABLE:
        review_reason = "mirror_partner_satisfies_measurement_and_symmetry"
    return TerrainReconciliationAlternative(
        feature_id=feature.feature_id,
        alternative_kind=f"mirror_partner:{partner.feature_id}",
        option_id=option.option_id,
        proposed_bounds_inches=_round_bounds(proposed_bounds),
        measurement_status=measurement_check.status,
        symmetry_residual_inches=round(symmetry_residual, 4),
        overlap_feature_ids=overlap_feature_ids,
        status=status,
        review_reason=review_reason,
    )


def _rejected_missing_option_alternative(
    feature: TerrainFeature,
    layout: CanonicalLayout,
) -> TerrainReconciliationAlternative:
    bounds = _feature_bounds(feature)
    return TerrainReconciliationAlternative(
        feature_id=feature.feature_id,
        alternative_kind="self_center",
        option_id=None,
        proposed_bounds_inches=_round_bounds(bounds),
        measurement_status=ReconciliationCheckStatus.UNAVAILABLE,
        symmetry_residual_inches=_bounds_residual(bounds, _rotated_bounds(bounds, layout)),
        overlap_feature_ids=(),
        status=ReconciliationAlternativeStatus.REJECTED,
        review_reason="candidate_not_in_standard_options",
    )


def _alternative_status(
    *,
    proposed_bounds: tuple[float, float, float, float],
    measurement_check: FeatureMeasurementCheck,
    symmetry_residual: float,
    overlap_feature_ids: tuple[str, ...],
    option: StandardTerrainFootprintOption,
    current_dimensions: tuple[float, float],
) -> tuple[ReconciliationAlternativeStatus, str]:
    if not _on_inch_grid(proposed_bounds):
        return (
            ReconciliationAlternativeStatus.REJECTED,
            "candidate_not_on_inch_grid",
        )
    if overlap_feature_ids:
        return (
            ReconciliationAlternativeStatus.REJECTED,
            "candidate_overlaps_existing_feature",
        )
    if measurement_check.status != ReconciliationCheckStatus.PASSED:
        return (
            ReconciliationAlternativeStatus.REJECTED,
            "candidate_measurement_check_failed",
        )
    if symmetry_residual > 0.0:
        return (
            ReconciliationAlternativeStatus.REJECTED,
            "candidate_symmetry_check_failed",
        )
    if _option_matches_dimensions(option, current_dimensions):
        return (
            ReconciliationAlternativeStatus.VIABLE,
            "self_center_satisfies_measurement_and_symmetry",
        )
    return (
        ReconciliationAlternativeStatus.VIABLE,
        "standard_option_satisfies_measurement_and_symmetry",
    )


def _reconciliation_status(
    *,
    raw_measurement_status: ReconciliationCheckStatus,
    raw_symmetry_status: TerrainSymmetryStatus,
    final_measurement_status: ReconciliationCheckStatus,
    final_symmetry_status: TerrainSymmetryStatus,
    viable_alternative_count: int,
) -> TerrainReconciliationStatus:
    if (
        raw_measurement_status == ReconciliationCheckStatus.PASSED
        and raw_symmetry_status == TerrainSymmetryStatus.PASSED
    ):
        return TerrainReconciliationStatus.PASSED
    if (
        final_measurement_status == ReconciliationCheckStatus.PASSED
        and final_symmetry_status == TerrainSymmetryStatus.PASSED
        and viable_alternative_count > 0
    ):
        return TerrainReconciliationStatus.PASSED_WITH_ALTERNATIVES
    return TerrainReconciliationStatus.WARNING


def _warning_codes(
    *,
    final_measurement_status: ReconciliationCheckStatus,
    final_symmetry_status: TerrainSymmetryStatus,
    unresolved_feature_ids: tuple[str, ...],
) -> tuple[str, ...]:
    warnings: list[str] = []
    if final_measurement_status != ReconciliationCheckStatus.PASSED:
        warnings.append("terrain_reconciliation_measurement_not_fully_verified")
    if final_symmetry_status != TerrainSymmetryStatus.PASSED:
        warnings.append("terrain_reconciliation_symmetry_not_fully_verified")
    if unresolved_feature_ids:
        warnings.append("terrain_reconciliation_unresolved_asymmetry")
    return tuple(warnings)


def _feature_by_id(layout: CanonicalLayout, feature_id: str) -> TerrainFeature:
    for feature in layout.terrain_features:
        if feature.feature_id == feature_id:
            return feature
    raise ValueError(f"Terrain feature not found: {feature_id}")


def _feature_bounds(feature: TerrainFeature) -> tuple[float, float, float, float]:
    xs = [point.x for point in feature.footprint.points]
    ys = [point.y for point in feature.footprint.points]
    return min(xs), min(ys), max(xs), max(ys)


def _feature_dimensions(feature: TerrainFeature) -> tuple[float, float]:
    x_min, y_min, x_max, y_max = _feature_bounds(feature)
    return x_max - x_min, y_max - y_min


def _bounds_dimensions(bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    x_min, y_min, x_max, y_max = bounds
    return x_max - x_min, y_max - y_min


def _edge_offsets(
    bounds: tuple[float, float, float, float],
    layout: CanonicalLayout,
) -> tuple[float, float, float, float]:
    x_min, y_min, x_max, y_max = bounds
    return (
        x_min,
        layout.board.width - x_max,
        y_min,
        layout.board.height - y_max,
    )


def _matched_corner_offsets(
    bounds: tuple[float, float, float, float],
    layout: CanonicalLayout,
    measurements: tuple[MeasurementAnnotation, ...],
) -> tuple[float, ...]:
    matched: list[float] = []
    for corner in _corners_with_offsets(bounds, layout):
        for expected_offset in (corner[2], corner[3]):
            if _has_matching_measurement(expected_offset, corner[:2], measurements):
                matched.append(round(expected_offset, 4))
    return tuple(matched)


def _verified_corner_count(
    bounds: tuple[float, float, float, float],
    layout: CanonicalLayout,
    measurements: tuple[MeasurementAnnotation, ...],
) -> int:
    return sum(
        1
        for corner in _corners_with_offsets(bounds, layout)
        if _has_distinct_matching_measurements(corner[2], corner[3], corner[:2], measurements)
    )


def _corners_with_offsets(
    bounds: tuple[float, float, float, float],
    layout: CanonicalLayout,
) -> tuple[tuple[float, float, float, float], ...]:
    x_min, y_min, x_max, y_max = bounds
    left, right, bottom, top = _edge_offsets(bounds, layout)
    return (
        (x_min, y_min, left, bottom),
        (x_max, y_min, right, bottom),
        (x_max, y_max, right, top),
        (x_min, y_max, left, top),
    )


def _has_matching_measurement(
    expected_value: float,
    corner: tuple[float, float],
    measurements: tuple[MeasurementAnnotation, ...],
) -> bool:
    corner_x, corner_y = corner
    return any(
        isfinite(measurement.x)
        and isfinite(measurement.y)
        and abs(measurement.value - expected_value) <= MEASUREMENT_TOLERANCE_INCHES
        and abs(measurement.x - corner_x) <= MEASUREMENT_POSITION_TOLERANCE_INCHES
        and abs(measurement.y - corner_y) <= MEASUREMENT_POSITION_TOLERANCE_INCHES
        for measurement in measurements
    )


def _has_distinct_matching_measurements(
    first_expected_value: float,
    second_expected_value: float,
    corner: tuple[float, float],
    measurements: tuple[MeasurementAnnotation, ...],
) -> bool:
    first_matches = _matching_measurement_indexes(
        first_expected_value,
        corner,
        measurements,
    )
    second_matches = _matching_measurement_indexes(
        second_expected_value,
        corner,
        measurements,
    )
    return any(
        first_index != second_index
        for first_index in first_matches
        for second_index in second_matches
    )


def _matching_measurement_indexes(
    expected_value: float,
    corner: tuple[float, float],
    measurements: tuple[MeasurementAnnotation, ...],
) -> tuple[int, ...]:
    corner_x, corner_y = corner
    return tuple(
        index
        for index, measurement in enumerate(measurements)
        if isfinite(measurement.x)
        and isfinite(measurement.y)
        and abs(measurement.value - expected_value) <= MEASUREMENT_TOLERANCE_INCHES
        and abs(measurement.x - corner_x) <= MEASUREMENT_POSITION_TOLERANCE_INCHES
        and abs(measurement.y - corner_y) <= MEASUREMENT_POSITION_TOLERANCE_INCHES
    )


def _option_for_dimensions(
    width: float,
    height: float,
    standard_options: tuple[StandardTerrainFootprintOption, ...],
) -> StandardTerrainFootprintOption | None:
    candidate = FootprintSizeOption(
        option_id="candidate",
        width_inches=max(width, height),
        height_inches=min(width, height),
        count=1,
        feature_ids=(),
    )
    for option in standard_options:
        if (
            abs(option.width_inches - candidate.width_inches) <= GRID_TOLERANCE_INCHES
            and abs(option.height_inches - candidate.height_inches) <= GRID_TOLERANCE_INCHES
        ):
            return option
    return None


def _option_matches_dimensions(
    option: StandardTerrainFootprintOption,
    dimensions: tuple[float, float],
) -> bool:
    width, height = dimensions
    return (
        abs(option.width_inches - max(width, height)) <= GRID_TOLERANCE_INCHES
        and abs(option.height_inches - min(width, height)) <= GRID_TOLERANCE_INCHES
    )


def _oriented_option_dimensions(
    option: StandardTerrainFootprintOption,
    current_dimensions: tuple[float, float],
) -> tuple[float, float]:
    current_width, current_height = current_dimensions
    if current_width <= current_height:
        return option.height_inches, option.width_inches
    return option.width_inches, option.height_inches


def _dedupe_options(
    options: tuple[StandardTerrainFootprintOption, ...],
) -> tuple[StandardTerrainFootprintOption, ...]:
    seen: set[str] = set()
    deduped: list[StandardTerrainFootprintOption] = []
    for option in options:
        if option.option_id in seen:
            continue
        seen.add(option.option_id)
        deduped.append(option)
    return tuple(deduped)


def _overlap_feature_ids(
    bounds: tuple[float, float, float, float],
    layout: CanonicalLayout,
    *,
    ignore_feature_id: str,
) -> tuple[str, ...]:
    candidate_shape = box(*bounds)
    overlaps: list[str] = []
    for feature in layout.terrain_features:
        if feature.feature_id == ignore_feature_id:
            continue
        if candidate_shape.intersection(feature.footprint.to_shapely()).area > 1e-6:
            overlaps.append(feature.feature_id)
    return tuple(overlaps)


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


def _bounds_center(bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    x_min, y_min, x_max, y_max = bounds
    return (x_min + x_max) / 2.0, (y_min + y_max) / 2.0


def _bounds_from_center(
    center: tuple[float, float],
    dimensions: tuple[float, float],
) -> tuple[float, float, float, float]:
    center_x, center_y = center
    width, height = dimensions
    return (
        center_x - width / 2.0,
        center_y - height / 2.0,
        center_x + width / 2.0,
        center_y + height / 2.0,
    )


def _on_inch_grid(bounds: tuple[float, float, float, float]) -> bool:
    return all(abs(value - round(value)) <= GRID_TOLERANCE_INCHES for value in bounds)


def _round_bounds(
    bounds: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    return (
        round(bounds[0], 4),
        round(bounds[1], 4),
        round(bounds[2], 4),
        round(bounds[3], 4),
    )
