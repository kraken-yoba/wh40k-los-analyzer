from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Literal

from warhammer_companion.domain.overlays import (
    ToolkitAssumption,
    ToolkitReadiness,
    ToolkitWarning,
)
from warhammer_companion.domain.semantics import (
    FieldSourceRef,
    SemanticsBlockReason,
    SemanticsCompatibilityState,
    SemanticsFreshnessState,
    SemanticsReadinessReport,
    SemanticsValidationRecord,
    field_source_ref_ids,
    report_semantics_readiness,
)

MM_PER_INCH = 25.4

BaseShape = Literal["round", "oval", "rectangle", "hull", "custom"]
BaseSourceKind = Literal[
    "manual_entry", "profile_pack", "roster_snapshot", "source_pending", "unknown"
]
SUPPORTED_BASE_SHAPES: frozenset[BaseShape] = frozenset(
    ("round", "oval", "rectangle", "hull", "custom")
)


@dataclass(frozen=True, slots=True)
class ManualEntryProvenance:
    operator_id: str
    entered_at: datetime
    reason: str
    reviewed_fields: tuple[str, ...]
    original_units: Literal["mm", "inches"]
    override_history: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BaseGeometry:
    shape: BaseShape
    diameter_inches: float | None = None
    length_inches: float | None = None
    width_inches: float | None = None

    @classmethod
    def round(cls, *, diameter_inches: float) -> BaseGeometry:
        return cls(shape="round", diameter_inches=diameter_inches)

    @classmethod
    def oval(cls, *, length_inches: float, width_inches: float) -> BaseGeometry:
        return cls(shape="oval", length_inches=length_inches, width_inches=width_inches)

    def __post_init__(self) -> None:
        if self.shape not in SUPPORTED_BASE_SHAPES:
            raise ValueError(f"unknown base geometry shape: {self.shape}")
        if self.shape in {"hull", "custom"}:
            raise ValueError(
                f"{self.shape} base geometry is unsupported without a footprint policy"
            )
        if self.shape == "round":
            _require_positive("diameter", self.diameter_inches)
        if self.shape in {"oval", "rectangle"}:
            _require_positive("length", self.length_inches)
            _require_positive("width", self.width_inches)


@dataclass(frozen=True, slots=True)
class BaseSizeRecord:
    record_id: str
    label: str
    source_kind: BaseSourceKind
    geometry: BaseGeometry | None
    readiness: ToolkitReadiness
    source_ref_ids: tuple[str, ...] = ()
    field_source_refs: tuple[FieldSourceRef, ...] = ()
    freshness: SemanticsFreshnessState = "unknown"
    compatibility: SemanticsCompatibilityState = "unknown"
    validation_records: tuple[SemanticsValidationRecord, ...] = ()
    manual_entry: ManualEntryProvenance | None = None
    assumptions: tuple[ToolkitAssumption, ...] = ()
    warnings: tuple[ToolkitWarning, ...] = ()
    block_reasons: tuple[SemanticsBlockReason, ...] = ()

    @classmethod
    def manual_round_mm(
        cls,
        *,
        record_id: str,
        label: str,
        diameter_mm: float,
        operator_id: str,
        entered_at: datetime,
        reason: str,
        source_ref_ids: tuple[str, ...],
        reviewed_fields: tuple[str, ...],
        override_history: tuple[str, ...] = (),
    ) -> BaseSizeRecord:
        geometry = BaseGeometry.round(diameter_inches=diameter_mm / MM_PER_INCH)
        return cls(
            record_id=record_id,
            label=label,
            source_kind="manual_entry",
            geometry=geometry,
            readiness="estimated",
            source_ref_ids=source_ref_ids,
            field_source_refs=(
                FieldSourceRef("diameter_mm", source_ref_ids),
                FieldSourceRef("diameter_inches", source_ref_ids),
                FieldSourceRef("shape", source_ref_ids),
            ),
            freshness="current",
            compatibility="candidate",
            manual_entry=ManualEntryProvenance(
                operator_id=operator_id,
                entered_at=entered_at,
                reason=reason,
                reviewed_fields=reviewed_fields,
                original_units="mm",
                override_history=override_history,
            ),
            assumptions=(
                ToolkitAssumption(
                    assumption_id="manual-base-size",
                    detail="Base size was manually entered and is not source-authoritative.",
                    source_ref_ids=source_ref_ids,
                ),
            ),
            warnings=(
                ToolkitWarning(
                    warning_id="manual-base-size",
                    detail="Manual base size supports diagnostics only, not trusted legal claims.",
                    source_ref_ids=source_ref_ids,
                ),
            ),
        )

    @classmethod
    def manual_oval_mm(
        cls,
        *,
        record_id: str,
        label: str,
        length_mm: float,
        width_mm: float,
        operator_id: str,
        entered_at: datetime,
        reason: str,
        source_ref_ids: tuple[str, ...],
        reviewed_fields: tuple[str, ...],
        override_history: tuple[str, ...] = (),
    ) -> BaseSizeRecord:
        geometry = BaseGeometry.oval(
            length_inches=length_mm / MM_PER_INCH,
            width_inches=width_mm / MM_PER_INCH,
        )
        return cls(
            record_id=record_id,
            label=label,
            source_kind="manual_entry",
            geometry=geometry,
            readiness="estimated",
            source_ref_ids=source_ref_ids,
            field_source_refs=(
                FieldSourceRef("length_mm", source_ref_ids),
                FieldSourceRef("length_inches", source_ref_ids),
                FieldSourceRef("width_mm", source_ref_ids),
                FieldSourceRef("width_inches", source_ref_ids),
                FieldSourceRef("shape", source_ref_ids),
            ),
            freshness="current",
            compatibility="candidate",
            manual_entry=ManualEntryProvenance(
                operator_id=operator_id,
                entered_at=entered_at,
                reason=reason,
                reviewed_fields=reviewed_fields,
                original_units="mm",
                override_history=override_history,
            ),
            assumptions=(
                ToolkitAssumption(
                    assumption_id="manual-base-size",
                    detail="Base size was manually entered and is not source-authoritative.",
                    source_ref_ids=source_ref_ids,
                ),
            ),
            warnings=(
                ToolkitWarning(
                    warning_id="manual-base-size",
                    detail="Manual base size supports diagnostics only, not trusted legal claims.",
                    source_ref_ids=source_ref_ids,
                ),
            ),
        )

    @classmethod
    def unknown(cls, *, record_id: str, label: str) -> BaseSizeRecord:
        return cls(
            record_id=record_id,
            label=label,
            source_kind="unknown",
            geometry=None,
            readiness="blocked",
            block_reasons=(
                SemanticsBlockReason(
                    reason_id="missing-base-size",
                    detail="Base size is required before legal or safe claims can be made.",
                    remediation="Enter a manual base size or resolve the model profile.",
                ),
            ),
            warnings=(
                ToolkitWarning(
                    warning_id="missing-base-size",
                    detail="Base size is missing.",
                ),
            ),
        )

    def field_source_ref_ids(self, field_name: str) -> tuple[str, ...]:
        return field_source_ref_ids(self.field_source_refs, field_name)


