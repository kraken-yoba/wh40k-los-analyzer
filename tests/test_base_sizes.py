from __future__ import annotations

from datetime import UTC, datetime
from math import inf, nan

import pytest

from warhammer_companion.application.base_sizes import build_manual_model_frame_result
from warhammer_companion.domain.base_sizes import (
    BaseGeometry,
    BaseSizeRecord,
    ManualUnitFootprint,
    ModelFrameRecord,
)
from warhammer_companion.domain.semantics import (
    SemanticsValidationRecord,
    report_semantics_readiness,
)

ENTERED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)


def test_manual_round_base_normalizes_mm_to_inches_and_remains_estimated() -> None:
    record = BaseSizeRecord.manual_round_mm(
        record_id="base-40mm",
        label="40mm round base",
        diameter_mm=40.0,
        operator_id="local-user",
        entered_at=ENTERED_AT,
        reason="Manual setup measurement.",
        source_ref_ids=("manual-entry:setup",),
        reviewed_fields=("diameter_mm",),
    )

    assert record.readiness == "estimated"
    assert record.source_kind == "manual_entry"
    assert record.freshness == "current"
    assert record.compatibility == "candidate"
    assert record.geometry.shape == "round"
    assert record.geometry.diameter_inches == pytest.approx(40.0 / 25.4)
    assert record.manual_entry is not None
    assert record.manual_entry.original_units == "mm"
    assert record.manual_entry.operator_id == "local-user"
    assert record.field_source_ref_ids("diameter_inches") == ("manual-entry:setup",)
    assert {warning.warning_id for warning in record.warnings} == {"manual-base-size"}
    assert not report_semantics_readiness(base_records=(record,)).allows_trusted_claims()


def test_unknown_base_blocks_trusted_claims() -> None:
    record = BaseSizeRecord.unknown(record_id="base-missing", label="Missing base")
    report = report_semantics_readiness(base_records=(record,))

    assert record.readiness == "blocked"
    assert report.readiness == "blocked"
    assert not report.allows_trusted_claims()
    assert any(reason.reason_id == "missing-base-size" for reason in report.block_reasons)


def test_base_geometry_rejects_non_positive_dimensions() -> None:
    with pytest.raises(ValueError, match="positive"):
        BaseGeometry.round(diameter_inches=0.0)


