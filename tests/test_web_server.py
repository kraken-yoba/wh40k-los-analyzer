from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from warhammer_companion.application.mission_pack import (
    PUBLIC_MISSION_SHEET_GID,
    PUBLIC_MISSION_SHEET_ID,
)
from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.application.view_models import (
    DamageProfileState,
    DeploymentExposureState,
    DeploymentScorecardState,
    DeploymentZoneSelectOption,
    HeatmapState,
    HiddenCoverageState,
    MissionPackState,
    MovementReachState,
    TerrainSelectOption,
    ThreatRangeState,
)
from warhammer_companion.domain.damage import DamageProbabilityRow
from warhammer_companion.domain.deployment_scorecard import DeploymentScorecardComponent
from warhammer_companion.domain.missions import (
    MissionPack,
    MissionRecord,
    MissionSourceAnchor,
    MissionSourceRef,
)
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.packet_io import write_packet
from warhammer_companion.domain.repository import FileBackedMapRepository, StaticMapRepository
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.official_layout_metadata import official_layout_metadata_for_page
from warhammer_companion.ingestion.packet_builder import IngestionReport, PacketValidationResult
from warhammer_companion.sample_data import SAMPLE_PACKETS
from warhammer_companion.web import server


def test_map_data_ingestion_runs_and_reloads_repository(
    tmp_path: Path,
    monkeypatch,
) -> None:
    paths = IngestionPaths(tmp_path / "data")
    repository = FileBackedMapRepository(paths.map_packets_dir, fallback=SAMPLE_PACKETS)
    official_packet = _official_packet()

    def fake_ingestion(
        *,
        paths: IngestionPaths,
        layout_pages=None,
        classify_features: bool = False,
    ) -> IngestionReport:
        assert classify_features
        write_packet(official_packet, paths.map_packets_dir / f"{official_packet.id}.json")
        return IngestionReport(
            started_at_epoch=1.0,
            duration_seconds=0.25,
            source_footprint_pdf=str(paths.raw_dir / "terrain-area-footprints.pdf"),
            source_layout_pdf=str(paths.raw_dir / "event-companion.pdf"),
            footprint_library_path=str(paths.footprint_library_path),
            layout_library_path=str(paths.layout_library_path),
            map_packets_dir=str(paths.map_packets_dir),
            packet_count=1,
            layout_count=1,
            validation=[PacketValidationResult(packet_id=official_packet.id, valid=True)],
        )

    monkeypatch.setattr(
        server,
        "service",
        WarhammerCompanionService(
            paths=paths,
            repository=repository,
            codex_backend=server.codex_backend,
            ingestion_runner=fake_ingestion,
        ),
    )
    client = TestClient(server.app)

    response = client.post("/map-data/ingest", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/map-data?ingestion=complete"
    assert repository.list_packets() == [official_packet]


def test_map_data_delete_removes_generated_packet_and_reloads(
    tmp_path: Path,
    monkeypatch,
) -> None:
    paths = IngestionPaths(tmp_path / "data")
    official_packet = _official_packet()
    write_packet(official_packet, paths.map_packets_dir / f"{official_packet.id}.json")
    repository = FileBackedMapRepository(paths.map_packets_dir, fallback=SAMPLE_PACKETS)
    monkeypatch.setattr(
        server,
        "service",
        WarhammerCompanionService(
            paths=paths,
            repository=repository,
            codex_backend=server.codex_backend,
        ),
    )
    client = TestClient(server.app)

    response = client.post(
        "/map-data/delete",
        data={"packet_id": official_packet.id},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/map-data?deleted=1"
    assert not (paths.map_packets_dir / f"{official_packet.id}.json").exists()
    assert repository.list_packets() == SAMPLE_PACKETS


def test_heatmap_route_uses_edge_offset_controls(monkeypatch) -> None:
    calls: list[tuple[str, str, str, int]] = []
    packet = server.repository.default_packet()
    packet_selector = WarhammerCompanionService(
        paths=server.ingestion_paths,
        repository=StaticMapRepository([packet]),
        codex_backend=server.codex_backend,
    ).packet_selector_state(packet_id=packet.id)

    class FakeService:
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
            resolved_packet_id = packet_id or packet.id
            calls.append((resolved_packet_id, zone_id, source, offset_inches))
            return HeatmapState(
                packet=packet,
                packet_groups=[],
                packet_selector=packet_selector,
                selected_zone_id=zone_id,
                selected_source=source,
                selected_offset_inches=offset_inches,
                offset_options=list(range(0, 13)),
                map_svg='<svg class="map-svg" role="img" aria-label="fake map"></svg>',
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        f"/heatmap?packet_id={packet.id}&zone_id=attacker&source=edge&offset_inches=6"
    )

    assert response.status_code == 200
    assert calls == [(packet.id, "attacker", "edge", 6)]
    assert 'name="source"' in response.text
    assert 'name="offset_inches"' in response.text
    assert 'value="6"' in response.text


def test_hidden_coverage_route_uses_terrain_and_range_controls(monkeypatch) -> None:
    calls: list[tuple[str, str, int]] = []
    packet = server.repository.default_packet()
    terrain_area = packet.terrain_areas[0]
    packet_selector = WarhammerCompanionService(
        paths=server.ingestion_paths,
        repository=StaticMapRepository([packet]),
        codex_backend=server.codex_backend,
    ).packet_selector_state(packet_id=packet.id)

    class FakeService:
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
            resolved_packet_id = packet_id or packet.id
            resolved_terrain_id = terrain_area_id or terrain_area.id
            calls.append((resolved_packet_id, resolved_terrain_id, detection_range))
            return HiddenCoverageState(
                packet=packet,
                packet_groups=[],
                packet_selector=packet_selector,
                terrain_options=[
                    TerrainSelectOption(id=area.id, label=area.label)
                    for area in packet.terrain_areas
                ],
                selected_terrain_area_id=resolved_terrain_id,
                selected_detection_range=detection_range,
                detection_range_options=[12, 15, 18],
                map_svg=(
                    '<svg class="map-svg" role="img" aria-label="fake hidden map">'
                    '<image class="hidden-coverage-image"/></svg>'
                ),
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        f"/hidden-coverage?packet_id={packet.id}"
        f"&terrain_area_id={terrain_area.id}&detection_range=18"
    )

    assert response.status_code == 200
    assert calls == [(packet.id, terrain_area.id, 18)]
    assert 'name="terrain_area_id"' in response.text
    assert 'name="detection_range"' in response.text
    assert 'value="18"' in response.text
    assert "Hidden Coverage" in response.text
    assert "hidden-coverage-image" in response.text


def test_movement_reach_route_uses_manual_geometry_controls_and_cautious_language(
    monkeypatch,
) -> None:
    calls: list[tuple[str, float, float, float, float, float, float, str, str]] = []
    packet = server.repository.default_packet()
    packet_selector = WarhammerCompanionService(
        paths=server.ingestion_paths,
        repository=StaticMapRepository([packet]),
        codex_backend=server.codex_backend,
    ).packet_selector_state(packet_id=packet.id)

    class FakeService:
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
            movement_profile: str = "ground-non-mobile",
        ) -> MovementReachState:
            resolved_packet_id = packet_id or packet.id
            calls.append(
                (
                    resolved_packet_id,
                    start_x,
                    start_y,
                    target_x,
                    target_y,
                    base,
                    move,
                    mode,
                    movement_profile,
                )
            )
            return MovementReachState(
                packet=packet,
                packet_groups=[],
                packet_selector=packet_selector,
                start_x=start_x,
                start_y=start_y,
                target_x=target_x,
                target_y=target_y,
                base=base,
                move=move,
                mode=mode,
                movement_modes=["normal", "advance", "charge"],
                endpoint_estimated_reachable=True,
                endpoint_reason_details=[],
                map_svg=(
                    '<svg class="map-svg" role="img" aria-label="fake movement map">'
                    '<image class="movement-envelope-image"/></svg>'
                ),
                movement_profile=movement_profile,
                movement_profile_label="Ground mobile / infantry",
                effective_move=6.0,
                input_hash="sha256:test-movement",
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        f"/movement-reach?packet_id={packet.id}&start_x=16&start_y=10"
        "&target_x=22&target_y=10&base=1.57&move=6&mode=advance"
        "&movement_profile=ground-mobile"
    )
    normalized = " ".join(response.text.split()).lower()

    assert response.status_code == 200
    assert calls == [(packet.id, 16.0, 10.0, 22.0, 10.0, 1.57, 6.0, "advance", "ground-mobile")]
    assert "Movement Reach" in response.text
    assert 'name="start_x"' in response.text
    assert 'name="target_x"' in response.text
    assert 'name="move"' in response.text
    assert 'name="mode"' in response.text
    assert 'name="movement_profile"' in response.text
    assert 'value="advance" selected' in response.text
    assert 'value="ground-mobile" selected' in response.text
    assert "Ground mobile / infantry" in response.text
    assert "Effective movement" in response.text
    assert "estimated 2d geometry" in normalized
    assert "route-connected under selected assumptions" in normalized
    assert "movement-envelope-image" in response.text
    assert "<script" not in response.text
    for forbidden in ("legal", " safe", "recommended", "optimal", "likely"):
        assert forbidden not in normalized


def test_threat_range_route_uses_manual_probability_controls_and_cautious_language(
    monkeypatch,
) -> None:
    calls: list[tuple[str, float, float, float, float, float, float, float, str, str]] = []
    packet = server.repository.default_packet()
    packet_selector = WarhammerCompanionService(
        paths=server.ingestion_paths,
        repository=StaticMapRepository([packet]),
        codex_backend=server.codex_backend,
    ).packet_selector_state(packet_id=packet.id)

    class FakeService:
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
            movement_profile: str = "ground-non-mobile",
        ) -> ThreatRangeState:
            resolved_packet_id = packet_id or packet.id
            calls.append(
                (
                    resolved_packet_id,
                    source_x,
                    source_y,
                    target_x,
                    target_y,
                    base,
                    move,
                    threat,
                    mode,
                    movement_profile,
                )
            )
            from warhammer_companion.domain.threat import ThreatDiceOutcome

            return ThreatRangeState(
                packet=packet,
                packet_groups=[],
                packet_selector=packet_selector,
                source_x=source_x,
                source_y=source_y,
                target_x=target_x,
                target_y=target_y,
                base=base,
                move=move,
                threat=threat,
                mode=mode,
                threat_modes=["raw-range", "fixed-move-plus-range", "2d6-move-plus-range"],
                measurement_convention="source-base-edge-to-target-point",
                target_probability=0.75,
                distribution=[
                    ThreatDiceOutcome(
                        dice_label="2D6",
                        variable_inches=7,
                        numerator=6,
                        denominator=36,
                        probability=6 / 36,
                        total_reach=16.0,
                        effective_move_distance=13.0,
                    )
                ],
                warning_details=[
                    "Source-backed rules pending; this result remains estimated.",
                    "No recommendations are generated from estimated threat projections.",
                ],
                map_svg=(
                    '<svg class="map-svg" role="img" aria-label="fake threat map">'
                    '<image class="threat-projection-image"/></svg>'
                ),
                movement_profile=movement_profile,
                movement_profile_label="Fly: Take to the Skies",
                effective_move=4.0,
                input_hash="sha256:test-threat",
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        f"/threat-range?packet_id={packet.id}&source_x=16&source_y=10"
        "&target_x=24&target_y=10&base=1.57&move=6&threat=2&mode=2d6-move-plus-range"
        "&movement_profile=fly-take-to-skies"
    )
    normalized = " ".join(response.text.split()).lower()

    assert response.status_code == 200
    assert calls == [
        (
            packet.id,
            16.0,
            10.0,
            24.0,
            10.0,
            1.57,
            6.0,
            2.0,
            "2d6-move-plus-range",
            "fly-take-to-skies",
        )
    ]
    assert "Threat Range" in response.text
    assert 'name="source_x"' in response.text
    assert 'name="target_x"' in response.text
    assert 'name="threat"' in response.text
    assert 'name="mode"' in response.text
    assert 'name="movement_profile"' in response.text
    assert 'value="2d6-move-plus-range" selected' in response.text
    assert 'value="fly-take-to-skies" selected' in response.text
    assert "Fly: Take to the Skies" in response.text
    assert "Effective movement" in response.text
    assert "estimated 2d threat projection" in normalized
    assert "source base edge to target point" in normalized
    assert "source-backed rules pending" in normalized
    assert "no recommendations" in normalized
    assert "75.0%" in response.text
    assert "threat-projection-image" in response.text
    assert "<script" not in response.text
    for forbidden in ("legal", " safe", "recommended", "optimal", "likely", "guaranteed"):
        assert forbidden not in normalized


