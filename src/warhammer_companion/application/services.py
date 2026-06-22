from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Protocol

from warhammer_companion.application.damage_profile import build_damage_profile_toolkit_result
from warhammer_companion.application.deployment_exposure import (
    build_deployment_exposure_toolkit_result,
)
from warhammer_companion.application.los_toolkit import (
    LosCheckerToolkitPayload,
    build_los_checker_toolkit_result,
)
from warhammer_companion.application.movement_reach import build_movement_reach_toolkit_result
from warhammer_companion.application.threat_range import build_threat_range_toolkit_result
from warhammer_companion.application.toolkit import ToolkitResult
from warhammer_companion.application.view_models import (
    DamageProfileState,
    DeploymentExposureState,
    DeploymentZoneSelectOption,
    HeatmapState,
    HiddenCoverageState,
    LosCheckerState,
    MapDataState,
    MovementReachState,
    PacketLayoutOption,
    PacketSelectGroup,
    PacketSelectOption,
    PacketSelectorState,
    SettingsState,
    TerrainSelectOption,
    ThreatRangeState,
    ViewerState,
)
from warhammer_companion.domain.damage import (
    DEFAULT_DAMAGE_PROFILE_INPUT,
    DEFAULT_TARGET_PROFILE_INPUT,
    DamageEstimatePayload,
)
from warhammer_companion.domain.exposure import (
    EXPOSURE_MODES,
    DeploymentExposurePayload,
    exposure_mode_includes_los,
    exposure_mode_includes_threat,
)
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.movement import MOVEMENT_MODES, MovementReachPayload
from warhammer_companion.domain.repository import MapRepository
from warhammer_companion.domain.threat import THREAT_MODES, ThreatRangePayload
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.packet_builder import IngestionReport, run_official_ingestion
from warhammer_companion.ingestion.pipeline import PipelineStage, current_pipeline_status
from warhammer_companion.ingestion.sources import OFFICIAL_SOURCES, OfficialSource
from warhammer_companion.integrations.codex_backend import (
    CodexBackend,
    CodexBackendStatus,
    CodexLoginStart,
)
from warhammer_companion.los.geometry import (
    clamp_base_center,
    heatmap_exclusion_zone,
    heatmap_visibility_polygons_from_deployment_edge,
    heatmap_visibility_polygons_from_deployment_zone,
    hidden_coverage_from_terrain_area,
    safe_heatmap_regions,
)
from warhammer_companion.rendering.svg import render_map_svg


class ReloadableMapRepository(MapRepository, Protocol):
    def reload(self) -> None: ...


IngestionRunner = Callable[..., IngestionReport]
PipelineStatusProvider = Callable[[], list[PipelineStage]]
HeatmapCacheKey = tuple[str, str, str, int]
HIDDEN_DETECTION_RANGE_OPTIONS = [12, 15, 18]
HIDDEN_COVERAGE_OBSERVER_GRID_STEP = 1.0
HIDDEN_COVERAGE_SAMPLE_STEP = 2.0

APP_BACKEND_STATUS = "python ingestion backend ready"
APP_BACKEND_DETAIL = (
    "Official PDF extraction, LOS geometry, and visual categorizer artifacts "
    "run through Python service boundaries."
)


