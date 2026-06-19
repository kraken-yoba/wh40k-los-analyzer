from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.ingestion.packet_builder import IngestionReport
from warhammer_companion.ingestion.pipeline import PipelineStage
from warhammer_companion.ingestion.sources import OfficialSource
from warhammer_companion.integrations.codex_backend import CodexBackendStatus


@dataclass(frozen=True)
class PacketSelectOption:
    id: str
    label: str


@dataclass(frozen=True)
class PacketSelectGroup:
    label: str
    options: list[PacketSelectOption]


@dataclass(frozen=True)
class SettingsState:
    app_backend_status: str
    app_backend_detail: str
    codex_status: CodexBackendStatus


@dataclass(frozen=True)
class MapDataState:
    packets: list[MapPacket]
    deletable_packet_ids: set[str]
    sources: Sequence[OfficialSource]
    pipeline: list[PipelineStage]
    report: IngestionReport | None


@dataclass(frozen=True)
class ViewerState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    map_svg: str


@dataclass(frozen=True)
class HeatmapState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    selected_zone_id: str
    selected_source: str
    selected_offset_inches: int
    offset_options: list[int]
    map_svg: str


@dataclass(frozen=True)
class LosCheckerState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    x: float
    y: float
    base: float
    map_svg: str