def test_threat_range_post_redirect_preserves_manual_values(monkeypatch) -> None:
    packet = server.repository.default_packet()
    resolved_calls: list[tuple[str | None, str | None, str | None, str | None]] = []

    class FakeService:
        def resolve_packet_id(
            self,
            *,
            packet_id: str | None = None,
            player_a: str | None = None,
            player_b: str | None = None,
            layout_variant: str | None = None,
        ) -> str:
            resolved_calls.append((packet_id, player_a, player_b, layout_variant))
            return packet.id

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.post(
        "/threat-range",
        data={
            "packet_id": packet.id,
            "player_a": "Take and Hold",
            "player_b": "Reconnaissance",
            "layout_variant": "B",
            "source_x": "16",
            "source_y": "10",
            "target_x": "24",
            "target_y": "10",
            "base": "1.57",
            "move": "6",
            "threat": "2",
            "mode": "2d6-move-plus-range",
            "movement_profile": "fly-hover-take-to-skies",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert resolved_calls == [(packet.id, "Take and Hold", "Reconnaissance", "B")]
    assert response.headers["location"] == (
        f"/threat-range?packet_id={packet.id}&source_x=16.0&source_y=10.0"
        "&target_x=24.0&target_y=10.0&base=1.57&move=6.0&threat=2.0"
        "&mode=2d6-move-plus-range&movement_profile=fly-hover-take-to-skies"
    )


def test_deployment_exposure_route_uses_manual_controls_and_cautious_language(
    monkeypatch,
) -> None:
    packet = server.repository.default_packet()
    real_service = server.service
    calls: list[tuple[str | None, str, float, float, str, str]] = []

    class FakeService:
        def deployment_exposure_state(
            self,
            *,
            packet_id: str | None = None,
            player_a: str | None = None,
            player_b: str | None = None,
            layout_variant: str | None = None,
            deployment_zone_id: str = "attacker",
            friendly_x: float = 10.0,
            friendly_y: float = 5.0,
            friendly_base: float = 1.57,
            enemy_x: float = 38.0,
            enemy_y: float = 52.0,
            enemy_base: float = 1.57,
            enemy_move: float = 0.0,
            enemy_threat: float = 1.0,
            enemy_mode: str = "raw-range",
            enemy_movement_profile: str = "ground-non-mobile",
            exposure_mode: str = "threat-and-los",
        ) -> DeploymentExposureState:
            calls.append(
                (
                    packet_id,
                    deployment_zone_id,
                    friendly_x,
                    enemy_x,
                    enemy_movement_profile,
                    exposure_mode,
                )
            )
            return DeploymentExposureState(
                packet=packet,
                packet_groups=real_service.packet_select_groups(),
                packet_selector=real_service.packet_selector_state(packet_id=packet.id),
                deployment_zone_options=[
                    DeploymentZoneSelectOption(id=zone.id, label=zone.label)
                    for zone in packet.deployment_zones
                ],
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
                enemy_threat_modes=["raw-range", "fixed-move-plus-range"],
                exposure_modes=["threat-only", "los-only", "threat-or-los", "threat-and-los"],
                not_exposed_under_assumptions=True,
                threat_probability_at_center=0.0,
                placement_reason_details=[],
                warning_details=[
                    "Estimated deployment exposure diagnostic uses manual 2D geometry.",
                    "This is not a placement planner; mission constraints are not modeled.",
                ],
                map_svg=(
                    '<svg class="map-svg" role="img" aria-label="fake deployment exposure">'
                    '<image class="coverage-image"/>'
                    '<image class="threat-projection-image"/>'
                    '<polyline class="safe-zone-outline"/>'
                    '<circle class="model-base"/>'
                    '<circle class="threat-source-base"/>'
                    "</svg>"
                ),
                enemy_movement_profile=enemy_movement_profile,
                enemy_movement_profile_label="Ground mobile / infantry",
                enemy_effective_move=6.0,
                input_hash="sha256:test-exposure",
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        f"/deployment-exposure?packet_id={packet.id}&deployment_zone_id=attacker"
        "&friendly_x=10&friendly_y=5&friendly_base=1.57"
        "&enemy_x=38&enemy_y=52&enemy_base=1.57&enemy_move=0&enemy_threat=1"
        "&enemy_mode=raw-range&enemy_movement_profile=ground-mobile"
        "&exposure_mode=threat-and-los"
    )
    normalized = " ".join(response.text.split()).lower()
    normalized_without_classes = normalized.replace("safe-zone-outline", "")

    assert response.status_code == 200
    assert calls == [(packet.id, "attacker", 10.0, 38.0, "ground-mobile", "threat-and-los")]
    assert "Deployment Exposure" in response.text
    assert 'name="deployment_zone_id"' in response.text
    assert 'name="friendly_x"' in response.text
    assert 'name="enemy_x"' in response.text
    assert 'name="enemy_mode"' in response.text
    assert 'name="enemy_movement_profile"' in response.text
    assert 'name="exposure_mode"' in response.text
    assert 'value="ground-mobile" selected' in response.text
    assert 'value="threat-and-los" selected' in response.text
    assert "Ground mobile / infantry" in response.text
    assert "not exposed under selected assumptions" in normalized
    assert "estimated deployment exposure diagnostic" in normalized
    assert "not a placement planner" in normalized
    assert "0.0%" in response.text
    assert "safe-zone-outline" in response.text
    assert "coverage-image" in response.text
    assert "threat-projection-image" in response.text
    assert "<script" not in response.text
    for forbidden in ("legal", " safe", "recommended", "optimal", "likely", "guaranteed"):
        assert forbidden not in normalized_without_classes


def test_deployment_exposure_post_redirect_preserves_manual_values(monkeypatch) -> None:
    packet = server.repository.default_packet()
    resolved_calls: list[tuple[str | None, str | None, str | None, str | None]] = []

    class FakeService:
        def resolve_packet_id(
            self,
            *,
            packet_id: str | None = None,
            player_a: str | None = None,
            player_b: str | None = None,
            layout_variant: str | None = None,
        ) -> str:
            resolved_calls.append((packet_id, player_a, player_b, layout_variant))
            return packet.id

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.post(
        "/deployment-exposure",
        data={
            "packet_id": packet.id,
            "player_a": "Take and Hold",
            "player_b": "Reconnaissance",
            "layout_variant": "B",
            "deployment_zone_id": "attacker",
            "friendly_x": "10",
            "friendly_y": "5",
            "friendly_base": "1.57",
            "enemy_x": "38",
            "enemy_y": "52",
            "enemy_base": "1.57",
            "enemy_move": "0",
            "enemy_threat": "1",
            "enemy_mode": "raw-range",
            "enemy_movement_profile": "ground-mobile",
            "exposure_mode": "threat-and-los",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert resolved_calls == [(packet.id, "Take and Hold", "Reconnaissance", "B")]
    assert response.headers["location"] == (
        f"/deployment-exposure?packet_id={packet.id}&deployment_zone_id=attacker"
        "&friendly_x=10.0&friendly_y=5.0&friendly_base=1.57"
        "&enemy_x=38.0&enemy_y=52.0&enemy_base=1.57&enemy_move=0.0"
        "&enemy_threat=1.0&enemy_mode=raw-range&enemy_movement_profile=ground-mobile"
        "&exposure_mode=threat-and-los"
    )


def test_deployment_scorecard_route_uses_manual_controls_and_cautious_language(
    monkeypatch,
) -> None:
    calls: list[tuple[str, str, float, float, str, str, str]] = []
    packet = server.repository.default_packet()
    packet_selector = WarhammerCompanionService(
        paths=server.ingestion_paths,
        repository=StaticMapRepository([packet]),
        codex_backend=server.codex_backend,
    ).packet_selector_state(packet_id=packet.id)

    class FakeService:
        def deployment_scorecard_state(
            self,
            *,
            packet_id: str | None = None,
            player_a: str | None = None,
            player_b: str | None = None,
            layout_variant: str | None = None,
            deployment_zone_id: str = "attacker",
            friendly_x: float = 10.0,
            friendly_y: float = 5.0,
            friendly_base: float = 1.57,
            enemy_x: float = 38.0,
            enemy_y: float = 52.0,
            enemy_base: float = 1.57,
            enemy_move: float = 0.0,
            enemy_threat: float = 1.0,
            enemy_mode: str = "raw-range",
            enemy_movement_profile: str = "ground-non-mobile",
            exposure_mode: str = "threat-and-los",
            turn_order: str = "going-first",
        ) -> DeploymentScorecardState:
            calls.append(
                (
                    packet_id or "",
                    deployment_zone_id,
                    friendly_x,
                    enemy_x,
                    enemy_movement_profile,
                    exposure_mode,
                    turn_order,
                )
            )
            return _scorecard_state(
                packet=packet,
                packet_selector=packet_selector,
                readiness="estimated",
                turn_order=turn_order,
                components=[
                    DeploymentScorecardComponent(
                        component_id="deployment-fit",
                        label="Deployment fit",
                        assessment="checked",
                        detail="Manual footprint fits selected deployment zone.",
                        source_ref_ids=("deployment-exposure",),
                    ),
                    DeploymentScorecardComponent(
                        component_id="selected-exposure",
                        label="Selected exposure",
                        assessment="checked",
                        detail="Threat probability at center is 0.0%.",
                        source_ref_ids=("deployment-exposure",),
                    ),
                    DeploymentScorecardComponent(
                        component_id="mission-readiness",
                        label="Mission readiness",
                        assessment="warning",
                        detail="Mission context is source-pending.",
                        source_ref_ids=("mission-pack",),
                    ),
                    DeploymentScorecardComponent(
                        component_id="turn-order-assumption",
                        label="Turn order assumption",
                        assessment="warning",
                        detail=f"Manual turn order: {turn_order}.",
                        source_ref_ids=(),
                    ),
                ],
                warning_details=[
                    "Mission context is source-pending.",
                    "Turn-order assumption is manual.",
                ],
                map_svg=(
                    '<svg class="map-svg" role="img" aria-label="fake deployment scorecard">'
                    '<g data-toolkit-overlay="deployment-scorecard">'
                    '<image class="threat-projection-image"/>'
                    "</g></svg>"
                ),
                enemy_movement_profile=enemy_movement_profile,
                enemy_movement_profile_label="Fly: Hover / no-cost Take to the Skies",
                enemy_effective_move=8.0,
                input_hash="sha256:test-scorecard",
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        f"/deployment-scorecard?packet_id={packet.id}&deployment_zone_id=attacker"
        "&friendly_x=10&friendly_y=5&friendly_base=1.57"
        "&enemy_x=38&enemy_y=52&enemy_base=1.57&enemy_move=0&enemy_threat=1"
        "&enemy_mode=raw-range&enemy_movement_profile=fly-hover-take-to-skies"
        "&exposure_mode=threat-and-los&turn_order=going-second"
    )
    normalized = " ".join(response.text.split()).lower()
    main_html = response.text.split("<main", 1)[1].split("</main>", 1)[0]
    normalized_main = " ".join(main_html.split()).lower()

    assert response.status_code == 200
    assert calls == [
        (
            packet.id,
            "attacker",
            10.0,
            38.0,
            "fly-hover-take-to-skies",
            "threat-and-los",
            "going-second",
        )
    ]
    assert "Deployment Scorecard" in response.text
    assert 'name="deployment_zone_id"' in response.text
    assert 'name="friendly_x"' in response.text
    assert 'name="enemy_x"' in response.text
    assert 'name="enemy_movement_profile"' in response.text
    assert 'name="turn_order"' in response.text
    assert 'value="fly-hover-take-to-skies" selected' in response.text
    assert 'value="going-second" selected' in response.text
    assert "Fly: Hover / no-cost Take to the Skies" in response.text
    assert "Mission readiness" in response.text
    assert "Turn order assumption" in response.text
    assert "source-pending" in normalized
    assert "threat-projection-image" in response.text
    assert "<script" not in response.text
    for forbidden in (
        "legal",
        " safe",
        "optimal",
        "recommended",
        "likely",
        "guaranteed",
        "preferred",
        "pairing",
    ):
        assert forbidden not in normalized_main


def test_deployment_scorecard_route_renders_blocked_output_without_tactical_overlay(
    monkeypatch,
) -> None:
    packet = server.repository.default_packet()
    packet_selector = WarhammerCompanionService(
        paths=server.ingestion_paths,
        repository=StaticMapRepository([packet]),
        codex_backend=server.codex_backend,
    ).packet_selector_state(packet_id=packet.id)

    class FakeService:
        def deployment_scorecard_state(self, **kwargs) -> DeploymentScorecardState:
            return _scorecard_state(
                packet=packet,
                packet_selector=packet_selector,
                readiness="blocked",
                turn_order=kwargs.get("turn_order", "alpha-strike"),
                components=[
                    DeploymentScorecardComponent(
                        component_id="turn-order-assumption",
                        label="Turn order assumption",
                        assessment="blocked",
                        detail="Turn order must be going-first or going-second.",
                        source_ref_ids=(),
                    )
                ],
                block_reason_details=[
                    "invalid-turn-order: Turn order must be going-first or going-second."
                ],
                warning_details=["Manual input cannot be evaluated until blockers are resolved."],
                map_svg='<svg class="map-svg" role="img" aria-label="fake blocked map"></svg>',
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        f"/deployment-scorecard?packet_id={packet.id}&deployment_zone_id=attacker"
        "&friendly_x=10&friendly_y=5&friendly_base=1.57"
        "&enemy_x=38&enemy_y=52&enemy_base=1.57&enemy_move=0&enemy_threat=1"
        "&enemy_mode=raw-range&exposure_mode=threat-and-los&turn_order=alpha-strike"
    )

    assert response.status_code == 200
    assert "blocked" in response.text.lower()
    assert "invalid-turn-order" in response.text
    assert "invalid-turn-order: invalid-turn-order" not in response.text
    assert "data-toolkit-overlay" not in response.text
    assert "safe-zone-outline" not in response.text
    assert "coverage-image" not in response.text
    assert "threat-projection-image" not in response.text


def test_deployment_scorecard_post_redirect_preserves_manual_values(monkeypatch) -> None:
    packet = server.repository.default_packet()
    resolved_calls: list[tuple[str | None, str | None, str | None, str | None]] = []

    class FakeService:
        def resolve_packet_id(
            self,
            *,
            packet_id: str | None = None,
            player_a: str | None = None,
            player_b: str | None = None,
            layout_variant: str | None = None,
        ) -> str:
            resolved_calls.append((packet_id, player_a, player_b, layout_variant))
            return packet.id

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.post(
        "/deployment-scorecard",
        data={
            "packet_id": packet.id,
            "player_a": "Take and Hold",
            "player_b": "Reconnaissance",
            "layout_variant": "B",
            "deployment_zone_id": "attacker",
            "friendly_x": "10",
            "friendly_y": "5",
            "friendly_base": "1.57",
            "enemy_x": "38",
            "enemy_y": "52",
            "enemy_base": "1.57",
            "enemy_move": "0",
            "enemy_threat": "1",
            "enemy_mode": "raw-range",
            "enemy_movement_profile": "fly-hover-take-to-skies",
            "exposure_mode": "threat-and-los",
            "turn_order": "going-second",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert resolved_calls == [(packet.id, "Take and Hold", "Reconnaissance", "B")]
    assert response.headers["location"] == (
        f"/deployment-scorecard?packet_id={packet.id}&deployment_zone_id=attacker"
        "&friendly_x=10.0&friendly_y=5.0&friendly_base=1.57"
        "&enemy_x=38.0&enemy_y=52.0&enemy_base=1.57&enemy_move=0.0"
        "&enemy_threat=1.0&enemy_mode=raw-range"
        "&enemy_movement_profile=fly-hover-take-to-skies&exposure_mode=threat-and-los"
        "&turn_order=going-second"
    )


def test_damage_profile_route_uses_manual_math_controls_and_cautious_language(
    monkeypatch,
) -> None:
    calls: list[tuple[float, int, int, int, float, float, float]] = []

    class FakeService:
        def damage_profile_state(
            self,
            *,
            attacks: float = 2,
            hit: int = 4,
            wound: int = 4,
            save: int = 4,
            damage: float = 2,
            wounds: float = 2,
            models: float = 3,
        ) -> DamageProfileState:
            calls.append((attacks, hit, wound, save, damage, wounds, models))
            return DamageProfileState(
                attacks=attacks,
                hit_target=hit,
                wound_target=wound,
                save_target=save,
                damage_per_unsaved_wound=damage,
                target_wounds_per_model=wounds,
                target_model_count=models,
                is_blocked=False,
                expected_hits=1.0,
                expected_wounds=0.5,
                expected_unsaved_wounds=0.25,
                expected_damage=0.5,
                expected_models_destroyed=0.25,
                probability_destroying_at_least_one_model=15 / 64,
                unsaved_wound_distribution=[
                    DamageProbabilityRow(
                        outcome=0, numerator=49, denominator=64, probability=49 / 64
                    ),
                    DamageProbabilityRow(
                        outcome=1, numerator=14, denominator=64, probability=14 / 64
                    ),
                    DamageProbabilityRow(
                        outcome=2, numerator=1, denominator=64, probability=1 / 64
                    ),
                ],
                models_destroyed_distribution=[
                    DamageProbabilityRow(
                        outcome=0, numerator=49, denominator=64, probability=49 / 64
                    ),
                    DamageProbabilityRow(
                        outcome=1, numerator=14, denominator=64, probability=14 / 64
                    ),
                    DamageProbabilityRow(
                        outcome=2, numerator=1, denominator=64, probability=1 / 64
                    ),
                ],
                warning_details=[
                    (
                        "Manual estimate; not roster-derived; not official/profile-resolved; "
                        "effective save supplied by user; unsupported effects omitted; "
                        "no source-backed rules/list claim."
                    )
                ],
                block_reason_details=[],
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        "/damage-profile?attacks=2&hit=4&wound=4&save=4&damage=2&wounds=2&models=3"
    )
    normalized = " ".join(response.text.split()).lower()
    normalized_without_negative_claim = normalized.replace("not official/profile-resolved", "")

    assert response.status_code == 200
    assert calls == [(2.0, 4, 4, 4, 2.0, 2.0, 3.0)]
    assert "Damage Profile" in response.text
    assert 'name="attacks"' in response.text
    assert 'name="hit"' in response.text
    assert 'name="wound"' in response.text
    assert 'name="save"' in response.text
    assert 'name="damage"' in response.text
    assert 'name="wounds"' in response.text
    assert 'name="models"' in response.text
    assert "manual estimate" in normalized
    assert "effective save supplied by user" in normalized
    assert "expected damage" in normalized
    assert "0.50" in response.text
    assert "49/64" in response.text
    assert "<script" not in response.text
    for forbidden in (
        "legal",
        "optimal",
        "recommended",
        "likely",
        "target priority",
        "bad target",
        "official",
        "profile-resolved",
    ):
        assert forbidden not in normalized_without_negative_claim


def test_damage_profile_route_shows_blocked_manual_inputs(monkeypatch) -> None:
    class FakeService:
        def damage_profile_state(
            self,
            *,
            attacks: float = 2,
            hit: int = 4,
            wound: int = 4,
            save: int = 4,
            damage: float = 2,
            wounds: float = 2,
            models: float = 3,
        ) -> DamageProfileState:
            return DamageProfileState(
                attacks=attacks,
                hit_target=hit,
                wound_target=wound,
                save_target=save,
                damage_per_unsaved_wound=damage,
                target_wounds_per_model=wounds,
                target_model_count=models,
                is_blocked=True,
                expected_hits=0.0,
                expected_wounds=0.0,
                expected_unsaved_wounds=0.0,
                expected_damage=0.0,
                expected_models_destroyed=0.0,
                probability_destroying_at_least_one_model=0.0,
                unsaved_wound_distribution=[],
                models_destroyed_distribution=[],
                warning_details=["Manual estimate cannot run until manual inputs are valid."],
                block_reason_details=["Attack count must be a finite positive integer."],
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        "/damage-profile?attacks=0&hit=4&wound=4&save=4&damage=2&wounds=2&models=3"
    )
    normalized = " ".join(response.text.split()).lower()

    assert response.status_code == 200
    assert "blocked" in normalized
    assert "attack count must be a finite positive integer" in normalized
    assert "traceback" not in normalized
    assert "internal server error" not in normalized
    assert "<script" not in response.text


def test_damage_profile_post_redirect_preserves_manual_values() -> None:
    client = TestClient(server.app)

    response = client.post(
        "/damage-profile",
        data={
            "attacks": "2",
            "hit": "4",
            "wound": "4",
            "save": "4",
            "damage": "2",
            "wounds": "2",
            "models": "3",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/damage-profile?attacks=2.0&hit=4&wound=4&save=4&damage=2.0&wounds=2.0&models=3.0"
    )


def test_mission_pack_route_renders_source_safe_summary_without_javascript(monkeypatch) -> None:
    source = MissionSourceRef(
        source_ref_id="public-mission-sheet-candidate",
        label="Public mission sheet candidate",
        source_kind="public_sheet_candidate",
        trust="untrusted_candidate",
        retrieval_status="not_fetched",
        url="https://docs.google.com/spreadsheets/d/test/edit?gid=1565185881#gid=1565185881",
        sheet_id="test",
        gid="1565185881",
        content_hash=None,
        warnings=("Public mission sheet not fetched and not ingested.",),
    )
    mission = MissionRecord(
        mission_id="primary-battlefield-dominance",
        label="Battlefield Dominance",
        category="primary",
        readiness="estimated",
        source_ref_ids=("event-companion-layout-metadata",),
        source_anchors=(
            MissionSourceAnchor(
                source_ref_id="event-companion-layout-metadata",
                anchor_id="event-companion-page-9",
                label="Event Companion page 9",
                page_number=9,
            ),
        ),
        mechanics_readiness="source-pending",
    )

    class FakeService:
        def mission_pack_state(self) -> MissionPackState:
            return MissionPackState(
                readiness="estimated",
                mission_count=1,
                source_refs=[source],
                primary_missions=[mission],
                warning_details=[
                    "Mission mechanics, scoring, and actions are source-pending.",
                    "Public mission sheet is not fetched and not ingested.",
                ],
                pack=MissionPack(
                    pack_id="mission-pack-pariah-nexus-skeleton",
                    label="Mission Pack Skeleton",
                    schema_version="mission-pack/v0",
                    readiness="estimated",
                    source_ref_ids=(source.source_ref_id,),
                    primary_missions=(mission,),
                    warnings=("Mission mechanics, scoring, and actions are source-pending.",),
                ),
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get("/mission-pack")
    normalized = " ".join(response.text.split()).lower()

    assert response.status_code == 200
    assert "Mission Pack" in response.text
    assert "Battlefield Dominance" in response.text
    assert "Event Companion page 9" in response.text
    assert "not fetched" in normalized
    assert "not ingested" in normalized
    assert "source-pending" in normalized
    assert "<script" not in response.text
    for forbidden in ("legal", "optimal", "recommended", "likely", "pairing-score"):
        assert forbidden not in normalized


def test_team_pairing_route_renders_degraded_matrix_without_authority_claims() -> None:
    client = TestClient(server.app)

    response = client.get("/team-pairing?friendly_lists=Alpha%0ABeta&opponent_lists=Gamma%0ADelta")
    normalized = " ".join(response.text.split()).lower()

    assert response.status_code == 200
    assert "Team Pairing" in response.text
    assert "degraded" in normalized
    assert "Alpha" in response.text
    assert "Beta" in response.text
    assert "Gamma" in response.text
    assert "Delta" in response.text
    assert "unsupported-data" in response.text
    assert "shared scenario" in normalized
    assert "not pair-specific" in normalized
    assert "<script" not in response.text
    for forbidden in (
        "legal",
        "safe",
        "optimal",
        "recommended",
        "likely",
        "guaranteed",
        "preferred",
        "pairing score",
        "expected points",
        "win probability",
        "favored",
        "calibrated",
        "docs.google.com",
        PUBLIC_MISSION_SHEET_GID,
        PUBLIC_MISSION_SHEET_ID.lower(),
        "mission card",
    ):
        assert forbidden not in normalized


def test_team_pairing_route_normalizes_and_escapes_manual_labels() -> None:
    client = TestClient(server.app)

    normalized_response = client.get(
        "/team-pairing?friendly_lists=Alpha%20%20Prime%2C%2C%20%20Beta%0AControl%07Name"
        "&opponent_lists=Gamma%2C%2C%20Delta"
    )
    script_response = client.get(
        "/team-pairing?friendly_lists=%3Cscript%3Ealert(1)%3C%2Fscript%3E&opponent_lists=Gamma"
    )

    assert normalized_response.status_code == 200
    assert "Alpha Prime" in normalized_response.text
    assert "Alpha  Prime" not in normalized_response.text
    assert "Beta" in normalized_response.text
    assert "ControlName" in normalized_response.text
    assert normalized_response.text.index("Alpha Prime") < normalized_response.text.index("Beta")
    assert normalized_response.text.index("Beta") < normalized_response.text.index("ControlName")
    assert "Gamma" in normalized_response.text
    assert "Delta" in normalized_response.text
    assert "<script" not in script_response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in script_response.text


def test_team_pairing_route_shows_blocked_manual_label_inputs() -> None:
    client = TestClient(server.app)

    response = client.get("/team-pairing?friendly_lists=&opponent_lists=Gamma%0ADelta")
    overflow = client.get(
        "/team-pairing?friendly_lists=A%0AB%0AC%0AD%0AE%0AF%0AG%0AH%0AI&opponent_lists=Gamma"
    )
    normalized = " ".join(response.text.split()).lower()

    assert response.status_code == 200
    assert "blocked" in normalized
    assert "missing-friendly-lists" in response.text
    assert "data-team-pairing-cell" not in response.text
    assert "traceback" not in normalized
    assert "internal server error" not in normalized
    assert "too-many-friendly-lists" in overflow.text
    assert "data-team-pairing-cell" not in overflow.text


def test_team_pairing_post_redirect_preserves_labels_and_packet_selection(monkeypatch) -> None:
    packet = server.repository.default_packet()
    resolved_calls: list[tuple[str | None, str | None, str | None, str | None]] = []

    class FakeService:
        def resolve_packet_id(
            self,
            *,
            packet_id: str | None = None,
            player_a: str | None = None,
            player_b: str | None = None,
            layout_variant: str | None = None,
        ) -> str:
            resolved_calls.append((packet_id, player_a, player_b, layout_variant))
            return packet.id

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.post(
        "/team-pairing",
        data={
            "packet_id": packet.id,
            "player_a": "Take and Hold",
            "player_b": "Reconnaissance",
            "layout_variant": "B",
            "friendly_lists": "Alpha\nBeta",
            "opponent_lists": "Gamma\nDelta",
        },
        follow_redirects=False,
    )
    location = urlparse(response.headers["location"])
    params = parse_qs(location.query)

    assert response.status_code == 303
    assert resolved_calls == [(packet.id, "Take and Hold", "Reconnaissance", "B")]
    assert location.path == "/team-pairing"
    assert params["packet_id"] == [packet.id]
    assert params["friendly_lists"] == ["Alpha\nBeta"]
    assert params["opponent_lists"] == ["Gamma\nDelta"]


def test_pages_do_not_load_custom_frontend_javascript() -> None:
    client = TestClient(server.app)

    response = client.get("/viewer")

    assert response.status_code == 200
    assert "<script" not in response.text
    assert "app.js" not in response.text


def test_viewer_reports_light_review_feature_counts() -> None:
    client = TestClient(server.app)

    response = client.get("/viewer")

    assert response.status_code == 200
    assert "Dense Blockers" in response.text
    assert "Light / Review Features" in response.text
    assert "Floor / Platform Review" in response.text


def test_viewer_groups_official_packets_by_dispositions_and_layout_variant(monkeypatch) -> None:
    packets = [
        _official_packet().model_copy(
            update={
                "id": f"official-event-companion-page-{page}",
                "name": f"Official Page {page}",
                "layout_metadata": official_layout_metadata_for_page(page),
            }
        )
        for page in range(9, 54)
    ]
    monkeypatch.setattr(
        server,
        "service",
        WarhammerCompanionService(
            paths=server.ingestion_paths,
            repository=StaticMapRepository(list(reversed(packets))),
            codex_backend=server.codex_backend,
        ),
    )
    client = TestClient(server.app)

    response = client.get(
        "/viewer?player_a=Take%20and%20Hold&player_b=Take%20and%20Hold&layout_variant=A"
    )
    normalized_response = " ".join(response.text.split())

    assert response.status_code == 200
    assert 'name="player_a"' in response.text
    assert 'name="player_b"' in response.text
    assert 'name="layout_variant"' in response.text
    assert "Player A disposition" in response.text
    assert "Player B disposition" in response.text
    assert "Terrain layout" in response.text
    assert response.text.count('value="Take and Hold"') == 2
    assert response.text.count('value="Priority Assets"') == 2
    assert response.text.count('value="A"') == 1
    assert response.text.count('value="B"') == 1
    assert response.text.count('value="C"') == 1
    assert "Layout A - Battlefield Dominance vs Battlefield Dominance" in response.text
    assert "Layout C - Battlefield Dominance vs Battlefield Dominance" in response.text
    assert 'class="packet-summary"' in response.text
    assert "Force dispositions" in response.text
    assert "Primary missions" in response.text
    assert "Layout source" in response.text
    assert "Layout A - Event Companion page 9" in normalized_response
    assert "First player" in response.text
    assert "Second player" in response.text


def test_viewer_resolves_packet_from_selector_query(monkeypatch) -> None:
    packets = [
        _official_packet().model_copy(
            update={
                "id": f"official-event-companion-page-{page}",
                "name": f"Official Page {page}",
                "layout_metadata": official_layout_metadata_for_page(page),
            }
        )
        for page in range(9, 54)
    ]
    monkeypatch.setattr(
        server,
        "service",
        WarhammerCompanionService(
            paths=server.ingestion_paths,
            repository=StaticMapRepository(list(reversed(packets))),
            codex_backend=server.codex_backend,
        ),
    )
    client = TestClient(server.app)

    response = client.get(
        "/viewer?player_a=Take%20and%20Hold&player_b=Reconnaissance&layout_variant=C"
    )

    assert response.status_code == 200
    assert "Layout C - Event Companion page 20" in " ".join(response.text.split())
    assert "Take and Hold vs Reconnaissance" in " ".join(response.text.split())


def test_settings_exposes_codex_account_controls_without_javascript(monkeypatch) -> None:
    class FakeCodexBackend:
        def current_status(self):
            from warhammer_companion.integrations.codex_backend import CodexBackendStatus

            return CodexBackendStatus(
                state="not-authenticated",
                label="Codex SDK ready",
                detail="No Codex account is signed in.",
                sdk_available=True,
                sdk_version="0.1",
                runtime_label="Codex Test",
                runtime_source="openai-codex bundled runtime",
                runtime_package_version="0.1",
                state_home="data/codex-home",
                authenticated=False,
                auth_method=None,
                account_label="Not signed in",
                requires_openai_auth=True,
                can_login=True,
                can_logout=False,
                active_login_label=None,
            )

    monkeypatch.setattr(
        server,
        "service",
        WarhammerCompanionService(
            paths=server.ingestion_paths,
            repository=server.repository,
            codex_backend=FakeCodexBackend(),
        ),
    )
    client = TestClient(server.app)

    response = client.get("/settings")

    assert response.status_code == 200
    assert "App Python Backend" in response.text
    assert "Codex Account" in response.text
    assert response.text.count("metric metric-status") == 2
    assert "Start Codex login" in response.text
    assert "ChatGPT Subscription" not in response.text
    assert "Open ChatGPT login" not in response.text
    assert "https://chatgpt.com" not in response.text
    assert "<script" not in response.text


def test_settings_status_values_use_wrapping_layout() -> None:
    css = (server.PACKAGE_DIR / "static" / "style.css").read_text()

    assert "settings-status-list" in css
    assert "grid-template-columns: minmax(8rem, 0.45fr) minmax(0, 1fr)" in css
    assert "tag-wrap" in css
    assert "white-space: normal" in css
    assert "overflow-wrap: anywhere" in css


def test_toolbar_packet_select_does_not_force_horizontal_overflow() -> None:
    css = (server.PACKAGE_DIR / "static" / "style.css").read_text()

    assert ".toolbar" in css
    assert "min-width: 0" in css
    assert ".toolbar > label:first-child" in css
    assert "flex: 1 1 280px" in css
    assert ".toolbar > label:first-child select" in css
    assert "width: 100%" in css
    assert ".selector-grid" in css
    assert "grid-template-columns: repeat(3, minmax(160px, 1fr))" in css
    assert ".sidebar" in css
    assert ".main" in css


def test_codex_browser_login_route_redirects_to_sdk_auth_url(monkeypatch) -> None:
    class FakeStart:
        auth_url = "https://auth.example/login"

    class FakeService:
        def start_codex_login(self):
            return FakeStart()

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.post("/settings/codex/login", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "https://auth.example/login"


def test_codex_logout_route_redirects_to_settings(monkeypatch) -> None:
    calls: list[str] = []

    class FakeService:
        def logout_codex(self) -> None:
            calls.append("logout")

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.post("/settings/codex/logout", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/settings?codex_action=logout-complete"
    assert calls == ["logout"]


def _official_packet() -> MapPacket:
    return SAMPLE_PACKETS[0].model_copy(
        update={
            "id": "official-event-companion-page-1",
            "name": "Official Page 1",
            "source": "test official extraction",
        }
    )


def _scorecard_state(
    *,
    packet: MapPacket,
    packet_selector,
    readiness: str,
    turn_order: str,
    components: list[DeploymentScorecardComponent],
    warning_details: list[str],
    map_svg: str,
    block_reason_details: list[str] | None = None,
    enemy_movement_profile: str = "ground-non-mobile",
    enemy_movement_profile_label: str = "Ground non-mobile",
    enemy_effective_move: float = 0.0,
    input_hash: str = "",
) -> DeploymentScorecardState:
    return DeploymentScorecardState(
        packet=packet,
        packet_groups=[],
        packet_selector=packet_selector,
        deployment_zone_options=[
            DeploymentZoneSelectOption(id=zone.id, label=zone.label)
            for zone in packet.deployment_zones
        ],
        deployment_zone_id="attacker",
        friendly_x=10.0,
        friendly_y=5.0,
        friendly_base=1.57,
        enemy_x=38.0,
        enemy_y=52.0,
        enemy_base=1.57,
        enemy_move=0.0,
        enemy_threat=1.0,
        enemy_mode="raw-range",
        exposure_mode="threat-and-los",
        turn_order=turn_order,
        enemy_threat_modes=["raw-range", "fixed-move-plus-range"],
        exposure_modes=["threat-only", "los-only", "threat-or-los", "threat-and-los"],
        turn_order_options=["going-first", "going-second"],
        readiness=readiness,
        is_blocked=readiness == "blocked",
        not_exposed_under_assumptions=readiness != "blocked",
        threat_probability_at_center=0.0,
        components=components,
        block_reason_details=block_reason_details or [],
        warning_details=warning_details,
        map_svg=map_svg,
        enemy_movement_profile=enemy_movement_profile,
        enemy_movement_profile_label=enemy_movement_profile_label,
        enemy_effective_move=enemy_effective_move,
        input_hash=input_hash,
    )
