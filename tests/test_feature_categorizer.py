from __future__ import annotations

from warhammer_companion.ingestion.feature_categorizer import (
    FeatureCategorization,
    apply_feature_categorizations,
    apply_layout_feature_categorizations_with_stats,
    build_categorizer_request,
)
from warhammer_companion.ingestion.layouts import ExtractedLayout, LayoutElement


def test_apply_feature_categorizations_updates_profiles_and_warnings() -> None:
    feature = _dense_feature("feature-1", profile="unknown_dense")

    updated = apply_feature_categorizations(
        [feature],
        [
            FeatureCategorization(
                feature_id="feature-1",
                profile="ruined_wall_perimeter",
                confidence=0.91,
                rationale="visual model identified vertical ruin walls around a floor",
                wall_sides=["left", "right", "top", "bottom"],
            )
        ],
    )

    assert updated[0].feature_profile == "ruined_wall_perimeter"
    assert updated[0].feature_wall_sides == ["left", "right", "top", "bottom"]
    assert updated[0].confidence == 0.91
    assert "chatgpt-subscription-categorized:ruined_wall_perimeter" in updated[0].warnings
    assert "chatgpt-subscription-wall-sides:left,right,top,bottom" in updated[0].warnings


def test_categorizer_request_lists_wall_container_and_floor_options() -> None:
    request = build_categorizer_request(
        [_dense_feature("feature-1", profile="unknown_dense")],
        review_image_lookup={9: "data/processed/review/layouts/page-9.png"},
    )

    options = request.profile_options

    assert "ruined_wall_perimeter" in options
    assert "ruined_wall_l" in options
    assert "ruined_wall_u" in options
    assert "container_or_solid" in options
    assert "floor_or_platform" in options
    assert request.features[0].feature_id == "feature-1"
    assert request.features[0].review_image_path == "data/processed/review/layouts/page-9.png"
    assert request.wall_side_options == ["left", "right", "top", "bottom"]


def test_apply_layout_feature_categorizations_reports_unmatched_results() -> None:
    layout = _layout_with_feature(_dense_feature("feature-1", profile="unknown_dense"))

    result = apply_layout_feature_categorizations_with_stats(
        [layout],
        [
            FeatureCategorization(
                feature_id="missing-feature",
                profile="floor_or_platform",
                confidence=0.9,
            )
        ],
    )

    assert result.layouts[0].terrain_features[0].feature_profile == "unknown_dense"
    assert result.applied_count == 0
    assert result.unmatched_feature_ids == ["missing-feature"]


def test_apply_feature_categorizations_ignores_wall_sides_on_solid_profiles() -> None:
    feature = _dense_feature("feature-1", profile="unknown_dense")

    updated = apply_feature_categorizations(
        [feature],
        [
            FeatureCategorization(
                feature_id="feature-1",
                profile="container_or_solid",
                confidence=0.9,
                wall_sides=["left", "top"],
            )
        ],
    )

    assert updated[0].feature_profile == "container_or_solid"
    assert updated[0].feature_wall_sides is None
    assert (
        "chatgpt-subscription-wall-sides-ignored:profile-container_or_solid" in updated[0].warnings
    )


def test_apply_feature_categorizations_ignores_wrong_wall_side_count() -> None:
    feature = _dense_feature("feature-1", profile="unknown_dense")

    updated = apply_feature_categorizations(
        [feature],
        [
            FeatureCategorization(
                feature_id="feature-1",
                profile="ruined_wall_u",
                confidence=0.9,
                wall_sides=["left", "top"],
            )
        ],
    )

    assert updated[0].feature_profile == "ruined_wall_u"
    assert updated[0].feature_wall_sides is None
    assert "chatgpt-subscription-wall-sides-ignored:expected-3-sides" in updated[0].warnings


def _dense_feature(feature_id: str, *, profile: str) -> LayoutElement:
    return LayoutElement(
        id=feature_id,
        label="Dense Feature",
        kind="terrain_feature",
        feature_type="dense",
        feature_profile=profile,
        terrain_area_id="area-1",
        footprint=[(2.0, 2.0), (18.0, 2.0), (18.0, 18.0), (2.0, 18.0)],
        source_page=9,
        source_bbox=(20.0, 20.0, 180.0, 180.0),
        confidence=0.7,
        warnings=["heuristic-dense-profile:unknown_dense"],
    )


def _layout_with_feature(feature: LayoutElement) -> ExtractedLayout:
    return ExtractedLayout(
        id="layout-1",
        name="Layout 1",
        source_page=9,
        board_rect=(0.0, 0.0, 440.0, 600.0),
        deployment_zones=[
            LayoutElement(
                id="attacker",
                label="Attacker",
                kind="deployment",
                source_role="attacker",
                footprint=[(0.0, 0.0), (44.0, 0.0), (44.0, 10.0), (0.0, 10.0)],
                source_page=9,
                source_bbox=(0.0, 500.0, 440.0, 600.0),
            ),
            LayoutElement(
                id="defender",
                label="Defender",
                kind="deployment",
                source_role="defender",
                footprint=[(0.0, 50.0), (44.0, 50.0), (44.0, 60.0), (0.0, 60.0)],
                source_page=9,
                source_bbox=(0.0, 0.0, 440.0, 100.0),
            ),
        ],
        terrain_areas=[
            LayoutElement(
                id="area-1",
                label="Area 1",
                kind="terrain_area",
                footprint=[(0.0, 0.0), (20.0, 0.0), (20.0, 20.0), (0.0, 20.0)],
                source_page=9,
                source_bbox=(0.0, 0.0, 200.0, 200.0),
            )
        ],
        terrain_features=[feature],
    )
