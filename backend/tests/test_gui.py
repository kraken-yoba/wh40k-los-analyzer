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
        'id="interaction-mode"',
        'id="base-diameter"',
        'id="source-underlay-toggle"',
        'id="source-underlay-status"',
        'id="board-canvas"',
        'id="source-status"',
        'id="rules-evidence"',
        'id="footprint-evidence"',
        'id="footprint-match-evidence"',
        'id="visual-sanity-evidence"',
        'id="terrain-semantics"',
        'id="feature-provenance"',
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


def test_client_script_renders_automatic_validation_review_state() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "review_status" in script
    assert "accepted_with_warnings" in script
    assert "Accept warning" not in script


def test_client_script_does_not_wire_manual_warning_acceptance_flow() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "function acceptValidationWarning" not in script
    assert "/validation/" not in script
    assert "/accept" not in script


def test_client_script_renders_terrain_footprint_evidence() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const footprintEvidence" in script
    assert "function renderFootprintEvidence" in script
    assert "/api/extraction/terrain-footprints" in script
    assert "terrain-footprint-vector-v1" in script


def test_client_script_renders_rules_terrain_semantics_evidence() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const rulesEvidence" in script
    assert "function renderRulesEvidence" in script
    assert "/api/rules/terrain-semantics" in script
    assert "core-rules-terrain-semantics-v1" in script
    assert "Dense/Solid" in script
    assert "Light/Exposed" in script
    assert "future 3D-aware LOS" in script


def test_client_script_keeps_rules_fetch_out_of_layout_load_barrier() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )
    initialize_body = script.split("async function initialize()", 1)[1].split(
        "function formatLayoutOption",
        1,
    )[0]
    initialize_barrier = initialize_body.split("]);", 1)[0]

    assert "/api/rules/terrain-semantics" not in initialize_barrier
    assert "async function loadRulesEvidence()" in script
    assert "void loadRulesEvidence();" in initialize_body
    assert "renderError(rulesEvidence" in script


def test_client_script_includes_source_page_in_extracted_layout_options() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )
    format_body = script.split("function formatLayoutOption(layout)", 1)[1].split(
        'canvas.addEventListener("click"',
        1,
    )[0]

    assert "layout.source_page" in format_body
    assert "p${layout.source_page}" in format_body


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


def test_client_script_renders_source_underlay_beneath_overlays() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const sourceUnderlayToggle" in script
    assert "const sourceUnderlayStatus" in script
    assert "sourceUnderlayImage" in script
    assert "async function loadSourceUnderlay" in script
    assert "/source-underlay.png" in script
    assert "context.drawImage(state.sourceUnderlayImage" in script
    assert "sourceUnderlayToggle.addEventListener" in script


def test_client_script_ignores_stale_source_underlay_responses() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )
    helper_body = script.split("function isCurrentSourceUnderlayRequest", 1)[1].split(
        "async function loadSourceUnderlay",
        1,
    )[0]
    load_body = script.split("async function loadSourceUnderlay(layoutId)", 1)[1].split(
        "function renderValidation()",
        1,
    )[0]

    assert "state.layout.layout_id === layoutId" in helper_body
    stale_guard = "isCurrentSourceUnderlayRequest(layoutId, sourceUnderlayRequestId)"
    assert load_body.count(stale_guard) >= 3
    assert load_body.index(stale_guard) < load_body.index("state.sourceUnderlayImage = image")


def test_client_script_ignores_disabled_source_underlay_responses() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )
    load_body = script.split("async function loadSourceUnderlay(layoutId)", 1)[1].split(
        "function renderValidation()",
        1,
    )[0]

    assert "sourceUnderlayRequestId" in script
    assert "state.sourceUnderlayRequestId += 1" in load_body
    current_guard = "isCurrentSourceUnderlayRequest(layoutId, sourceUnderlayRequestId)"
    assert load_body.count(current_guard) >= 3
    assert "sourceUnderlayToggle.checked" in script
    assert load_body.index(current_guard) < load_body.index("state.sourceUnderlayImage = image")


def test_client_script_renders_feature_provenance_from_inspect_clicks() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const interactionMode" in script
    assert "const featureProvenance" in script
    assert "selectedFeatureId" in script
    assert "function pointInPolygon" in script
    assert "function featureAtPoint" in script
    assert "function renderFeatureProvenance" in script
    assert "terrain_category" in script
    assert "blocker count" in script
    assert "Layout warnings" in script
    assert 'interactionMode.value === "inspect"' in script


def test_client_script_renders_dense_only_terrain_semantics() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const terrainSemantics" in script
    assert "function terrainCategoryCounts" in script
    assert "function renderTerrainSemantics" in script
    assert "Dense" in script
    assert "Light" in script
    assert "Exposed" in script
    assert "Unknown" in script
    assert "Dense wall candidates" in script
    assert 'feature.terrain_category === "dense"' in script
    assert "renderTerrainSemantics()" in script


def test_client_script_refreshes_selected_feature_on_layout_load() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "function selectedFeature()" in script
    assert "function renderSelectedFeatureProvenance()" in script


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


def test_client_script_distinguishes_terrain_categories_and_solid_dense_walls() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "function terrainFill" in script
    assert "terrain_category" in script
    assert 'case "dense"' in script
    assert 'case "light"' in script
    assert "provisionalBlockers" not in script
    assert "terrain_footprint_blocker_review_required" not in script
    assert "context.setLineDash(provisionalBlockers" not in script


def test_client_script_avoids_inner_html_for_api_derived_data() -> None:
    script = (REPO_ROOT / "backend" / "fortyk_los_backend" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    assert ".innerHTML" not in script
