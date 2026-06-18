from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PipelineStageStatus(StrEnum):
    NOT_STARTED = "not_started"
    READY = "ready"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PipelineStage:
    id: str
    label: str
    status: PipelineStageStatus
    note: str


def current_pipeline_status() -> list[PipelineStage]:
    return [
        PipelineStage(
            id="download_sources",
            label="Download official PDFs",
            status=PipelineStageStatus.READY,
            note="Source registry and CLI downloader are available.",
        ),
        PipelineStage(
            id="extract_footprints",
            label="Extract terrain footprint library",
            status=PipelineStageStatus.READY,
            note="Vector-first footprint extraction with raster fallback is wired.",
        ),
        PipelineStage(
            id="extract_layouts",
            label="Extract event companion layouts",
            status=PipelineStageStatus.READY,
            note="Board, deployment, terrain footprint, and raster feature extraction is wired.",
        ),
        PipelineStage(
            id="generate_packets",
            label="Generate normalized map packets",
            status=PipelineStageStatus.READY,
            note="Official layouts can be converted into validated map packet JSON.",
        ),
        PipelineStage(
            id="visual_review",
            label="Visual AI sanity review",
            status=PipelineStageStatus.READY,
            note="Codex visual categorizer artifacts and account status are wired.",
        ),
    ]
