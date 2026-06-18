from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Sequence
from os import PathLike
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from warhammer_companion.ingestion.layouts import (
    BBox,
    ExtractedLayout,
    FeatureProfile,
    LayoutElement,
    OfficialFeatureCode,
    Point,
    WallSide,
)
from warhammer_companion.ingestion.terrain_feature_catalog import (
    FEATURE_CATALOG_VERSION,
    FeaturePosition,
    TerrainFeatureType,
    terrain_feature_type_by_id,
    terrain_feature_type_options,
)

CategorizerPath = str | PathLike[str]

VISUAL_CATEGORIZER_PROFILE_OPTIONS: tuple[FeatureProfile, ...] = (
    "ruined_wall_section",
    "ruined_wall_l",
    "ruined_wall_u",
    "ruined_wall_perimeter",
    "container_or_solid",
    "solid_los_blocker",
    "floor_or_platform",
    "unknown_dense",
)
VISUAL_CATEGORIZER_WALL_SIDE_OPTIONS: tuple[WallSide, ...] = (
    "left",
    "right",
    "top",
    "bottom",
)
WALL_SIDE_COUNTS_BY_PROFILE: dict[FeatureProfile, int] = {
    "ruined_wall_l": 2,
    "ruined_wall_u": 3,
    "ruined_wall_perimeter": 4,
}


class CategorizerFeature(BaseModel):
    feature_id: str
    feature_digest: str
    feature_type: Literal["dense"]
    current_profile: FeatureProfile | None = None
    official_feature_code: OfficialFeatureCode | None = None
    current_wall_sides: list[WallSide] | None = None
    terrain_area_id: str | None = None
    review_image_path: str | None = None
    source_page: int = Field(ge=1)
    source_bbox: BBox
    footprint: list[Point]
    warnings: list[str] = Field(default_factory=list)


class CategorizerRequest(BaseModel):
    schema_version: int = 1
    provider: Literal["codex_visual_classifier"] = "codex_visual_classifier"
    catalog_version: int = FEATURE_CATALOG_VERSION
    instructions: str = (
        "Classify each dense terrain feature from the official layout review images against "
        "the supplied known terrain feature type catalog. Use type_id when possible. Choose "
        "an official_feature_code mapping when one is present, because official AB/CD/EF/GH "
        "labels are deterministic source data. Choose "
        "wall types only for vertical ruined walls; choose floor-or-platform for horizontal "
        "upper floors, platforms, or surfaces that should be retained for review but must not "
        "block line of sight. Echo feature_digest in each result."
    )
    profile_options: list[FeatureProfile] = Field(
        default_factory=lambda: list(VISUAL_CATEGORIZER_PROFILE_OPTIONS)
    )
    wall_side_options: list[WallSide] = Field(
        default_factory=lambda: list(VISUAL_CATEGORIZER_WALL_SIDE_OPTIONS)
    )
    terrain_feature_types: list[TerrainFeatureType] = Field(
        default_factory=terrain_feature_type_options
    )
    features: list[CategorizerFeature]


class FeatureCategorization(BaseModel):
    feature_id: str
    feature_digest: str | None = None
    type_id: str | None = None
    profile: FeatureProfile | None = None
    position: FeaturePosition | None = None
    wall_sides: list[WallSide] | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class CategorizerResults(BaseModel):
    schema_version: int = 1
    provider: str = "codex_visual_classifier"
    catalog_version: int = FEATURE_CATALOG_VERSION
    categorizations: list[FeatureCategorization] = Field(default_factory=list)


class FeatureCategorizationApplication(BaseModel):
    features: list[LayoutElement]
    applied_count: int = 0
    unmatched_feature_ids: list[str] = Field(default_factory=list)
    low_confidence_feature_ids: list[str] = Field(default_factory=list)
    digest_mismatch_feature_ids: list[str] = Field(default_factory=list)
    duplicate_conflict_feature_ids: list[str] = Field(default_factory=list)


class LayoutCategorizationApplication(BaseModel):
    layouts: list[ExtractedLayout]
    applied_count: int = 0
    unmatched_feature_ids: list[str] = Field(default_factory=list)
    low_confidence_feature_ids: list[str] = Field(default_factory=list)
    digest_mismatch_feature_ids: list[str] = Field(default_factory=list)
    duplicate_conflict_feature_ids: list[str] = Field(default_factory=list)


def build_categorizer_request(
    features: Sequence[LayoutElement],
    *,
    review_image_lookup: dict[int, str] | None = None,
) -> CategorizerRequest:
    dense_features = [
        CategorizerFeature(
            feature_id=feature.id,
            feature_digest=terrain_feature_digest(feature),
            feature_type="dense",
            current_profile=feature.feature_profile,
            official_feature_code=feature.official_feature_code,
            current_wall_sides=feature.feature_wall_sides,
            terrain_area_id=feature.terrain_area_id,
            review_image_path=(review_image_lookup or {}).get(feature.source_page),
            source_page=feature.source_page,
            source_bbox=feature.source_bbox,
            footprint=feature.footprint,
            warnings=feature.warnings,
        )
        for feature in features
        if feature.kind == "terrain_feature" and feature.feature_type == "dense"
    ]
    return CategorizerRequest(features=dense_features)


