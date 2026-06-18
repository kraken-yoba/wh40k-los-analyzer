from __future__ import annotations

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
    Point,
    WallSide,
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
    feature_type: Literal["dense"]
    current_profile: FeatureProfile | None = None
    terrain_area_id: str | None = None
    review_image_path: str | None = None
    source_page: int = Field(ge=1)
    source_bbox: BBox
    footprint: list[Point]
    warnings: list[str] = Field(default_factory=list)


class CategorizerRequest(BaseModel):
    schema_version: int = 1
    provider: Literal["chatgpt_subscription"] = "chatgpt_subscription"
    instructions: str = (
        "Classify each dense terrain feature from the official layout review images. "
        "Choose wall profiles only for vertical ruined walls; choose floor_or_platform for "
        "horizontal upper floors, platforms, or other surfaces that should be retained for "
        "review but must not block line of sight."
    )
    profile_options: list[FeatureProfile] = Field(
        default_factory=lambda: list(VISUAL_CATEGORIZER_PROFILE_OPTIONS)
    )
    wall_side_options: list[WallSide] = Field(
        default_factory=lambda: list(VISUAL_CATEGORIZER_WALL_SIDE_OPTIONS)
    )
    features: list[CategorizerFeature]


class FeatureCategorization(BaseModel):
    feature_id: str
    profile: FeatureProfile
    wall_sides: list[WallSide] | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class CategorizerResults(BaseModel):
    schema_version: int = 1
    categorizations: list[FeatureCategorization] = Field(default_factory=list)


class FeatureCategorizationApplication(BaseModel):
    features: list[LayoutElement]
    applied_count: int = 0
    unmatched_feature_ids: list[str] = Field(default_factory=list)
    low_confidence_feature_ids: list[str] = Field(default_factory=list)


class LayoutCategorizationApplication(BaseModel):
    layouts: list[ExtractedLayout]
    applied_count: int = 0
    unmatched_feature_ids: list[str] = Field(default_factory=list)
    low_confidence_feature_ids: list[str] = Field(default_factory=list)


def build_categorizer_request(
    features: Sequence[LayoutElement],
    *,
    review_image_lookup: dict[int, str] | None = None,
) -> CategorizerRequest:
    dense_features = [
        CategorizerFeature(
            feature_id=feature.id,
            feature_type="dense",
            current_profile=feature.feature_profile,
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
    for layout in layouts:
        result = apply_feature_categorizations_with_stats(
            layout.terrain_features,
            categorizations,
            min_confidence=min_confidence,
        )
        updated_layouts.append(layout.model_copy(update={"terrain_features": result.features}))
        applied_count += result.applied_count
        low_confidence_feature_ids.extend(result.low_confidence_feature_ids)
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
    by_feature_id = {
        categorization.feature_id: categorization for categorization in categorizations
    }
    categorization_counts = Counter(categorization.feature_id for categorization in categorizations)
    updated: list[LayoutElement] = []
    applied_count = 0
    low_confidence_feature_ids: list[str] = []
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
        warnings = [
            warning
            for warning in feature.warnings
            if not warning.startswith("chatgpt-subscription-categorized:")
            and not warning.startswith("chatgpt-subscription-wall-sides:")
        ]
        warnings.append(f"chatgpt-subscription-categorized:{categorization.profile}")
        wall_sides, ignored_wall_sides_reason = _validated_wall_sides(categorization)
        if wall_sides:
            warnings.append("chatgpt-subscription-wall-sides:" + ",".join(wall_sides))
        elif ignored_wall_sides_reason:
            warnings.append(f"chatgpt-subscription-wall-sides-ignored:{ignored_wall_sides_reason}")
        updated.append(
            feature.model_copy(
                update={
                    "feature_profile": categorization.profile,
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
    )


def _iter_layout_features(layouts: Iterable[ExtractedLayout]) -> list[LayoutElement]:
    return [feature for layout in layouts for feature in layout.terrain_features]


def _validated_wall_sides(
    categorization: FeatureCategorization,
) -> tuple[list[WallSide] | None, str | None]:
    wall_sides = categorization.wall_sides
    if not wall_sides:
        return None, None
    expected_count = WALL_SIDE_COUNTS_BY_PROFILE.get(categorization.profile)
    if expected_count is None:
        return None, f"profile-{categorization.profile}"
    unique_sides = list(dict.fromkeys(wall_sides))
    if len(unique_sides) != expected_count:
        return None, f"expected-{expected_count}-sides"
    return unique_sides, None
