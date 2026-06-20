from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from warhammer_companion.domain.overlays import (
    ToolkitAssumption,
    ToolkitReadiness,
    ToolkitWarning,
)

SemanticsFreshnessState = Literal["current", "unknown", "stale"]
SemanticsCompatibilityState = Literal["compatible", "candidate", "incompatible", "unknown"]
SemanticsValidationStatus = Literal["passed", "warning", "failed", "not_run"]

_READINESS_ORDER: dict[ToolkitReadiness, int] = {
    "blocked": 0,
    "degraded": 1,
    "estimated": 2,
    "trusted": 3,
}


@dataclass(frozen=True, slots=True)
class FieldSourceRef:
    field_name: str
    source_ref_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SemanticsValidationRecord:
    validator_id: str
    status: SemanticsValidationStatus
    detail: str
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SemanticsBlockReason:
    reason_id: str
    detail: str
    remediation: str | None = None
    source_ref_ids: tuple[str, ...] = ()


class SemanticsRecord(Protocol):
    @property
    def readiness(self) -> ToolkitReadiness: ...

    @property
    def warnings(self) -> tuple[ToolkitWarning, ...]: ...

    @property
    def block_reasons(self) -> tuple[SemanticsBlockReason, ...]: ...

    @property
    def source_ref_ids(self) -> tuple[str, ...]: ...

    @property
    def validation_records(self) -> tuple[SemanticsValidationRecord, ...]: ...

    @property
    def assumptions(self) -> tuple[ToolkitAssumption, ...]: ...

    @property
    def freshness(self) -> SemanticsFreshnessState: ...

    @property
    def compatibility(self) -> SemanticsCompatibilityState: ...


@dataclass(frozen=True, slots=True)
class SemanticsReadinessReport:
    readiness: ToolkitReadiness
    warnings: tuple[ToolkitWarning, ...] = ()
    block_reasons: tuple[SemanticsBlockReason, ...] = ()
    assumptions: tuple[ToolkitAssumption, ...] = ()
    source_ref_ids: tuple[str, ...] = ()
    validation_records: tuple[SemanticsValidationRecord, ...] = ()

    def allows_trusted_claims(self) -> bool:
        return (
            self.readiness == "trusted"
            and not self.block_reasons
            and bool(self.source_ref_ids)
            and any(record.status == "passed" for record in self.validation_records)
        )


def field_source_ref_ids(
    field_source_refs: Iterable[FieldSourceRef],
    field_name: str,
) -> tuple[str, ...]:
    for field_ref in field_source_refs:
        if field_ref.field_name == field_name:
            return field_ref.source_ref_ids
    return ()