def write_visual_categorizer_request(
    layouts: Sequence[ExtractedLayout],
    output_path: CategorizerPath,
    *,
    review_dir: CategorizerPath | None = None,
) -> CategorizerRequest:
    path = Path(output_path)
    resolved_review_dir = Path(review_dir) if review_dir is not None else path.parent / "layouts"
    review_image_lookup = {
        layout.source_page: str(resolved_review_dir / f"page-{layout.source_page}.png")
        for layout in layouts
    }
    request = build_categorizer_request(
        _iter_layout_features(layouts),
        review_image_lookup=review_image_lookup,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(request.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return request


def load_feature_categorizations(input_path: CategorizerPath) -> list[FeatureCategorization]:
    path = Path(input_path)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [FeatureCategorization.model_validate(item) for item in payload]
    return CategorizerResults.model_validate(payload).categorizations


def apply_layout_feature_categorizations(
    layouts: Sequence[ExtractedLayout],
    categorizations: Sequence[FeatureCategorization],
    *,
    min_confidence: float = 0.5,
) -> list[ExtractedLayout]:
    return apply_layout_feature_categorizations_with_stats(
        layouts,
        categorizations,
        min_confidence=min_confidence,
    ).layouts


def apply_layout_feature_categorizations_with_stats(
    layouts: Sequence[ExtractedLayout],
    categorizations: Sequence[FeatureCategorization],
    *,
    min_confidence: float = 0.5,
) -> LayoutCategorizationApplication:
    updated_layouts: list[ExtractedLayout] = []
    applied_count = 0
    low_confidence_feature_ids: list[str] = []
    digest_mismatch_feature_ids: list[str] = []
    duplicate_conflict_feature_ids: list[str] = []
    for layout in layouts:
        result = apply_feature_categorizations_with_stats(
            layout.terrain_features,
            categorizations,
            min_confidence=min_confidence,
        )
        updated_layouts.append(layout.model_copy(update={"terrain_features": result.features}))
        applied_count += result.applied_count
        low_confidence_feature_ids.extend(result.low_confidence_feature_ids)
        digest_mismatch_feature_ids.extend(result.digest_mismatch_feature_ids)
        duplicate_conflict_feature_ids.extend(result.duplicate_conflict_feature_ids)
    dense_feature_ids = {
        feature.id
        for layout in layouts
        for feature in layout.terrain_features
        if feature.kind == "terrain_feature" and feature.feature_type == "dense"
    }
    unmatched_feature_ids = sorted(
        {
            categorization.feature_id
            for categorization in categorizations
            if categorization.feature_id not in dense_feature_ids
        }
    )
    return LayoutCategorizationApplication(
        layouts=updated_layouts,
        applied_count=applied_count,
        unmatched_feature_ids=unmatched_feature_ids,
        low_confidence_feature_ids=sorted(set(low_confidence_feature_ids)),
        digest_mismatch_feature_ids=sorted(set(digest_mismatch_feature_ids)),
        duplicate_conflict_feature_ids=sorted(set(duplicate_conflict_feature_ids)),
    )


def apply_feature_categorizations(
    features: Sequence[LayoutElement],
    categorizations: Sequence[FeatureCategorization],
    *,
    min_confidence: float = 0.5,
) -> list[LayoutElement]:
    return apply_feature_categorizations_with_stats(
        features,
        categorizations,
        min_confidence=min_confidence,
    ).features


def apply_feature_categorizations_with_stats(
    features: Sequence[LayoutElement],
    categorizations: Sequence[FeatureCategorization],
    *,
    min_confidence: float = 0.5,
) -> FeatureCategorizationApplication:
    by_feature_id, duplicate_conflict_feature_ids = _dedupe_categorizations(categorizations)
    categorization_counts = Counter(categorization.feature_id for categorization in categorizations)
    updated: list[LayoutElement] = []
    applied_count = 0
    low_confidence_feature_ids: list[str] = []
    digest_mismatch_feature_ids: list[str] = []
    for feature in features:
        categorization = by_feature_id.get(feature.id)
        if (
            categorization is None
            or feature.kind != "terrain_feature"
            or feature.feature_type != "dense"
        ):
            updated.append(feature)
            continue
        if categorization.confidence < min_confidence:
            low_confidence_feature_ids.append(categorization.feature_id)
            updated.append(feature)
            continue
        if (
            categorization.feature_digest is not None
            and categorization.feature_digest != terrain_feature_digest(feature)
        ):
            digest_mismatch_feature_ids.append(categorization.feature_id)
            updated.append(feature)
            continue
        resolved_profile, catalog_type = _resolved_profile(categorization)
        if resolved_profile is None:
            updated.append(feature)
            continue
        warnings = [
            warning
            for warning in feature.warnings
            if not warning.startswith("codex-categorizer-profile:")
            and not warning.startswith("codex-categorizer-type:")
            and not warning.startswith("codex-categorizer-position:")
            and not warning.startswith("codex-categorizer-wall-sides:")
        ]
        warnings.append(f"codex-categorizer-profile:{resolved_profile}")
        if catalog_type is not None:
            warnings.append(f"codex-categorizer-type:{catalog_type.type_id}")
        if categorization.position is not None:
            warnings.append(f"codex-categorizer-position:{categorization.position}")
        requested_wall_sides = (
            categorization.wall_sides
            if categorization.wall_sides is not None
            else catalog_type.default_wall_sides
            if catalog_type is not None
            else None
        )
        wall_sides, ignored_wall_sides_reason = _validated_wall_sides(
            resolved_profile,
            requested_wall_sides,
        )
        if wall_sides:
            warnings.append("codex-categorizer-wall-sides:" + ",".join(wall_sides))
        elif ignored_wall_sides_reason:
            warnings.append(f"codex-categorizer-wall-sides-ignored:{ignored_wall_sides_reason}")
        updated.append(
            feature.model_copy(
                update={
                    "feature_profile": resolved_profile,
                    "feature_wall_sides": wall_sides,
                    "confidence": categorization.confidence,
                    "warnings": warnings,
                }
            )
        )
        applied_count += categorization_counts[categorization.feature_id]
    feature_ids = {
        feature.id
        for feature in features
        if feature.kind == "terrain_feature" and feature.feature_type == "dense"
    }
    unmatched_feature_ids = sorted(
        {
            categorization.feature_id
            for categorization in categorizations
            if categorization.feature_id not in feature_ids
        }
    )
    return FeatureCategorizationApplication(
        features=updated,
        applied_count=applied_count,
        unmatched_feature_ids=unmatched_feature_ids,
        low_confidence_feature_ids=sorted(set(low_confidence_feature_ids)),
        digest_mismatch_feature_ids=sorted(set(digest_mismatch_feature_ids)),
        duplicate_conflict_feature_ids=sorted(set(duplicate_conflict_feature_ids)),
    )


def _iter_layout_features(layouts: Iterable[ExtractedLayout]) -> list[LayoutElement]:
    return [feature for layout in layouts for feature in layout.terrain_features]


def terrain_feature_digest(feature: LayoutElement) -> str:
    payload = {
        "catalog_version": FEATURE_CATALOG_VERSION,
        "current_profile": feature.feature_profile,
        "feature_id": feature.id,
        "feature_wall_sides": list(feature.feature_wall_sides or []),
        "footprint": _rounded_points(feature.footprint),
        "official_feature_code": feature.official_feature_code,
        "source_bbox": _rounded_bbox(feature.source_bbox),
        "source_page": feature.source_page,
        "terrain_area_id": feature.terrain_area_id,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


def _validated_wall_sides(
    profile: FeatureProfile,
    wall_sides: Sequence[WallSide] | None,
) -> tuple[list[WallSide] | None, str | None]:
    if not wall_sides:
        return None, None
    expected_count = WALL_SIDE_COUNTS_BY_PROFILE.get(profile)
    if expected_count is None:
        return None, f"profile-{profile}"
    unique_sides = list(dict.fromkeys(wall_sides))
    if len(unique_sides) != expected_count:
        return None, f"expected-{expected_count}-sides"
    return unique_sides, None


def _resolved_profile(
    categorization: FeatureCategorization,
) -> tuple[FeatureProfile | None, TerrainFeatureType | None]:
    if categorization.type_id:
        try:
            catalog_type = terrain_feature_type_by_id(categorization.type_id)
        except KeyError:
            return categorization.profile, None
        return catalog_type.feature_profile, catalog_type
    return categorization.profile, None


def _dedupe_categorizations(
    categorizations: Sequence[FeatureCategorization],
) -> tuple[dict[str, FeatureCategorization], list[str]]:
    grouped: dict[str, list[FeatureCategorization]] = {}
    for categorization in categorizations:
        grouped.setdefault(categorization.feature_id, []).append(categorization)

    deduped: dict[str, FeatureCategorization] = {}
    conflicts: list[str] = []
    for feature_id, items in grouped.items():
        first = items[0]
        first_key = _categorization_conflict_key(first)
        if all(_categorization_conflict_key(item) == first_key for item in items):
            deduped[feature_id] = first
        else:
            conflicts.append(feature_id)
    return deduped, sorted(conflicts)


def _categorization_conflict_key(
    categorization: FeatureCategorization,
) -> tuple[object, ...]:
    return (
        categorization.feature_digest,
        categorization.type_id,
        categorization.profile,
        categorization.position,
        tuple(categorization.wall_sides or ()),
    )


def _rounded_points(points: Sequence[Point]) -> list[tuple[float, float]]:
    return [(round(float(x), 4), round(float(y), 4)) for x, y in points]


def _rounded_bbox(bbox: BBox) -> tuple[float, float, float, float]:
    return (
        round(float(bbox[0]), 4),
        round(float(bbox[1]), 4),
        round(float(bbox[2]), 4),
        round(float(bbox[3]), 4),
    )
