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
            status=PipelineStageStatus.NOT_STARTED,
            note="Next step: render PDF pages, detect contours, snap polygons.",
        ),
        PipelineStage(
            id="extract_layouts",
            label="Extract event companion layouts",
            status=PipelineStageStatus.NOT_STARTED,
            note="Next step: identify footprint instances and measurement labels.",
        ),
        PipelineStage(
            id="generate_packets",
            label="Generate normalized map packets",
            status=PipelineStageStatus.NOT_STARTED,
            note="Packet schema exists; persistence is not wired yet.",
        ),
        PipelineStage(
            id="visual_review",
            label="Visual AI sanity review",
            status=PipelineStageStatus.BLOCKED,
            note="Codex/vision backend integration is intentionally a later boundary.",
        ),
    ]
