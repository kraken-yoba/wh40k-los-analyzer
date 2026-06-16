from pathlib import Path

from fastapi.testclient import TestClient
from fortyk_los_backend.app import app

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_index_serves_local_gui_shell() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Warhammer 40k LOS Analyzer" in response.text
    assert "Fixture-backed analysis ready" in response.text
    assert "/static/app.js" in response.text


def test_index_exposes_core_gui_workflow_controls() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    html = response.text
    for expected in [
        'id="layout-select"',
        'id="base-diameter"',
        'id="board-canvas"',
        'id="source-status"',
        'id="footprint-evidence"',
        'id="layout-metadata"',
        'id="validation-panel"',
        'id="los-result"',
        'id="heatmap-button"',
        'id="exposure-button"',
        'id="terrain-coverage-button"',
        'id="export-button"',
    ]:
        assert expected in html


def test_client_script_handles_async_action_errors_in_panels() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "function renderError" in script
    assert "async function runPanelAction" in script
    assert "runPanelAction(losResult" in script
    assert "runPanelAction(analysisResult" in script


def test_client_script_renders_layout_metadata() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const layoutMetadata" in script
    assert "function renderLayoutMetadata" in script
    assert "validation_status" in script
    assert "source_document_id" in script


def test_client_script_renders_terrain_footprint_evidence() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const footprintEvidence" in script
    assert "function renderFootprintEvidence" in script
    assert "/api/extraction/terrain-footprints" in script
    assert "terrain-footprint-vector-v1" in script


def test_client_script_avoids_inner_html_for_api_derived_data() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert ".innerHTML" not in script
