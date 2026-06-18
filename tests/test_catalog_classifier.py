from __future__ import annotations

import json
from pathlib import Path

from warhammer_companion.ingestion.catalog_classifier import (
    classify_categorizer_request,
    write_catalog_categorizer_results,
)
from warhammer_companion.ingestion.feature_categorizer import (
    CategorizerFeature,
    CategorizerRequest,
)


def test_catalog_classifier_marks_filled_ruin_slab_as_floor_or_platform() -> None:
    request = CategorizerRequest(
        features=[
            _feature(
                "feature-1",
                footprint=[(2.0, 2.0), (8.0, 2.0), (8.0, 8.0), (2.0, 8.0)],
                current_profile="container_or_solid",
            )
        ]
    )

    results = classify_categorizer_request(request)

    assert results.categorizations[0].feature_id == "feature-1"
    assert results.categorizations[0].feature_digest == "digest-feature-1"
    assert results.categorizations[0].type_id == "floor-or-platform"
    assert results.categorizations[0].confidence >= 0.7


def test_catalog_classifier_keeps_thin_wall_strips_blocking() -> None:
    request = CategorizerRequest(
        features=[
            _feature(
                "feature-1",
                footprint=[(2.0, 2.0), (10.0, 2.0), (10.0, 2.5), (2.0, 2.5)],
                current_profile="ruined_wall_section",
            )
        ]
    )

    results = classify_categorizer_request(request)

    assert results.categorizations[0].type_id == "solid-los-blocker"
    assert results.categorizations[0].confidence >= 0.75


def test_catalog_classifier_maps_sparse_wall_shape_to_ruin_type() -> None:
    request = CategorizerRequest(
        features=[
            _feature(
                "feature-1",
                footprint=[
                    (2.0, 2.0),
                    (8.0, 2.0),
                    (8.0, 3.0),
                    (3.0, 3.0),
                    (3.0, 8.0),
                    (2.0, 8.0),
                ],
                current_profile="solid_los_blocker",
            )
        ]
    )

    results = classify_categorizer_request(request)

    assert results.categorizations[0].type_id == "ruined-wall-l"
    assert results.categorizations[0].position == "corner"


def test_catalog_classifier_uses_official_feature_codes_as_authoritative() -> None:
    request = CategorizerRequest(
        features=[
            _feature(
                "feature-1",
                footprint=[(2.0, 2.0), (8.0, 2.0), (8.0, 8.0), (2.0, 8.0)],
                current_profile="container_or_solid",
                official_feature_code="CD",
                current_wall_sides=["left", "right", "top"],
            )
        ]
    )

    results = classify_categorizer_request(request)

    assert results.categorizations[0].type_id == "ruined-wall-u"
    assert results.categorizations[0].wall_sides == ["left", "right", "top"]
    assert results.categorizations[0].confidence == 0.95


def test_write_catalog_categorizer_results_writes_artifact(tmp_path: Path) -> None:
    request_path = tmp_path / "visual-categorizer-request.json"
    results_path = tmp_path / "visual-categorizer-results.json"
    request = CategorizerRequest(
        features=[
            _feature(
                "feature-1",
                footprint=[(2.0, 2.0), (8.0, 2.0), (8.0, 8.0), (2.0, 8.0)],
                current_profile="container_or_solid",
            )
        ]
    )
    request_path.write_text(
        json.dumps(request.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )

    results = write_catalog_categorizer_results(request_path, results_path)

    payload = json.loads(results_path.read_text(encoding="utf-8"))
    assert results.categorizations[0].type_id == "floor-or-platform"
    assert payload["provider"] == "local_catalog_classifier"
    assert payload["categorizations"][0]["feature_id"] == "feature-1"


def _feature(
    feature_id: str,
    *,
    footprint: list[tuple[float, float]],
    current_profile: str,
    official_feature_code: str | None = None,
    current_wall_sides: list[str] | None = None,
) -> CategorizerFeature:
    return CategorizerFeature(
        feature_id=feature_id,
        feature_digest=f"digest-{feature_id}",
        feature_type="dense",
        current_profile=current_profile,
        official_feature_code=official_feature_code,
        current_wall_sides=current_wall_sides,
        terrain_area_id="terrain-1",
        source_page=9,
        source_bbox=(10.0, 10.0, 80.0, 80.0),
        footprint=footprint,
    )
