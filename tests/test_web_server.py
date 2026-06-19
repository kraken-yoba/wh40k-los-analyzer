from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.application.view_models import HeatmapState
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

    class FakeService:
        def heatmap_state(
            self,
            *,
            packet_id: str | None = None,
            zone_id: str = "attacker",
            source: str = "edge",
            offset_inches: int = 0,
        ) -> HeatmapState:
            resolved_packet_id = packet_id or packet.id
            calls.append((resolved_packet_id, zone_id, source, offset_inches))
            return HeatmapState(
                packet=packet,
                packet_groups=[],
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

    response = client.get("/viewer?packet_id=official-event-companion-page-9")
    normalized_response = " ".join(response.text.split())

    assert response.status_code == 200
    assert response.text.count("<optgroup") == 15
    assert response.text.count('value="official-event-companion-page-') == 45
    assert '<optgroup label="Take and Hold vs Take and Hold">' in response.text
    assert (
        "Layout A - Take and Hold vs Take and Hold (Battlefield Dominance vs Battlefield Dominance)"
    ) in response.text
    assert (
        "Layout B - Take and Hold vs Take and Hold (Battlefield Dominance vs Battlefield Dominance)"
    ) in response.text
    assert (
        "Layout C - Take and Hold vs Take and Hold (Battlefield Dominance vs Battlefield Dominance)"
    ) in response.text
    assert '<optgroup label="Priority Assets vs Priority Assets">' in response.text
    assert ("Layout C - Priority Assets vs Priority Assets (Sabotage vs Sabotage)") in response.text
    assert 'class="packet-summary"' in response.text
    assert "Force dispositions" in response.text
    assert "Primary missions" in response.text
    assert "Layout source" in response.text
    assert "Layout A - Event Companion page 9" in normalized_response
    assert "First player" in response.text
    assert "Second player" in response.text


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
    assert ".toolbar label:first-child" in css
    assert "flex: 1 1 280px" in css
    assert ".toolbar label:first-child select" in css
    assert "width: 100%" in css
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
