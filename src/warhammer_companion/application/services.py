from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from warhammer_companion.application.view_models import (
    HeatmapState,
    LosCheckerState,
    MapDataState,
    PacketSelectGroup,
    PacketSelectOption,
    SettingsState,
    ViewerState,
)
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.repository import MapRepository
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
    safe_heatmap_regions,
    visibility_polygon_from_base,
    visibility_rays_from_base,
)
from warhammer_companion.rendering.svg import render_map_svg


class ReloadableMapRepository(MapRepository, Protocol):
    def reload(self) -> None: ...


IngestionRunner = Callable[..., IngestionReport]
PipelineStatusProvider = Callable[[], list[PipelineStage]]
HeatmapCacheKey = tuple[str, str, str, int]

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

    def viewer_state(self, packet_id: str | None = None) -> ViewerState:
        packet = self._selected_packet(packet_id)
        return ViewerState(
            packet=packet,
            packet_groups=self.packet_select_groups(),
            map_svg=render_map_svg(packet),
        )

    def heatmap_state(
        self,
        *,
        packet_id: str | None = None,
        zone_id: str = "attacker",
        source: str = "edge",
        offset_inches: int = 0,
    ) -> HeatmapState:
        packet = self._selected_packet(packet_id)
        heatmap_source = source if source in {"edge", "interior"} else "edge"
        clamped_offset = min(max(offset_inches, 0), 12)
        return HeatmapState(
            packet=packet,
            packet_groups=self.packet_select_groups(),
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
        x: float = 22.0,
        y: float = 10.0,
        base: float = 1.57,
    ) -> LosCheckerState:
        packet = self._selected_packet(packet_id)
        center = clamp_base_center(packet, (x, y), base)
        coverage_polygon = visibility_polygon_from_base(
            packet,
            center=center,
            base_diameter=base,
        )
        rays = visibility_rays_from_base(packet, center=center, base_diameter=base)
        return LosCheckerState(
            packet=packet,
            packet_groups=self.packet_select_groups(),
            x=center[0],
            y=center[1],
            base=base,
            map_svg=render_map_svg(
                packet,
                coverage_polygon=coverage_polygon,
                rays=rays,
                base_center=center,
                base_diameter=base,
            ),
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
