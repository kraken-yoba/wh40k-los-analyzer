from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.packet_io import write_packet
from warhammer_companion.domain.repository import FileBackedMapRepository
from warhammer_companion.ingestion.artifacts import IngestionPaths
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

    monkeypatch.setattr(server, "ingestion_paths", paths)
    monkeypatch.setattr(server, "repository", repository)
    monkeypatch.setattr(server, "run_official_ingestion", fake_ingestion)
    server._cached_heatmap_svg.cache_clear()
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
    monkeypatch.setattr(server, "ingestion_paths", paths)
    monkeypatch.setattr(server, "repository", repository)
    server._cached_heatmap_svg.cache_clear()
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

    def fake_heatmap_svg(packet_id: str, zone_id: str, source: str, offset_inches: int) -> str:
        calls.append((packet_id, zone_id, source, offset_inches))
        return '<svg class="map-svg" role="img" aria-label="fake map"></svg>'

    monkeypatch.setattr(server, "_cached_heatmap_svg", fake_heatmap_svg)
    client = TestClient(server.app)
    packet = server.repository.default_packet()

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

    monkeypatch.setattr(server, "codex_backend", FakeCodexBackend())
    client = TestClient(server.app)

    response = client.get("/settings")

    assert response.status_code == 200
    assert "App Python Backend" in response.text
    assert "Codex Account" in response.text
    assert "Start Codex login" in response.text
    assert "ChatGPT Subscription" not in response.text
    assert "Open ChatGPT login" not in response.text
    assert "https://chatgpt.com" not in response.text
    assert "<script" not in response.text


def test_codex_browser_login_route_redirects_to_sdk_auth_url(monkeypatch) -> None:
    class FakeStart:
        auth_url = "https://auth.example/login"

    class FakeCodexBackend:
        def start_chatgpt_login(self):
            return FakeStart()

    monkeypatch.setattr(server, "codex_backend", FakeCodexBackend())
    client = TestClient(server.app)

    response = client.post("/settings/codex/login", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "https://auth.example/login"


def test_codex_logout_route_redirects_to_settings(monkeypatch) -> None:
    calls: list[str] = []

    class FakeCodexBackend:
        def logout(self) -> None:
            calls.append("logout")

    monkeypatch.setattr(server, "codex_backend", FakeCodexBackend())
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
