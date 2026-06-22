from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.application.view_models import (
    DeploymentExposureState,
    DeploymentZoneSelectOption,
    HeatmapState,
    HiddenCoverageState,
    MovementReachState,
    TerrainSelectOption,
    ThreatRangeState,
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
    calls: list[tuple[str, float, float, float, float, float, float, str]] = []
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
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        f"/movement-reach?packet_id={packet.id}&start_x=16&start_y=10"
        "&target_x=22&target_y=10&base=1.57&move=6&mode=advance"
    )
    normalized = " ".join(response.text.split()).lower()

    assert response.status_code == 200
    assert calls == [(packet.id, 16.0, 10.0, 22.0, 10.0, 1.57, 6.0, "advance")]
    assert "Movement Reach" in response.text
    assert 'name="start_x"' in response.text
    assert 'name="target_x"' in response.text
    assert 'name="move"' in response.text
    assert 'name="mode"' in response.text
    assert 'value="advance" selected' in response.text
    assert "estimated 2d geometry" in normalized
    assert "no straight-corridor blocker found under current assumptions" in normalized
    assert "movement-envelope-image" in response.text
    assert "<script" not in response.text
    for forbidden in ("legal", " safe", "recommended", "optimal", "likely"):
        assert forbidden not in normalized


def test_threat_range_route_uses_manual_probability_controls_and_cautious_language(
    monkeypatch,
) -> None:
    calls: list[tuple[str, float, float, float, float, float, float, float, str]] = []
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
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        f"/threat-range?packet_id={packet.id}&source_x=16&source_y=10"
        "&target_x=24&target_y=10&base=1.57&move=6&threat=2&mode=2d6-move-plus-range"
    )
    normalized = " ".join(response.text.split()).lower()

    assert response.status_code == 200
    assert calls == [(packet.id, 16.0, 10.0, 24.0, 10.0, 1.57, 6.0, 2.0, "2d6-move-plus-range")]
    assert "Threat Range" in response.text
    assert 'name="source_x"' in response.text
    assert 'name="target_x"' in response.text
    assert 'name="threat"' in response.text
    assert 'name="mode"' in response.text
    assert 'value="2d6-move-plus-range" selected' in response.text
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
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert resolved_calls == [(packet.id, "Take and Hold", "Reconnaissance", "B")]
    assert response.headers["location"] == (
        f"/threat-range?packet_id={packet.id}&source_x=16.0&source_y=10.0"
        "&target_x=24.0&target_y=10.0&base=1.57&move=6.0&threat=2.0"
        "&mode=2d6-move-plus-range"
    )


def test_deployment_exposure_route_uses_manual_controls_and_cautious_language(
    monkeypatch,
) -> None:
    packet = server.repository.default_packet()
    real_service = server.service
    calls: list[tuple[str | None, str, float, float, str]] = []

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
            exposure_mode: str = "threat-and-los",
        ) -> DeploymentExposureState:
            calls.append((packet_id, deployment_zone_id, friendly_x, enemy_x, exposure_mode))
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
            )

    monkeypatch.setattr(server, "service", FakeService())
    client = TestClient(server.app)

    response = client.get(
        f"/deployment-exposure?packet_id={packet.id}&deployment_zone_id=attacker"
        "&friendly_x=10&friendly_y=5&friendly_base=1.57"
        "&enemy_x=38&enemy_y=52&enemy_base=1.57&enemy_move=0&enemy_threat=1"
        "&enemy_mode=raw-range&exposure_mode=threat-and-los"
    )
    normalized = " ".join(response.text.split()).lower()
    normalized_without_classes = normalized.replace("safe-zone-outline", "")

    assert response.status_code == 200
    assert calls == [(packet.id, "attacker", 10.0, 38.0, "threat-and-los")]
    assert "Deployment Exposure" in response.text
    assert 'name="deployment_zone_id"' in response.text
    assert 'name="friendly_x"' in response.text
    assert 'name="enemy_x"' in response.text
    assert 'name="enemy_mode"' in response.text
    assert 'name="exposure_mode"' in response.text
    assert 'value="threat-and-los" selected' in response.text
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
        "&enemy_threat=1.0&enemy_mode=raw-range&exposure_mode=threat-and-los"
    )


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
