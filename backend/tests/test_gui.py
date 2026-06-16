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
    assert "Provisional Matches" in html
    for expected in [
        'id="layout-select"',
        'id="load-layout-button"',
        'id="base-diameter"',
        'id="board-canvas"',
        'id="source-status"',
        'id="footprint-evidence"',
        'id="footprint-match-evidence"',
        'id="visual-sanity-evidence"',
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


def test_client_script_wires_explicit_layout_load_button() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const loadLayoutButton" in script
    assert "loadLayoutButton.addEventListener" in script
    assert "loadSelectedLayout()" in script


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


def test_client_script_renders_footprint_match_evidence() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const footprintMatchEvidence" in script
    assert "function renderFootprintMatches" in script
    assert "/footprint-matches" in script
    assert "terrain-footprint-match-v1" in script
    assert "score=" in script


def test_client_script_renders_visual_sanity_evidence() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const visualSanityEvidence" in script
    assert "function renderVisualSanity" in script
    assert "/visual-sanity" in script
    assert "event-companion-cv-sanity-v1" in script
    assert "vision_advisory" in script


def test_client_script_keeps_visual_sanity_advisory_fetch_out_of_layout_load_barrier() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )
    load_layout_body = script.split("async function loadLayout(layoutId)", 1)[1].split(
        "async function initialize()", 1
    )[0]
    load_layout_barrier = load_layout_body.split("]);", 1)[0]

    assert "/visual-sanity" not in load_layout_barrier
    assert "async function loadVisualSanity(layoutId)" in script
    assert "void loadVisualSanity(layoutId);" in load_layout_body
    assert "renderError(visualSanityEvidence" in script


def test_client_script_distinguishes_terrain_categories_and_provisional_blockers() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "function terrainFill" in script
    assert "terrain_category" in script
    assert 'case "dense"' in script
    assert 'case "light"' in script
    assert "terrain_footprint_blocker_review_required" in script
    assert "function hasValidationCode" in script
    assert "context.setLineDash" in script


def test_client_script_avoids_inner_html_for_api_derived_data() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert ".innerHTML" not in script