class WarhammerCompanionService:
    def __init__(
        self,
        *,
        paths: IngestionPaths,
        repository: MapRepository,
        codex_backend: CodexBackend,
        ingestion_runner: IngestionRunner = run_official_ingestion,
        pipeline_status_provider: PipelineStatusProvider = current_pipeline_status,
        official_sources: Sequence[OfficialSource] = OFFICIAL_SOURCES,
    ) -> None:
        self.paths = paths
        self.repository = repository
        self.codex_backend = codex_backend
        self.ingestion_runner = ingestion_runner
        self.pipeline_status_provider = pipeline_status_provider
        self.official_sources = official_sources
        self._heatmap_cache: OrderedDict[HeatmapCacheKey, str] = OrderedDict()

    def settings_state(self) -> SettingsState:
        return SettingsState(
            app_backend_status=APP_BACKEND_STATUS,
            app_backend_detail=APP_BACKEND_DETAIL,
            codex_status=self.codex_backend.current_status(),
        )

    def map_data_state(self) -> MapDataState:
        return MapDataState(
            packets=self.repository.list_packets(),
            deletable_packet_ids=self.deletable_packet_ids(),
            sources=self.official_sources,
            pipeline=self.pipeline_status_provider(),
            report=self.latest_ingestion_report(),
        )

    def viewer_state(
        self,
        packet_id: str | None = None,
        *,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
    ) -> ViewerState:
        packet = self._selected_packet_by_selector(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
        )
        return ViewerState(
            packet=packet,
            packet_groups=self.packet_select_groups(),
            packet_selector=self.packet_selector_state(packet_id=packet.id),
            map_svg=render_map_svg(packet),
        )

    def heatmap_state(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
        zone_id: str = "attacker",
        source: str = "edge",
        offset_inches: int = 0,
    ) -> HeatmapState:
        packet = self._selected_packet_by_selector(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
        )
        heatmap_source = source if source in {"edge", "interior"} else "edge"
        clamped_offset = min(max(offset_inches, 0), 12)
        return HeatmapState(
            packet=packet,
            packet_groups=self.packet_select_groups(),
            packet_selector=self.packet_selector_state(packet_id=packet.id),
            selected_zone_id=zone_id,
            selected_source=heatmap_source,
            selected_offset_inches=clamped_offset,
            offset_options=list(range(0, 13)),
            map_svg=self._cached_heatmap_svg(
                packet.id,
                zone_id,
                heatmap_source,
                clamped_offset,
            ),
        )

    def los_checker_state(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
        x: float = 22.0,
        y: float = 10.0,
        base: float = 1.57,
    ) -> LosCheckerState:
        result = self.los_checker_toolkit_result(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
            x=x,
            y=y,
            base=base,
        )
        payload = result.payload
        return LosCheckerState(
            packet=payload.packet,
            packet_groups=self.packet_select_groups(),
            packet_selector=self.packet_selector_state(packet_id=payload.packet.id),
            x=payload.center[0],
            y=payload.center[1],
            base=payload.base_diameter,
            map_svg=render_map_svg(
                payload.packet,
                coverage_polygon=payload.coverage_polygon,
                rays=list(payload.rays),
                base_center=payload.center,
                base_diameter=payload.base_diameter,
            ),
        )

    def los_checker_toolkit_result(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
        x: float = 22.0,
        y: float = 10.0,
        base: float = 1.57,
    ) -> ToolkitResult[LosCheckerToolkitPayload]:
        packet = self._selected_packet_by_selector(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
        )
        center = clamp_base_center(packet, (x, y), base)
        return build_los_checker_toolkit_result(
            packet,
            center=center,
            base_diameter=base,
        )

    def movement_reach_state(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
        start_x: float = 16.0,
        start_y: float = 10.0,
        target_x: float = 22.0,
        target_y: float = 10.0,
        base: float = 1.57,
        move: float = 6.0,
        mode: str = "normal",
    ) -> MovementReachState:
        result = self.movement_reach_toolkit_result(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
            start_x=start_x,
            start_y=start_y,
            target_x=target_x,
            target_y=target_y,
            base=base,
            move=move,
            mode=mode,
        )
        payload = result.payload
        if result.is_blocked:
            map_svg = render_map_svg(payload.packet)
            endpoint_details = [reason.detail for reason in result.block_reasons]
        else:
            map_svg = render_map_svg(
                payload.packet,
                movement_envelope=payload.movement_envelope,
                movement_path=payload.swept_path,
                movement_start_center=payload.start_center,
                movement_target_center=payload.target_center,
                movement_base_diameter=payload.base_diameter,
            )
            endpoint_details = [reason.detail for reason in payload.endpoint.reasons]
        return MovementReachState(
            packet=payload.packet,
            packet_groups=self.packet_select_groups(),
            packet_selector=self.packet_selector_state(packet_id=payload.packet.id),
            start_x=payload.start_center[0],
            start_y=payload.start_center[1],
            target_x=payload.target_center[0],
            target_y=payload.target_center[1],
            base=payload.base_diameter,
            move=payload.move_distance,
            mode=payload.mode,
            movement_modes=list(MOVEMENT_MODES),
            endpoint_estimated_reachable=payload.endpoint.estimated_reachable,
            endpoint_reason_details=endpoint_details,
            map_svg=map_svg,
        )

    def movement_reach_toolkit_result(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
        start_x: float = 16.0,
        start_y: float = 10.0,
        target_x: float = 22.0,
        target_y: float = 10.0,
        base: float = 1.57,
        move: float = 6.0,
        mode: str = "normal",
    ) -> ToolkitResult[MovementReachPayload]:
        packet = self._selected_packet_by_selector(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
        )
        return build_movement_reach_toolkit_result(
            packet,
            start_center=(start_x, start_y),
            target_center=(target_x, target_y),
            base_diameter=base,
            move_distance=move,
            mode=mode,
        )

    def threat_range_state(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
        source_x: float = 16.0,
        source_y: float = 10.0,
        target_x: float = 24.0,
        target_y: float = 10.0,
        base: float = 1.57,
        move: float = 6.0,
        threat: float = 2.0,
        mode: str = "fixed-move-plus-range",
    ) -> ThreatRangeState:
        result = self.threat_range_toolkit_result(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
            source_x=source_x,
            source_y=source_y,
            target_x=target_x,
            target_y=target_y,
            base=base,
            move=move,
            threat=threat,
            mode=mode,
        )
        payload = result.payload
        map_svg = (
            render_map_svg(payload.packet)
            if result.is_blocked
            else render_map_svg(
                payload.packet,
                threat_regions=payload.threat_regions,
                threat_source_center=payload.source_center,
                threat_target_point=payload.target_point,
                threat_base_diameter=payload.base_diameter,
            )
        )
        return ThreatRangeState(
            packet=payload.packet,
            packet_groups=self.packet_select_groups(),
            packet_selector=self.packet_selector_state(packet_id=payload.packet.id),
            source_x=payload.source_center[0],
            source_y=payload.source_center[1],
            target_x=payload.target_point[0],
            target_y=payload.target_point[1],
            base=payload.base_diameter,
            move=payload.move_distance,
            threat=payload.threat_range,
            mode=payload.mode,
            threat_modes=list(THREAT_MODES),
            measurement_convention=payload.measurement_convention,
            target_probability=payload.target_probability,
            distribution=list(payload.distribution),
            warning_details=[warning.detail for warning in result.warnings],
            map_svg=map_svg,
        )

    def threat_range_toolkit_result(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
        source_x: float = 16.0,
        source_y: float = 10.0,
        target_x: float = 24.0,
        target_y: float = 10.0,
        base: float = 1.57,
        move: float = 6.0,
        threat: float = 2.0,
        mode: str = "fixed-move-plus-range",
    ) -> ToolkitResult[ThreatRangePayload]:
        packet = self._selected_packet_by_selector(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
        )
        return build_threat_range_toolkit_result(
            packet,
            source_center=(source_x, source_y),
            target_point=(target_x, target_y),
            base_diameter=base,
            move_distance=move,
            threat_range=threat,
            mode=mode,
        )

    def deployment_exposure_state(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
        deployment_zone_id: str = "attacker",
        friendly_x: float = 19.24,
        friendly_y: float = 51.48,
        friendly_base: float = 1.57,
        enemy_x: float = 24.77,
        enemy_y: float = 8.46,
        enemy_base: float = 1.57,
        enemy_move: float = 0.0,
        enemy_threat: float = 1.0,
        enemy_mode: str = "raw-range",
        exposure_mode: str = "threat-and-los",
    ) -> DeploymentExposureState:
        result = self.deployment_exposure_toolkit_result(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
            deployment_zone_id=deployment_zone_id,
            friendly_x=friendly_x,
            friendly_y=friendly_y,
            friendly_base=friendly_base,
            enemy_x=enemy_x,
            enemy_y=enemy_y,
            enemy_base=enemy_base,
            enemy_move=enemy_move,
            enemy_threat=enemy_threat,
            enemy_mode=enemy_mode,
            exposure_mode=exposure_mode,
        )
        payload = result.payload
        if result.is_blocked:
            map_svg = render_map_svg(payload.packet)
            placement_details = [reason.detail for reason in result.block_reasons]
        else:
            map_svg = render_map_svg(
                payload.packet,
                coverage_polygon=payload.enemy_los_region
                if exposure_mode_includes_los(payload.exposure_mode)
                else None,
                safe_regions=payload.candidate_center_region,
                base_center=payload.friendly_center,
                base_diameter=payload.friendly_base_diameter,
                threat_regions=payload.enemy_threat_regions
                if exposure_mode_includes_threat(payload.exposure_mode)
                else None,
                threat_source_center=payload.enemy_source_center,
                threat_base_diameter=payload.enemy_base_diameter,
            )
            placement_details = [reason.detail for reason in payload.placement.reasons]
        return DeploymentExposureState(
            packet=payload.packet,
            packet_groups=self.packet_select_groups(),
            packet_selector=self.packet_selector_state(packet_id=payload.packet.id),
            deployment_zone_options=[
                DeploymentZoneSelectOption(id=zone.id, label=zone.label)
                for zone in payload.packet.deployment_zones
            ],
            deployment_zone_id=payload.deployment_zone_id,
            friendly_x=payload.friendly_center[0],
            friendly_y=payload.friendly_center[1],
            friendly_base=payload.friendly_base_diameter,
            enemy_x=payload.enemy_source_center[0],
            enemy_y=payload.enemy_source_center[1],
            enemy_base=payload.enemy_base_diameter,
            enemy_move=payload.enemy_move_distance,
            enemy_threat=payload.enemy_threat_range,
            enemy_mode=payload.enemy_threat_mode,
            exposure_mode=payload.exposure_mode,
            enemy_threat_modes=list(THREAT_MODES),
            exposure_modes=list(EXPOSURE_MODES),
            not_exposed_under_assumptions=payload.placement.not_exposed_under_assumptions,
            threat_probability_at_center=payload.threat_probability_at_center,
            placement_reason_details=placement_details,
            warning_details=[warning.detail for warning in result.warnings],
            map_svg=map_svg,
        )

    def deployment_exposure_toolkit_result(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
        deployment_zone_id: str = "attacker",
        friendly_x: float = 19.24,
        friendly_y: float = 51.48,
        friendly_base: float = 1.57,
        enemy_x: float = 24.77,
        enemy_y: float = 8.46,
        enemy_base: float = 1.57,
        enemy_move: float = 0.0,
        enemy_threat: float = 1.0,
        enemy_mode: str = "raw-range",
        exposure_mode: str = "threat-and-los",
    ) -> ToolkitResult[DeploymentExposurePayload]:
        packet = self._selected_packet_by_selector(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
        )
        return build_deployment_exposure_toolkit_result(
            packet,
            deployment_zone_id=deployment_zone_id,
            friendly_center=(friendly_x, friendly_y),
            friendly_base_diameter=friendly_base,
            enemy_source_center=(enemy_x, enemy_y),
            enemy_base_diameter=enemy_base,
            enemy_move_distance=enemy_move,
            enemy_threat_range=enemy_threat,
            enemy_threat_mode=enemy_mode,
            exposure_mode=exposure_mode,
        )

    def damage_profile_state(
        self,
        *,
        attacks: float = DEFAULT_DAMAGE_PROFILE_INPUT.attacks,
        hit: int = DEFAULT_DAMAGE_PROFILE_INPUT.hit_target,
        wound: int = DEFAULT_DAMAGE_PROFILE_INPUT.wound_target,
        save: int = DEFAULT_DAMAGE_PROFILE_INPUT.save_target,
        damage: float = DEFAULT_DAMAGE_PROFILE_INPUT.damage_per_unsaved_wound,
        wounds: float = DEFAULT_TARGET_PROFILE_INPUT.wounds_per_model,
        models: float = DEFAULT_TARGET_PROFILE_INPUT.model_count,
    ) -> DamageProfileState:
        result = self.damage_profile_toolkit_result(
            attacks=attacks,
            hit=hit,
            wound=wound,
            save=save,
            damage=damage,
            wounds=wounds,
            models=models,
        )
        payload = result.payload
        summary = payload.summary
        return DamageProfileState(
            attacks=payload.profile.attacks,
            hit_target=payload.profile.hit_target,
            wound_target=payload.profile.wound_target,
            save_target=payload.profile.save_target,
            damage_per_unsaved_wound=payload.profile.damage_per_unsaved_wound,
            target_wounds_per_model=payload.target.wounds_per_model,
            target_model_count=payload.target.model_count,
            is_blocked=result.is_blocked,
            expected_hits=summary.expected_hits,
            expected_wounds=summary.expected_wounds,
            expected_unsaved_wounds=summary.expected_unsaved_wounds,
            expected_damage=summary.expected_damage,
            expected_models_destroyed=summary.expected_models_destroyed,
            probability_destroying_at_least_one_model=(
                summary.probability_destroying_at_least_one_model
            ),
            unsaved_wound_distribution=list(payload.unsaved_wound_distribution),
            models_destroyed_distribution=list(payload.models_destroyed_distribution),
            warning_details=[warning.detail for warning in result.warnings],
            block_reason_details=[reason.detail for reason in result.block_reasons],
        )

    def damage_profile_toolkit_result(
        self,
        *,
        attacks: float = DEFAULT_DAMAGE_PROFILE_INPUT.attacks,
        hit: int = DEFAULT_DAMAGE_PROFILE_INPUT.hit_target,
        wound: int = DEFAULT_DAMAGE_PROFILE_INPUT.wound_target,
        save: int = DEFAULT_DAMAGE_PROFILE_INPUT.save_target,
        damage: float = DEFAULT_DAMAGE_PROFILE_INPUT.damage_per_unsaved_wound,
        wounds: float = DEFAULT_TARGET_PROFILE_INPUT.wounds_per_model,
        models: float = DEFAULT_TARGET_PROFILE_INPUT.model_count,
    ) -> ToolkitResult[DamageEstimatePayload]:
        return build_damage_profile_toolkit_result(
            attacks=attacks,
            hit_target=hit,
            wound_target=wound,
            save_target=save,
            damage_per_unsaved_wound=damage,
            target_wounds_per_model=wounds,
            target_model_count=models,
        )

    def hidden_coverage_state(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
        terrain_area_id: str | None = None,
        detection_range: int = 15,
    ) -> HiddenCoverageState:
        packet = self._selected_packet_by_selector(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
        )
        terrain_options = [
            TerrainSelectOption(id=area.id, label=area.label) for area in packet.terrain_areas
        ]
        if not terrain_options:
            return HiddenCoverageState(
                packet=packet,
                packet_groups=self.packet_select_groups(),
                packet_selector=self.packet_selector_state(packet_id=packet.id),
                terrain_options=[],
                selected_terrain_area_id="",
                selected_detection_range=_closest_option(
                    detection_range,
                    HIDDEN_DETECTION_RANGE_OPTIONS,
                ),
                detection_range_options=list(HIDDEN_DETECTION_RANGE_OPTIONS),
                map_svg=render_map_svg(packet),
            )
        terrain_ids = {option.id for option in terrain_options}
        selected_terrain_area_id = (
            terrain_area_id
            if terrain_area_id is not None and terrain_area_id in terrain_ids
            else terrain_options[0].id
        )
        selected_detection_range = _closest_option(
            detection_range,
            HIDDEN_DETECTION_RANGE_OPTIONS,
        )
        hidden_coverage = hidden_coverage_from_terrain_area(
            packet,
            selected_terrain_area_id,
            detection_range=float(selected_detection_range),
            observer_grid_step=HIDDEN_COVERAGE_OBSERVER_GRID_STEP,
            hidden_sample_step=HIDDEN_COVERAGE_SAMPLE_STEP,
        )
        return HiddenCoverageState(
            packet=packet,
            packet_groups=self.packet_select_groups(),
            packet_selector=self.packet_selector_state(packet_id=packet.id),
            terrain_options=terrain_options,
            selected_terrain_area_id=selected_terrain_area_id,
            selected_detection_range=selected_detection_range,
            detection_range_options=list(HIDDEN_DETECTION_RANGE_OPTIONS),
            map_svg=render_map_svg(packet, hidden_coverage=hidden_coverage),
        )

    def packet_select_groups(self) -> list[PacketSelectGroup]:
        grouped: dict[str, list[PacketSelectOption]] = {}
        for packet in sorted(self.repository.list_packets(), key=_packet_sort_key):
            grouped.setdefault(_packet_group_label(packet), []).append(
                PacketSelectOption(id=packet.id, label=_packet_option_label(packet))
            )
        return [
            PacketSelectGroup(label=label, options=options) for label, options in grouped.items()
        ]

    def packet_selector_state(
        self,
        packet_id: str | None = None,
        *,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
    ) -> PacketSelectorState:
        packets = sorted(self.repository.list_packets(), key=_packet_sort_key)
        official_packets = [packet for packet in packets if packet.layout_metadata is not None]
        if not official_packets:
            return self._fixture_packet_selector_state(packet_id)

        fallback_packet = self._selected_packet(packet_id)
        fallback_metadata = fallback_packet.layout_metadata
        selected_player_a = _clean_selector_value(player_a)
        selected_player_b = _clean_selector_value(player_b)
        selected_layout = _clean_selector_value(layout_variant)
        if fallback_metadata is not None:
            selected_player_a = (
                selected_player_a or fallback_metadata.first_player.force_disposition
            )
            selected_player_b = (
                selected_player_b or fallback_metadata.second_player.force_disposition
            )
            selected_layout = selected_layout or fallback_metadata.layout_variant

        player_a_options = _unique(
            packet.layout_metadata.first_player.force_disposition
            for packet in official_packets
            if packet.layout_metadata is not None
        )
        if selected_player_a not in player_a_options:
            selected_player_a = player_a_options[0]

        player_b_options = _unique(
            packet.layout_metadata.second_player.force_disposition
            for packet in official_packets
            if packet.layout_metadata is not None
            and packet.layout_metadata.first_player.force_disposition == selected_player_a
        )
        if selected_player_b not in player_b_options:
            selected_player_b = player_b_options[0]

        layout_packets = [
            packet
            for packet in official_packets
            if packet.layout_metadata is not None
            and packet.layout_metadata.first_player.force_disposition == selected_player_a
            and packet.layout_metadata.second_player.force_disposition == selected_player_b
        ]
        layout_options = [_packet_layout_option(packet) for packet in layout_packets]
        layout_variants = [option.variant for option in layout_options]
        if selected_layout not in layout_variants:
            selected_layout = layout_variants[0]
        selected_packet_id = next(
            option.packet_id for option in layout_options if option.variant == selected_layout
        )
        return PacketSelectorState(
            player_a_options=player_a_options,
            player_b_options=player_b_options,
            layout_options=layout_options,
            selected_player_a=selected_player_a,
            selected_player_b=selected_player_b,
            selected_layout_variant=selected_layout,
            selected_packet_id=selected_packet_id,
        )

    def resolve_packet_id(
        self,
        *,
        packet_id: str | None = None,
        player_a: str | None = None,
        player_b: str | None = None,
        layout_variant: str | None = None,
    ) -> str:
        return self.packet_selector_state(
            packet_id=packet_id,
            player_a=player_a,
            player_b=player_b,
            layout_variant=layout_variant,
        ).selected_packet_id

    def latest_ingestion_report(self) -> IngestionReport | None:
        path = self.paths.ingestion_report_path
        if not path.exists():
            return None
        try:
            return IngestionReport.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError:
            return None

    def run_ingestion(self) -> IngestionReport:
        report = self.ingestion_runner(paths=self.paths, classify_features=True)
        self.reload_packets()
        return report

    def delete_packet(self, packet_id: str) -> bool:
        deleted = False
        try:
            packet_path = self.packet_path(packet_id)
        except ValueError:
            packet_path = None
        if packet_path is not None and packet_path.exists():
            packet_path.unlink()
            deleted = True
        self.reload_packets()
        return deleted

    def deletable_packet_ids(self) -> set[str]:
        directory = self.paths.map_packets_dir
        if not directory.exists() or not directory.is_dir():
            return set()
        return {path.stem for path in directory.glob("*.json") if path.is_file()}

    def packet_path(self, packet_id: str) -> Path:
        candidate = self.paths.map_packets_dir / f"{packet_id}.json"
        if not packet_id or candidate.name != f"{packet_id}.json":
            raise ValueError(f"Invalid packet id: {packet_id}")
        return candidate

    def reload_packets(self) -> None:
        reload = getattr(self.repository, "reload", None)
        if callable(reload):
            reload()
        self.clear_caches()

    def clear_caches(self) -> None:
        self._heatmap_cache.clear()

    def codex_status(self) -> CodexBackendStatus:
        return self.codex_backend.current_status()

    def start_codex_login(self) -> CodexLoginStart:
        return self.codex_backend.start_chatgpt_login()

    def start_codex_device_code_login(self) -> CodexLoginStart:
        return self.codex_backend.start_chatgpt_device_code_login()

    def logout_codex(self) -> None:
        self.codex_backend.logout()

    def _selected_packet(self, packet_id: str | None) -> MapPacket:
        if packet_id:
            return self.repository.get_packet(packet_id)
        return self.repository.default_packet()

    def _selected_packet_by_selector(
        self,
        *,
        packet_id: str | None,
        player_a: str | None,
        player_b: str | None,
        layout_variant: str | None,
    ) -> MapPacket:
        if any(_clean_selector_value(value) for value in (player_a, player_b, layout_variant)):
            return self.repository.get_packet(
                self.resolve_packet_id(
                    packet_id=packet_id,
                    player_a=player_a,
                    player_b=player_b,
                    layout_variant=layout_variant,
                )
            )
        return self._selected_packet(packet_id)

    def _fixture_packet_selector_state(self, packet_id: str | None) -> PacketSelectorState:
        packets = sorted(self.repository.list_packets(), key=_packet_sort_key)
        selected_packet = self._selected_packet(packet_id)
        options = [
            PacketLayoutOption(
                packet_id=packet.id,
                variant=packet.id,
                label=packet.name,
                detail="Development fixture",
            )
            for packet in packets
        ]
        return PacketSelectorState(
            player_a_options=["Development fixture"],
            player_b_options=["Development fixture"],
            layout_options=options,
            selected_player_a="Development fixture",
            selected_player_b="Development fixture",
            selected_layout_variant=selected_packet.id,
            selected_packet_id=selected_packet.id,
        )

    def _cached_heatmap_svg(
        self,
        packet_id: str,
        zone_id: str,
        source: str,
        offset_inches: int,
    ) -> str:
        key = (packet_id, zone_id, source, offset_inches)
        cached_svg = self._heatmap_cache.get(key)
        if cached_svg is not None:
            self._heatmap_cache.move_to_end(key)
            return cached_svg
        rendered_svg = self._render_heatmap_svg(packet_id, zone_id, source, offset_inches)
        self._heatmap_cache[key] = rendered_svg
        if len(self._heatmap_cache) > 32:
            self._heatmap_cache.popitem(last=False)
        return rendered_svg

    def _render_heatmap_svg(
        self,
        packet_id: str,
        zone_id: str,
        source: str,
        offset_inches: int,
    ) -> str:
        packet = self.repository.get_packet(packet_id)
        if source == "interior":
            polygons = heatmap_visibility_polygons_from_deployment_zone(packet, zone_id)
        else:
            polygons = heatmap_visibility_polygons_from_deployment_edge(
                packet,
                zone_id,
                offset_inches=offset_inches,
            )
        exclusion = heatmap_exclusion_zone(
            packet,
            zone_id,
            source=source,
            offset_inches=offset_inches,
        )
        safe_regions = safe_heatmap_regions(packet, polygons, excluded_area=exclusion)
        return render_map_svg(
            packet,
            heatmap_polygons=polygons,
            heatmap_exclusion=exclusion,
            safe_regions=safe_regions,
        )