def report_semantics_readiness(
    *,
    base_records: Sequence[SemanticsRecord] = (),
    model_frames: Sequence[SemanticsRecord] = (),
    terrain_records: Sequence[SemanticsRecord] = (),
    source_pack_compatible: bool = True,
    source_freshness: SemanticsFreshnessState = "current",
    require_vertical_profile: bool = False,
) -> SemanticsReadinessReport:
    records = (*base_records, *model_frames, *terrain_records)
    warnings: list[ToolkitWarning] = []
    block_reasons: list[SemanticsBlockReason] = []
    assumptions: list[ToolkitAssumption] = []
    source_ref_ids: list[str] = []
    validation_records: list[SemanticsValidationRecord] = []
    readinesses: list[ToolkitReadiness] = [record.readiness for record in records]

    for record in records:
        warnings.extend(record.warnings)
        block_reasons.extend(record.block_reasons)
        assumptions.extend(record.assumptions)
        source_ref_ids.extend(record.source_ref_ids)
        validation_records.extend(record.validation_records)
        if record.readiness == "trusted":
            if not record.source_ref_ids:
                readinesses.append("degraded")
                warnings.append(
                    ToolkitWarning(
                        warning_id="trusted-source-refs-missing",
                        detail="Trusted semantics records require source references.",
                    )
                )
            if not any(validation.status == "passed" for validation in record.validation_records):
                readinesses.append("degraded")
                warnings.append(
                    ToolkitWarning(
                        warning_id="trusted-validation-missing",
                        detail=(
                            "Trusted semantics records require their own passed validation record."
                        ),
                        source_ref_ids=record.source_ref_ids,
                    )
                )
        if record.freshness == "stale":
            readinesses.append("blocked")
            block_reasons.append(
                SemanticsBlockReason(
                    reason_id="stale-source-pack",
                    detail="A semantics record uses stale source data.",
                    remediation="Refresh the source pack before running tactical checks.",
                    source_ref_ids=record.source_ref_ids,
                )
            )
        elif record.freshness == "unknown" and record.readiness == "trusted":
            readinesses.append("degraded")
            warnings.append(
                ToolkitWarning(
                    warning_id="source-freshness-unknown",
                    detail=(
                        "A trusted semantics record has unknown freshness; trusted tactical "
                        "claims are unavailable."
                    ),
                    source_ref_ids=record.source_ref_ids,
                )
            )
        if record.compatibility == "incompatible":
            readinesses.append("blocked")
            block_reasons.append(
                SemanticsBlockReason(
                    reason_id="incompatible-source-pack",
                    detail="A semantics record is incompatible with the active source pack.",
                    remediation="Refresh or select a compatible rules/base/terrain source pack.",
                    source_ref_ids=record.source_ref_ids,
                )
            )
        elif record.compatibility in {"candidate", "unknown"} and record.readiness == "trusted":
            readinesses.append("degraded")
            warnings.append(
                ToolkitWarning(
                    warning_id="source-compatibility-unproved",
                    detail=(
                        "A trusted semantics record does not have proven source compatibility."
                    ),
                    source_ref_ids=record.source_ref_ids,
                )
            )

    if terrain_records:
        warnings.append(
            ToolkitWarning(
                warning_id="terrain-traits-source-pending",
                detail=(
                    "Terrain category, visibility, movement, and height traits are source-pending."
                ),
            )
        )
        assumptions.append(
            ToolkitAssumption(
                assumption_id="map-packet-2d-terrain-semantics",
                detail=(
                    "Terrain semantics are inferred from current two-dimensional MapPacket "
                    "geometry and LOS flags."
                ),
            )
        )
    if require_vertical_profile:
        warnings.append(
            ToolkitWarning(
                warning_id="vertical-profile-source-pending",
                detail="Vertical and height interactions are not source-backed in this slice.",
            )
        )
    if not source_pack_compatible:
        readinesses.append("blocked")
        block_reasons.append(
            SemanticsBlockReason(
                reason_id="incompatible-source-pack",
                detail="The active source pack is not compatible with this semantics record.",
                remediation="Refresh or select a compatible rules/base/terrain source pack.",
            )
        )
    if source_freshness == "stale":
        readinesses.append("blocked")
        block_reasons.append(
            SemanticsBlockReason(
                reason_id="stale-source-pack",
                detail="The source pack is stale for tactical claims.",
                remediation="Refresh the source pack before running tactical checks.",
            )
        )
    elif source_freshness == "unknown":
        warnings.append(
            ToolkitWarning(
                warning_id="source-freshness-unknown",
                detail="Source freshness is unknown; trusted tactical claims are unavailable.",
            )
        )
        if readinesses and _minimum_readiness(readinesses) == "trusted":
            readinesses.append("degraded")

    if readinesses and _minimum_readiness(readinesses) == "trusted":
        if not source_ref_ids:
            readinesses.append("degraded")
            warnings.append(
                ToolkitWarning(
                    warning_id="trusted-source-refs-missing",
                    detail="Trusted semantics records require source references.",
                )
            )
        if not any(record.status == "passed" for record in validation_records):
            readinesses.append("degraded")
            warnings.append(
                ToolkitWarning(
                    warning_id="trusted-validation-missing",
                    detail="Trusted semantics records require a passed validation record.",
                )
            )

    readiness = _minimum_readiness(readinesses) if readinesses else "estimated"
    if block_reasons:
        readiness = "blocked"
    return SemanticsReadinessReport(
        readiness=readiness,
        warnings=_unique_warnings(warnings),
        block_reasons=_unique_block_reasons(block_reasons),
        assumptions=_unique_assumptions(assumptions),
        source_ref_ids=_unique_strings(source_ref_ids),
        validation_records=tuple(validation_records),
    )


def _minimum_readiness(readinesses: Iterable[ToolkitReadiness]) -> ToolkitReadiness:
    return min(readinesses, key=lambda readiness: _READINESS_ORDER[readiness])


def _unique_strings(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return tuple(unique)


def _unique_warnings(warnings: Iterable[ToolkitWarning]) -> tuple[ToolkitWarning, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[ToolkitWarning] = []
    for warning in warnings:
        key = (warning.warning_id, warning.detail)
        if key in seen:
            continue
        seen.add(key)
        unique.append(warning)
    return tuple(unique)


def _unique_assumptions(
    assumptions: Iterable[ToolkitAssumption],
) -> tuple[ToolkitAssumption, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[ToolkitAssumption] = []
    for assumption in assumptions:
        key = (assumption.assumption_id, assumption.detail)
        if key in seen:
            continue
        seen.add(key)
        unique.append(assumption)
    return tuple(unique)


def _unique_block_reasons(
    block_reasons: Iterable[SemanticsBlockReason],
) -> tuple[SemanticsBlockReason, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[SemanticsBlockReason] = []
    for reason in block_reasons:
        key = (reason.reason_id, reason.detail)
        if key in seen:
            continue
        seen.add(key)
        unique.append(reason)
    return tuple(unique)