@pytest.mark.parametrize("diameter_mm", [nan, inf])
def test_manual_round_base_rejects_non_finite_dimensions(diameter_mm: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        BaseSizeRecord.manual_round_mm(
            record_id="base-invalid",
            label="Invalid round base",
            diameter_mm=diameter_mm,
            operator_id="local-user",
            entered_at=ENTERED_AT,
            reason="Manual setup measurement.",
            source_ref_ids=("manual-entry:setup",),
            reviewed_fields=("diameter_mm",),
        )


@pytest.mark.parametrize(("length_mm", "width_mm"), [(nan, 42.0), (75.0, inf)])
def test_manual_oval_base_rejects_non_finite_dimensions(
    length_mm: float,
    width_mm: float,
) -> None:
    with pytest.raises(ValueError, match="finite"):
        BaseSizeRecord.manual_oval_mm(
            record_id="base-invalid",
            label="Invalid oval base",
            length_mm=length_mm,
            width_mm=width_mm,
            operator_id="local-user",
            entered_at=ENTERED_AT,
            reason="Manual setup measurement.",
            source_ref_ids=("manual-entry:setup",),
            reviewed_fields=("length_mm", "width_mm"),
        )


def test_manual_model_frame_result_blocks_invalid_dimensions() -> None:
    result = build_manual_model_frame_result(
        model_id="m1",
        model_label="Model 1",
        base_record_id="base-invalid",
        base_label="Invalid base",
        diameter_mm=0.0,
        operator_id="local-user",
        entered_at=ENTERED_AT,
        reason="Manual setup measurement.",
        source_ref_ids=("manual-entry:setup",),
    )

    assert result.readiness == "blocked"
    assert result.is_blocked
    assert not result.overlays
    assert not result.allows_recommendation_language()
    assert any(reason.reason_id == "invalid-base-dimension" for reason in result.block_reasons)


@pytest.mark.parametrize("diameter_mm", [nan, inf])
def test_manual_model_frame_result_blocks_non_finite_dimensions(diameter_mm: float) -> None:
    result = build_manual_model_frame_result(
        model_id="m1",
        model_label="Model 1",
        base_record_id="base-invalid",
        base_label="Invalid base",
        diameter_mm=diameter_mm,
        operator_id="local-user",
        entered_at=ENTERED_AT,
        reason="Manual setup measurement.",
        source_ref_ids=("manual-entry:setup",),
    )

    assert result.readiness == "blocked"
    assert result.is_blocked
    assert not result.overlays
    assert not result.allows_recommendation_language()
    assert any(reason.reason_id == "invalid-base-dimension" for reason in result.block_reasons)


def test_manual_model_frame_result_hash_changes_with_base_size() -> None:
    smaller = build_manual_model_frame_result(
        model_id="m1",
        model_label="Model 1",
        base_record_id="base-32mm",
        base_label="32mm round base",
        diameter_mm=32.0,
        operator_id="local-user",
        entered_at=ENTERED_AT,
        reason="Manual setup measurement.",
        source_ref_ids=("manual-entry:setup",),
    )
    larger = build_manual_model_frame_result(
        model_id="m1",
        model_label="Model 1",
        base_record_id="base-40mm",
        base_label="40mm round base",
        diameter_mm=40.0,
        operator_id="local-user",
        entered_at=ENTERED_AT,
        reason="Manual setup measurement.",
        source_ref_ids=("manual-entry:setup",),
    )

    assert smaller.readiness == "estimated"
    assert larger.readiness == "estimated"
    assert smaller.input_hash != larger.input_hash
    assert not smaller.allows_recommendation_language()
    assert not larger.allows_recommendation_language()


def test_non_round_frame_records_can_be_represented_without_los_changes() -> None:
    record = BaseSizeRecord.manual_oval_mm(
        record_id="base-75x42mm",
        label="75x42mm oval base",
        length_mm=75.0,
        width_mm=42.0,
        operator_id="local-user",
        entered_at=ENTERED_AT,
        reason="Manual setup measurement.",
        source_ref_ids=("manual-entry:setup",),
        reviewed_fields=("length_mm", "width_mm"),
    )
    frame = ModelFrameRecord(model_id="m1", label="Oval model", base=record)

    assert frame.base is record
    assert record.geometry.shape == "oval"
    assert record.geometry.length_inches == pytest.approx(75.0 / 25.4)
    assert record.geometry.width_inches == pytest.approx(42.0 / 25.4)
    assert frame.readiness_report().readiness == "estimated"


def test_model_frame_report_preserves_nested_base_provenance() -> None:
    base = BaseSizeRecord(
        record_id="trusted-base",
        label="Trusted base",
        source_kind="profile_pack",
        geometry=BaseGeometry.round(diameter_inches=1.57),
        readiness="trusted",
        source_ref_ids=("profile-pack:base-size",),
        freshness="current",
        compatibility="compatible",
        validation_records=(
            SemanticsValidationRecord(
                validator_id="base-pack-review",
                status="passed",
                detail="Base profile validation passed.",
                source_ref_ids=("profile-pack:base-size",),
            ),
        ),
    )
    frame = ModelFrameRecord(model_id="m1", label="Model 1", base=base)
    report = frame.readiness_report()

    assert report.readiness == "trusted"
    assert report.source_ref_ids == ("profile-pack:base-size",)
    assert report.validation_records == base.validation_records
    assert report.allows_trusted_claims()


def test_manual_unit_footprint_reports_missing_model_base() -> None:
    ready_model = ModelFrameRecord(
        model_id="m1",
        label="Model 1",
        base=BaseSizeRecord.manual_round_mm(
            record_id="base-40mm",
            label="40mm round base",
            diameter_mm=40.0,
            operator_id="local-user",
            entered_at=ENTERED_AT,
            reason="Manual setup measurement.",
            source_ref_ids=("manual-entry:setup",),
            reviewed_fields=("diameter_mm",),
        ),
    )
    missing_model = ModelFrameRecord(model_id="m2", label="Model 2", base=None)

    footprint = ManualUnitFootprint(
        unit_id="unit-1",
        label="Manual unit",
        models=(ready_model, missing_model),
    )
    report = footprint.readiness_report()

    assert report.readiness == "blocked"
    assert not report.allows_trusted_claims()
    assert any(reason.reason_id == "missing-base-size" for reason in report.block_reasons)
