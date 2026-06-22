from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from warhammer_companion.domain.damage import DamageProbabilityRow
from warhammer_companion.domain.deployment_scorecard import DeploymentScorecardComponent
from warhammer_companion.domain.matchups import (
    PairingCell,
    PairingListEntry,
    PairingScenario,
    PairingScenarioRange,
)
from warhammer_companion.domain.missions import MissionPack, MissionRecord, MissionSourceRef
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.movement import (
    DEFAULT_MOVEMENT_PROFILE_ID,
    MOVEMENT_PROFILES,
    MovementProfile,
)
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
class DeploymentZoneSelectOption:
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
    movement_profile: str = DEFAULT_MOVEMENT_PROFILE_ID
    movement_profiles: list[MovementProfile] = field(
        default_factory=lambda: list(MOVEMENT_PROFILES)
    )
    movement_profile_label: str = "Ground non-mobile"
    effective_move: float = 0.0
    input_hash: str = ""


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
    movement_profile: str = DEFAULT_MOVEMENT_PROFILE_ID
    movement_profiles: list[MovementProfile] = field(
        default_factory=lambda: list(MOVEMENT_PROFILES)
    )
    movement_profile_label: str = "Ground non-mobile"
    effective_move: float = 0.0
    input_hash: str = ""


@dataclass(frozen=True)
class DeploymentExposureState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    packet_selector: PacketSelectorState
    deployment_zone_options: list[DeploymentZoneSelectOption]
    deployment_zone_id: str
    friendly_x: float
    friendly_y: float
    friendly_base: float
    enemy_x: float
    enemy_y: float
    enemy_base: float
    enemy_move: float
    enemy_threat: float
    enemy_mode: str
    exposure_mode: str
    enemy_threat_modes: list[str]
    exposure_modes: list[str]
    not_exposed_under_assumptions: bool
    threat_probability_at_center: float
    placement_reason_details: list[str]
    warning_details: list[str]
    map_svg: str
    enemy_movement_profile: str = DEFAULT_MOVEMENT_PROFILE_ID
    enemy_movement_profiles: list[MovementProfile] = field(
        default_factory=lambda: list(MOVEMENT_PROFILES)
    )
    enemy_movement_profile_label: str = "Ground non-mobile"
    enemy_effective_move: float = 0.0
    input_hash: str = ""


@dataclass(frozen=True)
class DeploymentScorecardState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    packet_selector: PacketSelectorState
    deployment_zone_options: list[DeploymentZoneSelectOption]
    deployment_zone_id: str
    friendly_x: float
    friendly_y: float
    friendly_base: float
    enemy_x: float
    enemy_y: float
    enemy_base: float
    enemy_move: float
    enemy_threat: float
    enemy_mode: str
    exposure_mode: str
    turn_order: str
    enemy_threat_modes: list[str]
    exposure_modes: list[str]
    turn_order_options: list[str]
    readiness: str
    is_blocked: bool
    not_exposed_under_assumptions: bool
    threat_probability_at_center: float
    components: list[DeploymentScorecardComponent]
    block_reason_details: list[str]
    warning_details: list[str]
    map_svg: str
    enemy_movement_profile: str = DEFAULT_MOVEMENT_PROFILE_ID
    enemy_movement_profiles: list[MovementProfile] = field(
        default_factory=lambda: list(MOVEMENT_PROFILES)
    )
    enemy_movement_profile_label: str = "Ground non-mobile"
    enemy_effective_move: float = 0.0
    input_hash: str = ""


@dataclass(frozen=True)
class DamageProfileState:
    attacks: float
    hit_target: int
    wound_target: int
    save_target: int
    damage_per_unsaved_wound: float
    target_wounds_per_model: float
    target_model_count: float
    is_blocked: bool
    expected_hits: float
    expected_wounds: float
    expected_unsaved_wounds: float
    expected_damage: float
    expected_models_destroyed: float
    probability_destroying_at_least_one_model: float
    unsaved_wound_distribution: list[DamageProbabilityRow]
    models_destroyed_distribution: list[DamageProbabilityRow]
    warning_details: list[str]
    block_reason_details: list[str]


@dataclass(frozen=True)
class MissionPackState:
    readiness: str
    mission_count: int
    source_refs: list[MissionSourceRef]
    primary_missions: list[MissionRecord]
    warning_details: list[str]
    pack: MissionPack


@dataclass(frozen=True)
class TeamPairingMatrixState:
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    packet_selector: PacketSelectorState
    friendly_lists_text: str
    opponent_lists_text: str
    readiness: str
    is_blocked: bool
    friendly_lists: list[PairingListEntry]
    opponent_lists: list[PairingListEntry]
    scenarios: list[PairingScenario]
    cells: list[PairingCell]
    ranges: list[PairingScenarioRange]
    warning_details: list[str]
    block_reason_details: list[str]


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
