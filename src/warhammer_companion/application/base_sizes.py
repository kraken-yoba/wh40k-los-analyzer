from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from math import isfinite, isnan

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.base_sizes import BaseSizeRecord, ModelFrameRecord
from warhammer_companion.domain.overlays import ToolkitWarning

BASE_SIZE_TOOLKIT_SCHEMA_VERSION = "base-size-toolkit/v0"


@dataclass(frozen=True)
class ManualModelFramePayload:
    model_frame: ModelFrameRecord
    base_record: BaseSizeRecord | None


def build_manual_model_frame_result(
    *,
    model_id: str,
    model_label: str,
    base_record_id: str,
    base_label: str,
    diameter_mm: float,
    operator_id: str,
    entered_at: datetime,
    reason: str,
    source_ref_ids: tuple[str, ...],
) -> ToolkitResult[ManualModelFramePayload]:
    input_hash = _manual_model_frame_hash(
        model_id=model_id,
        model_label=model_label,
        base_record_id=base_record_id,
        base_label=base_label,
        diameter_mm=diameter_mm,
        operator_id=operator_id,
        entered_at=entered_at,
        reason=reason,
        source_ref_ids=source_ref_ids,
    )
    suffix = input_hash.removeprefix("sha256:")[:12]
    try:
        base_record = BaseSizeRecord.manual_round_mm(
            record_id=base_record_id,
            label=base_label,
            diameter_mm=diameter_mm,
            operator_id=operator_id,
            entered_at=entered_at,
            reason=reason,
            source_ref_ids=source_ref_ids,
            reviewed_fields=("diameter_mm",),
        )
    except ValueError as exc:
        model_frame = ModelFrameRecord(model_id=model_id, label=model_label, base=None)
        return ToolkitResult(
            result_id=f"{model_id}:manual-model-frame:{suffix}",
            tool_id="manual_model_frame",
            input_hash=input_hash,
            readiness="blocked",
            payload=ManualModelFramePayload(model_frame=model_frame, base_record=None),
            warnings=(
                ToolkitWarning(
                    warning_id="invalid-base-dimension",
                    detail=str(exc),
                    source_ref_ids=source_ref_ids,
                ),
            ),
            block_reasons=(
                BlockReason(
                    reason_id="invalid-base-dimension",
                    detail=str(exc),
                    remediation="Enter a positive base dimension.",
                    source_ref_ids=source_ref_ids,
                ),
            ),
            source_ref_ids=source_ref_ids,
        )

    model_frame = ModelFrameRecord(
        model_id=model_id,
        label=model_label,
        base=base_record,
        source_ref_ids=source_ref_ids,
    )
    return ToolkitResult(
        result_id=f"{model_id}:manual-model-frame:{suffix}",
        tool_id="manual_model_frame",
        input_hash=input_hash,
        readiness="estimated",
        payload=ManualModelFramePayload(model_frame=model_frame, base_record=base_record),
        assumptions=base_record.assumptions,
        warnings=base_record.warnings,
        source_ref_ids=source_ref_ids,
    )


def _manual_model_frame_hash(
    *,
    model_id: str,
    model_label: str,
    base_record_id: str,
    base_label: str,
    diameter_mm: float,
    operator_id: str,
    entered_at: datetime,
    reason: str,
    source_ref_ids: tuple[str, ...],
) -> str:
    payload = {
        "base_label": base_label,
        "base_record_id": base_record_id,
        "diameter_mm": _canonical_float(diameter_mm),
        "entered_at": entered_at.isoformat(),
        "model_id": model_id,
        "model_label": model_label,
        "operator_id": operator_id,
        "reason": reason,
        "schema_version": BASE_SIZE_TOOLKIT_SCHEMA_VERSION,
        "source_ref_ids": sorted(set(source_ref_ids)),
        "tool_id": "manual_model_frame",
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _canonical_float(value: float) -> str:
    if isfinite(value):
        return f"{value:.6f}"
    if isnan(value):
        return "nan"
    if value > 0:
        return "inf"
    return "-inf"
