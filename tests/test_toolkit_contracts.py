from __future__ import annotations

from typing import Any, cast

import pytest
from shapely.geometry import Polygon

from warhammer_companion.application.toolkit import (
    BlockReason,
    ExportMetadata,
    ToolkitResult,
    ValidationRecord,
)
from warhammer_companion.domain.overlays import MapOverlayLayer, ToolkitAssumption


def test_invalid_readiness_values_fail_explicitly() -> None:
    geometry = Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)])

    with pytest.raises(ValueError, match="Unknown toolkit readiness"):
        ToolkitResult[str](
            result_id="bad-readiness",
            tool_id="movement",
            input_hash="sha256:bad",
            readiness=cast(Any, "optimistic"),
            payload="diagnostic",
        )
    with pytest.raises(ValueError, match="Unknown toolkit readiness"):
        MapOverlayLayer(
            layer_id="bad-overlay",
            layer_kind="movement_reach",
            geometry=geometry,
            units="battlefield_inches",
            style_token="estimated-threat",
            label="Estimated reach",
            readiness=cast(Any, "optimistic"),
        )


def test_toolkit_result_readiness_controls_recommendation_language() -> None:
    blocked = ToolkitResult[None](
        result_id="blocked-los",
        tool_id="los",
        input_hash="sha256:blocked",
        readiness="blocked",
        payload=None,
        block_reasons=(BlockReason(reason_id="missing-base", detail="Base size is missing."),),
    )
    estimated = ToolkitResult[str](
        result_id="estimated-los",
        tool_id="los",
        input_hash="sha256:estimated",
        readiness="estimated",
        payload="diagnostic",
        assumptions=(ToolkitAssumption(assumption_id="2d", detail="2D geometry only."),),
    )
    trusted = ToolkitResult[str](
        result_id="trusted-los",
        tool_id="los",
        input_hash="sha256:trusted",
        readiness="trusted",
        payload="diagnostic",
        source_ref_ids=("core-rules-pdf",),
        validation_records=(
            ValidationRecord(
                validator_id="fixture",
                status="passed",
                detail="Fixture validation passed.",
            ),
        ),
        export_metadata=ExportMetadata(schema_version="toolkit-result/v0"),
    )

    assert blocked.is_blocked
    assert not blocked.is_usable
    assert not blocked.allows_recommendation_language()
    assert estimated.is_usable
    assert not estimated.allows_recommendation_language()
    assert trusted.is_usable
    assert trusted.allows_recommendation_language()


def test_trusted_result_requires_source_refs_and_passed_validation() -> None:
    with pytest.raises(ValueError, match="source refs"):
        ToolkitResult[str](
            result_id="trusted-without-source",
            tool_id="los",
            input_hash="sha256:trusted",
            readiness="trusted",
            payload="diagnostic",
            validation_records=(
                ValidationRecord(
                    validator_id="fixture",
                    status="passed",
                    detail="Fixture validation passed.",
                ),
            ),
        )

    with pytest.raises(ValueError, match="passed validation"):
        ToolkitResult[str](
            result_id="trusted-without-passed-validation",
            tool_id="los",
            input_hash="sha256:trusted",
            readiness="trusted",
            payload="diagnostic",
            source_ref_ids=("core-rules-pdf",),
            validation_records=(
                ValidationRecord(
                    validator_id="fixture",
                    status="warning",
                    detail="Fixture validation warned.",
                ),
            ),
        )


def test_blocked_result_requires_block_reason_and_no_overlays() -> None:
    overlay = MapOverlayLayer(
        layer_id="reach",
        layer_kind="movement_reach",
        geometry=Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]),
        units="battlefield_inches",
        style_token="estimated-threat",
        label="Estimated reach",
        readiness="estimated",
        source_ref_ids=("manual-measurement",),
    )

    with pytest.raises(ValueError, match="block reason"):
        ToolkitResult[None](
            result_id="blocked-without-reason",
            tool_id="movement",
            input_hash="sha256:blocked",
            readiness="blocked",
            payload=None,
        )
    with pytest.raises(ValueError, match="overlays"):
        ToolkitResult[None](
            result_id="blocked-with-overlay",
            tool_id="movement",
            input_hash="sha256:blocked",
            readiness="blocked",
            payload=None,
            overlays=(overlay,),
            block_reasons=(BlockReason(reason_id="missing-base", detail="Base size is missing."),),
        )


def test_overlay_readiness_cannot_exceed_result_readiness() -> None:
    overlay = MapOverlayLayer(
        layer_id="trusted-overlay",
        layer_kind="movement_reach",
        geometry=Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]),
        units="battlefield_inches",
        style_token="trusted-threat",
        label="Trusted reach",
        readiness="trusted",
    )

    with pytest.raises(ValueError, match="exceeds result readiness"):
        ToolkitResult[str](
            result_id="estimated-result",
            tool_id="movement",
            input_hash="sha256:estimated",
            readiness="estimated",
            payload="diagnostic",
            overlays=(overlay,),
        )


def test_map_overlay_layer_is_rendering_neutral_geometry() -> None:
    geometry = Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)])

    layer = MapOverlayLayer(
        layer_id="reach",
        layer_kind="movement_reach",
        geometry=geometry,
        units="battlefield_inches",
        style_token="estimated-threat",
        label="Estimated reach",
        readiness="estimated",
        source_ref_ids=("manual-measurement",),
    )

    assert layer.geometry.area == 4.0
    assert not layer.is_empty
    assert layer.source_ref_ids == ("manual-measurement",)
