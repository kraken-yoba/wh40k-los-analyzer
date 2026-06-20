from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, get_args

from warhammer_companion.domain.overlays import (
    MapOverlayLayer,
    ToolkitAssumption,
    ToolkitReadiness,
    ToolkitWarning,
)

READINESS_ORDER: dict[ToolkitReadiness, int] = {
    "blocked": 0,
    "degraded": 1,
    "estimated": 2,
    "trusted": 3,
}


@dataclass(frozen=True, slots=True)
class BlockReason:
    reason_id: str
    detail: str
    remediation: str | None = None
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationRecord:
    validator_id: str
    status: Literal["passed", "warning", "failed", "not_run"]
    detail: str
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExportMetadata:
    schema_version: str = "toolkit-result/v0"
    content_type: str = "application/json"
    generated_by: str = "warhammer-companion"


@dataclass(frozen=True, slots=True)
class ToolkitResult[PayloadT]:
    result_id: str
    tool_id: str
    input_hash: str
    readiness: ToolkitReadiness
    payload: PayloadT
    overlays: tuple[MapOverlayLayer, ...] = ()
    assumptions: tuple[ToolkitAssumption, ...] = ()
    warnings: tuple[ToolkitWarning, ...] = ()
    block_reasons: tuple[BlockReason, ...] = ()
    source_ref_ids: tuple[str, ...] = ()
    validation_records: tuple[ValidationRecord, ...] = ()
    export_metadata: ExportMetadata = field(default_factory=ExportMetadata)

    def __post_init__(self) -> None:
        if self.readiness not in get_args(ToolkitReadiness):
            raise ValueError(f"Unknown toolkit readiness: {self.readiness}")
        if self.readiness == "blocked" and not self.block_reasons:
            raise ValueError("blocked toolkit results require at least one block reason")
        if self.readiness == "blocked" and self.overlays:
            raise ValueError("blocked toolkit results cannot include tactical overlays")
        if self.readiness == "trusted" and not self.source_ref_ids:
            raise ValueError("trusted toolkit results require source refs")
        if self.readiness == "trusted" and not any(
            record.status == "passed" for record in self.validation_records
        ):
            raise ValueError("trusted toolkit results require a passed validation record")

        result_rank = READINESS_ORDER[self.readiness]
        for overlay in self.overlays:
            if READINESS_ORDER[overlay.readiness] > result_rank:
                raise ValueError("overlay readiness exceeds result readiness")

    @property
    def is_blocked(self) -> bool:
        return self.readiness == "blocked"

    @property
    def is_usable(self) -> bool:
        return self.readiness in {"trusted", "estimated", "degraded"} and not self.is_blocked

    def allows_recommendation_language(self) -> bool:
        return self.readiness == "trusted"
