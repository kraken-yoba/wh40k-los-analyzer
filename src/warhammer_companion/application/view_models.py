from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.threat import ThreatDiceOutcome
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
class PacketLayoutOption:
    packet_id: str
    variant: str
    label: str
    detail: str


@dataclass(frozen=True)
class PacketSelectorState:
    player_a_options: list[str]
    player_b_options: list[str]
    layout_options: list[PacketLayoutOption]
    selected_player_a: str
    selected_player_b: str
    selected_layout_variant: str
    selected_packet_id: str


@dataclass(frozen=True)
class TerrainSelectOption:
    id: str
    label: str


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
    packet_selector: PacketSelectorState
    map_svg: str


@dataclass(frozen=True)
class HeatmapState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    packet_selector: PacketSelectorState
    selected_zone_id: str
    selected_source: str
    selected_offset_inches: int
    offset_options: list[int]
    map_svg: str


@dataclass(frozen=True)
class LosCheckerState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    packet_selector: PacketSelectorState
    x: float
    y: float
    base: float
    map_svg: str


@dataclass(frozen=True)
class MovementReachState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    packet_selector: PacketSelectorState
    start_x: float
    start_y: float
    target_x: float
    target_y: float
    base: float
    move: float
    mode: str
    movement_modes: list[str]
    endpoint_estimated_reachable: bool
    endpoint_reason_details: list[str]
    map_svg: str


@dataclass(frozen=True)
class ThreatRangeState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    packet_selector: PacketSelectorState
    source_x: float
    source_y: float
    target_x: float
    target_y: float
    base: float
    move: float
    threat: float
    mode: str
    threat_modes: list[str]
    measurement_convention: str
    target_probability: float
    distribution: list[ThreatDiceOutcome]
    warning_details: list[str]
    map_svg: str


@dataclass(frozen=True)
class HiddenCoverageState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    packet_selector: PacketSelectorState
    terrain_options: list[TerrainSelectOption]
    selected_terrain_area_id: str
    selected_detection_range: int
    detection_range_options: list[int]
    map_svg: str