@dataclass(frozen=True, slots=True)
class ModelFrameRecord:
    model_id: str
    label: str
    base: BaseSizeRecord | None
    source_ref_ids: tuple[str, ...] = ()
    validation_records: tuple[SemanticsValidationRecord, ...] = ()
    assumptions: tuple[ToolkitAssumption, ...] = ()

    def __post_init__(self) -> None:
        if self.base is None:
            return
        object.__setattr__(
            self,
            "source_ref_ids",
            _unique_strings((*self.source_ref_ids, *self.base.source_ref_ids)),
        )
        object.__setattr__(
            self,
            "validation_records",
            (*self.validation_records, *self.base.validation_records),
        )
        object.__setattr__(
            self,
            "assumptions",
            (*self.assumptions, *self.base.assumptions),
        )

    @property
    def readiness(self) -> ToolkitReadiness:
        if self.base is None:
            return "blocked"
        return self.base.readiness

    @property
    def warnings(self) -> tuple[ToolkitWarning, ...]:
        if self.base is None:
            return (
                ToolkitWarning(
                    warning_id="missing-base-size",
                    detail=f"Model frame {self.model_id} has no resolved base size.",
                ),
            )
        return self.base.warnings

    @property
    def block_reasons(self) -> tuple[SemanticsBlockReason, ...]:
        if self.base is None:
            return (
                SemanticsBlockReason(
                    reason_id="missing-base-size",
                    detail=f"Model frame {self.model_id} has no resolved base size.",
                    remediation="Enter a manual base size or resolve the model profile.",
                ),
            )
        return self.base.block_reasons

    @property
    def freshness(self) -> SemanticsFreshnessState:
        if self.base is None:
            return "unknown"
        return self.base.freshness

    @property
    def compatibility(self) -> SemanticsCompatibilityState:
        if self.base is None:
            return "unknown"
        return self.base.compatibility

    def readiness_report(self) -> SemanticsReadinessReport:
        return report_semantics_readiness(model_frames=(self,))


@dataclass(frozen=True, slots=True)
class ManualUnitFootprint:
    unit_id: str
    label: str
    models: tuple[ModelFrameRecord, ...]
    source_ref_ids: tuple[str, ...] = ()

    def readiness_report(self) -> SemanticsReadinessReport:
        if not self.models:
            return SemanticsReadinessReport(
                readiness="blocked",
                warnings=(
                    ToolkitWarning(
                        warning_id="missing-unit-models",
                        detail=f"Manual unit footprint {self.unit_id} has no models.",
                        source_ref_ids=self.source_ref_ids,
                    ),
                ),
                block_reasons=(
                    SemanticsBlockReason(
                        reason_id="missing-unit-models",
                        detail=(
                            f"Manual unit footprint {self.unit_id} requires at least one model."
                        ),
                        remediation="Add at least one model frame before running toolkit checks.",
                        source_ref_ids=self.source_ref_ids,
                    ),
                ),
                source_ref_ids=self.source_ref_ids,
            )
        report = report_semantics_readiness(model_frames=self.models)
        if not self.source_ref_ids:
            return report
        return SemanticsReadinessReport(
            readiness=report.readiness,
            warnings=report.warnings,
            block_reasons=report.block_reasons,
            assumptions=report.assumptions,
            source_ref_ids=_unique_strings((*report.source_ref_ids, *self.source_ref_ids)),
            validation_records=report.validation_records,
        )


def _require_positive(field_name: str, value: float | None) -> None:
    if value is None:
        raise ValueError(f"{field_name} must be positive")
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    if value <= 0.0:
        raise ValueError(f"{field_name} must be positive")


def _unique_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return tuple(unique)