def _packet_sort_key(packet: MapPacket) -> tuple[int, int, str]:
    metadata = packet.layout_metadata
    if metadata is None:
        return (1, 0, packet.name)
    return (0, metadata.source_page, metadata.layout_variant)


def _packet_group_label(packet: MapPacket) -> str:
    metadata = packet.layout_metadata
    if metadata is None:
        return "Development fixtures"
    return (
        f"{metadata.first_player.force_disposition} vs {metadata.second_player.force_disposition}"
    )


def _packet_option_label(packet: MapPacket) -> str:
    metadata = packet.layout_metadata
    if metadata is None:
        return packet.name
    dispositions = (
        f"{metadata.first_player.force_disposition} vs {metadata.second_player.force_disposition}"
    )
    primary_missions = (
        f"{metadata.first_player.primary_mission} vs {metadata.second_player.primary_mission}"
    )
    return f"Layout {metadata.layout_variant} - {dispositions} ({primary_missions})"


def _packet_layout_option(packet: MapPacket) -> PacketLayoutOption:
    metadata = packet.layout_metadata
    if metadata is None:
        return PacketLayoutOption(
            packet_id=packet.id,
            variant=packet.id,
            label=packet.name,
            detail="Development fixture",
        )
    primary_missions = (
        f"{metadata.first_player.primary_mission} vs {metadata.second_player.primary_mission}"
    )
    return PacketLayoutOption(
        packet_id=packet.id,
        variant=metadata.layout_variant,
        label=f"Layout {metadata.layout_variant}",
        detail=f"{primary_missions} - Event Companion page {metadata.source_page}",
    )


def _clean_selector_value(value: str | None) -> str:
    return value.strip() if value else ""


def _unique(values: Iterable[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return unique_values


def _closest_option(value: int, options: Sequence[int]) -> int:
    return min(options, key=lambda option: (abs(option - value), option))
