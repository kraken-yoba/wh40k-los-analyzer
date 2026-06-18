from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import Polygon

from warhammer_companion.ingestion.feature_categorizer import (
    CategorizerFeature,
    CategorizerPath,
    CategorizerRequest,
    CategorizerResults,
    FeatureCategorization,
)
from warhammer_companion.ingestion.terrain_feature_catalog import (
    FEATURE_CATALOG_VERSION,
    FeaturePosition,
)

CATALOG_CLASSIFIER_PROVIDER = "local_catalog_classifier"


def classify_categorizer_request(request: CategorizerRequest) -> CategorizerResults:
    return CategorizerResults(
        provider=CATALOG_CLASSIFIER_PROVIDER,
        catalog_version=FEATURE_CATALOG_VERSION,
        categorizations=[_classify_feature(feature) for feature in request.features],
    )


def write_catalog_categorizer_results(
    request_path: CategorizerPath,
    output_path: CategorizerPath,
) -> CategorizerResults:
    request = CategorizerRequest.model_validate_json(Path(request_path).read_text(encoding="utf-8"))
    results = classify_categorizer_request(request)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(results.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return results


def _classify_feature(feature: CategorizerFeature) -> FeatureCategorization:
    polygon = Polygon(feature.footprint)
    if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
        return _result(
            feature,
            type_id="solid-los-blocker",
            confidence=0.5,
            position="unknown",
            rationale="Invalid or empty feature polygon; kept as conservative LOS blocker.",
        )

    min_x, min_y, max_x, max_y = polygon.bounds
    width = max_x - min_x
    height = max_y - min_y
    short_side = min(width, height)
    long_side = max(width, height)
    aspect = long_side / max(short_side, 1e-9)
    fill_ratio = polygon.area / max(width * height, 1e-9)
    current_profile = feature.current_profile

    if aspect >= 4.0 and short_side <= 1.0:
        return _result(
            feature,
            type_id="solid-los-blocker",
            confidence=0.82,
            position="edge",
            rationale="Thin elongated dense feature is treated as a vertical wall strip.",
        )

    if fill_ratio >= 0.62 and aspect <= 2.8 and polygon.area >= 0.75:
        return _result(
            feature,
            type_id="floor-or-platform",
            confidence=0.74,
            position="center",
            rationale=(
                "Broad filled dense patch is likely a horizontal floor or platform, "
                "so it is retained for review but not used as an LOS blocker."
            ),
        )

    if fill_ratio <= 0.45 and polygon.area >= 0.75:
        if aspect <= 1.65:
            return _result(
                feature,
                type_id="ruined-wall-l",
                confidence=0.72,
                position="corner",
                rationale="Sparse compact dense geometry matches an L-shaped ruined wall.",
            )
        return _result(
            feature,
            type_id="ruined-wall-u",
            confidence=0.7,
            position="edge",
            rationale="Sparse elongated dense geometry matches a U-shaped ruined wall shell.",
        )

    if current_profile == "container_or_solid" or aspect >= 2.8:
        return _result(
            feature,
            type_id="armoured-container",
            confidence=0.72,
            position="edge" if aspect >= 2.8 else "center",
            rationale="Dense feature geometry is solid or container-like.",
        )

    if polygon.area < 0.75:
        return _result(
            feature,
            type_id="floor-or-platform",
            confidence=0.58,
            position="unknown",
            rationale="Small dense patch is treated as non-blocking review geometry.",
        )

    return _result(
        feature,
        type_id="solid-los-blocker",
        confidence=0.66,
        position="unknown",
        rationale="Fallback catalog classification keeps ambiguous dense geometry blocking.",
    )


def _result(
    feature: CategorizerFeature,
    *,
    type_id: str,
    confidence: float,
    position: FeaturePosition,
    rationale: str,
) -> FeatureCategorization:
    return FeatureCategorization(
        feature_id=feature.feature_id,
        feature_digest=feature.feature_digest,
        type_id=type_id,
        confidence=confidence,
        position=position,
        rationale=rationale,
    )
