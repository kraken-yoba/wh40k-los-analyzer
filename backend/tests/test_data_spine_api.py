import json
from hashlib import sha256
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from fortyk_los_backend import app as app_module
from fortyk_los_backend.app import app
from fortyk_los_backend.domain import fixtures as fixtures_module
from fortyk_los_backend.domain.fixtures import FixtureRepository

SYNTHETIC_ALPHA_HASH = "7e7d811ab5a6db2ee9fa4ae0c19a66d78d7e7505b33b48b21486b2c970f0573a"


def test_layout_list_api_returns_synthetic_fixture() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts")

    assert response.status_code == 200
    payload = response.json()
    layouts_by_id = {layout["layout_id"]: layout for layout in payload["layouts"]}
    assert layouts_by_id["synthetic-alpha"] == {
        "layout_id": "synthetic-alpha",
        "name": "Synthetic Alpha",
        "layout_hash": SYNTHETIC_ALPHA_HASH,
        "source": "fixture",
    }


def test_layout_detail_api_returns_canonical_layout_and_hash() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/synthetic-alpha")

    assert response.status_code == 200
    payload = response.json()
    assert payload["layout_hash"] == SYNTHETIC_ALPHA_HASH
    assert payload["layout"]["board"] == {"height": 60.0, "unit": "inch", "width": 44.0}
    assert payload["layout"]["terrain_features"][0]["feature_id"] == "ruin-a"
    assert payload["layout"]["terrain_features"][0]["terrain_category"] == "dense"


def test_layout_detail_api_returns_404_for_unknown_layout() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/missing-layout")

    assert response.status_code == 404
    assert response.json()["detail"] == "Layout not found: missing-layout"


def test_source_manifest_api_returns_public_safe_documents() -> None:
    client = TestClient(app)

    response = client.get("/api/sources")

    assert response.status_code == 200
    payload = response.json()
    documents = {document["document_id"]: document for document in payload["documents"]}
    assert set(documents) == {
        "terrain-layouts-2026-06-12",
        "event-companion-2026-06-12",
        "core-rules-2026-06-01",
    }
    assert documents["terrain-layouts-2026-06-12"]["redistribution"] == "do-not-commit"
    assert documents["terrain-layouts-2026-06-12"]["cache_path"] == (
        "data/pdfs/terrainareafootprints.pdf"
    )
    assert documents["terrain-layouts-2026-06-12"]["cache_status"]["cache_path"] == (
        "data/pdfs/terrainareafootprints.pdf"
    )
    assert documents["terrain-layouts-2026-06-12"]["cache_status"]["status"] in {
        "missing",
        "hash_match",
    }
    assert documents["event-companion-2026-06-12"]["kind"] == "event_companion"
    assert documents["event-companion-2026-06-12"]["expected_sha256"] == (
        "0e26f6586929e7ec4c50c6a17d240ed794bb7b6c654d1d9664fb908abc606a19"
    )
    assert "assets.warhammer-community.com" in documents["core-rules-2026-06-01"]["url"]


def test_rules_terrain_semantics_api_returns_hash_backed_rules_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_rules_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.get("/api/rules/terrain-semantics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_document_id"] == "core-rules-2026-06-01"
    assert payload["cache_status"]["status"] == "hash_match"
    assert payload["extraction_method"] == "core-rules-terrain-semantics-v1"
    assert payload["backing_status"] == "backed"
    rules_by_code = {rule["code"]: rule for rule in payload["rules"]}
    assert set(rules_by_code) == {
        "visibility_line_of_sight",
        "terrain_categories",
        "dense_solid_blocks_2d_los",
        "light_exposed_not_opaque_blockers",
        "future_3d_rules_scope",
    }
    assert rules_by_code["dense_solid_blocks_2d_los"]["source_sections"] == [
        "Terrain and Visibility 13.07",
        "Solid 13.11",
    ]
    assert rules_by_code["dense_solid_blocks_2d_los"]["source_pages"] == [50]
    assert rules_by_code["dense_solid_blocks_2d_los"]["engine_implication"] == (
        "Matched Dense footprint fragments are the only official-layout wall candidates "
        "used by the current 2D LOS engine."
    )
    assert rules_by_code["light_exposed_not_opaque_blockers"]["engine_implication"] == (
        "Light and Exposed features remain visible terrain context and are not emitted as "
        "opaque LOS blocker segments."
    )


def test_rules_terrain_semantics_api_rejects_toc_only_anchor_matches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "data" / "pdfs" / "core_rules.pdf"
    pdf_path.parent.mkdir(parents=True)
    _write_toc_only_rules_pdf(pdf_path)
    _write_rules_manifest(
        tmp_path,
        expected_sha256=sha256(pdf_path.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.get("/api/rules/terrain-semantics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"]["status"] == "hash_match"
    assert payload["backing_status"] == "missing_anchor"
    assert payload["rules"] == []
    assert set(payload["missing_anchor_codes"]) == {
        "visibility_line_of_sight",
        "terrain_categories",
        "dense_solid_blocks_2d_los",
        "light_exposed_not_opaque_blockers",
        "future_3d_rules_scope",
    }


def test_rules_terrain_semantics_api_does_not_parse_missing_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_rules_manifest(tmp_path, expected_sha256="0" * 64)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    monkeypatch.setattr(fixtures_module, "extract_rules_terrain_semantics", _raise_if_called)
    client = TestClient(app)

    response = client.get("/api/rules/terrain-semantics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"]["status"] == "missing"
    assert payload["backing_status"] == "source_unavailable"
    assert payload["rules"] == []


def test_rules_terrain_semantics_api_does_not_parse_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "data" / "pdfs" / "core_rules.pdf"
    pdf_path.parent.mkdir(parents=True)
    _write_synthetic_rules_pdf(pdf_path)
    _write_rules_manifest(tmp_path, expected_sha256="0" * 64)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    monkeypatch.setattr(fixtures_module, "extract_rules_terrain_semantics", _raise_if_called)
    client = TestClient(app)

    response = client.get("/api/rules/terrain-semantics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"]["status"] == "hash_mismatch"
    assert payload["backing_status"] == "source_unavailable"
    assert payload["rules"] == []


def test_rules_terrain_semantics_api_rejects_multiple_rules_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_duplicate_rules_manifest(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    monkeypatch.setattr(fixtures_module, "extract_rules_terrain_semantics", _raise_if_called)
    client = TestClient(app)

    response = client.get("/api/rules/terrain-semantics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_document_id"] is None
    assert payload["cache_status"] is None
    assert payload["backing_status"] == "source_ambiguous"
    assert payload["rules"] == []


def test_layout_api_includes_extracted_event_companion_layout_when_cache_matches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_companion_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.get("/api/layouts")

    assert response.status_code == 200
    payload = response.json()
    extracted = [
        layout for layout in payload["layouts"] if layout["layout_id"] == "event-companion-page-1"
    ]
    assert extracted == [
        {
            "layout_id": "event-companion-page-1",
            "layout_hash": extracted[0]["layout_hash"],
            "name": "Layout A",
            "source": "extracted",
            "source_document_id": "event-companion-2026-06-12",
            "source_page": "1",
            "validation_status": "warning",
        }
    ]

    detail_response = client.get("/api/layouts/event-companion-page-1")

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["layout"]["provenance"]["extraction_method"] == (
        "event-companion-vector-v1"
    )


def test_los_api_runs_for_grid_snapped_extracted_event_companion_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_companion_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/api/layouts/event-companion-page-1/los",
        json={
            "source": {"x": 2.0, "y": 40.0},
            "target": {"x": 42.0, "y": 40.0},
        },
    )

    assert response.status_code == 200
    detail_response = client.get("/api/layouts/event-companion-page-1")
    record_codes = {
        record["code"] for record in detail_response.json()["layout"]["validation_records"]
    }
    assert "terrain_footprint_grid_snap_verified" in record_codes
    assert "placement_proxy_not_los_ready" not in record_codes


def test_extracted_layout_validation_warnings_are_auto_processed_without_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_and_terrain_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    detail_response = client.get("/api/layouts/event-companion-page-1")
    accepted_warning_codes = [
        record["code"]
        for record in detail_response.json()["layout"]["validation_records"]
        if record["severity"] == "warning" and record["review_status"] == "accepted"
    ]
    assert accepted_warning_codes

    ready_response = client.post(
        "/api/layouts/event-companion-page-1/los",
        json={
            "source": {"x": 2.0, "y": 40.0},
            "target": {"x": 42.0, "y": 40.0},
        },
    )

    assert ready_response.status_code == 200
    payload = ready_response.json()
    assert payload["validation_state"] == {
        "status": "accepted_with_warnings",
        "accepted_warning_codes": accepted_warning_codes,
        "unresolved_warning_codes": [],
    }


@pytest.mark.parametrize(
    ("endpoint", "payload"),
    [
        (
            "/api/layouts/event-companion-page-1/los",
            {
                "source": {"x": 2.0, "y": 40.0},
                "target": {"x": 42.0, "y": 40.0},
            },
        ),
        (
            "/api/layouts/event-companion-page-1/heatmap",
            {
                "source_region": {"x_min": 0, "y_min": 0, "x_max": 44, "y_max": 10},
                "source_step": 10,
                "target_grid": {"x_min": 2, "y_min": 4, "x_max": 42, "y_max": 24, "step": 10},
            },
        ),
        (
            "/api/layouts/event-companion-page-1/exposure",
            {
                "deployment_zone_id": "attacker",
                "movement_distance": 2,
                "threat_region": {"x_min": 42, "y_min": 20, "x_max": 42, "y_max": 20},
                "sample_step": 10,
            },
        ),
        (
            "/api/layouts/event-companion-page-1/terrain/terrain-01/coverage",
            {
                "source_region": {"x_min": 2, "y_min": 4, "x_max": 2, "y_max": 4},
                "target_grid": {"x_min": 42, "y_min": 4, "x_max": 42, "y_max": 4, "step": 1},
            },
        ),
    ],
)
def test_auto_reviewed_warning_state_allows_all_analysis_endpoints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    endpoint: str,
    payload: dict[str, object],
) -> None:
    _write_temp_event_and_terrain_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    detail_response = client.get("/api/layouts/event-companion-page-1")
    accepted_warning_codes = [
        record["code"]
        for record in detail_response.json()["layout"]["validation_records"]
        if record["severity"] == "warning" and record["review_status"] == "accepted"
    ]
    assert accepted_warning_codes

    response = client.post(endpoint, json=payload)

    assert response.status_code == 200
    assert response.json()["validation_state"]["status"] == "accepted_with_warnings"
    assert response.json()["validation_state"]["accepted_warning_codes"] == accepted_warning_codes
    assert response.json()["validation_state"]["unresolved_warning_codes"] == []


def test_accept_validation_warning_requires_current_layout_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_companion_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/api/layouts/event-companion-page-1/validation/placement_proxy_not_los_ready/accept",
        json={"layout_hash": "0" * 64},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["status"] == "layout_hash_mismatch"


def test_accept_validation_warning_rejects_missing_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_companion_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/api/layouts/event-companion-page-1/validation/placement_proxy_not_los_ready/accept",
        json={},
    )

    assert response.status_code == 422


def test_terrain_footprint_evidence_api_returns_hash_matched_outlines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_terrain_footprint_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.get("/api/extraction/terrain-footprints")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_document_id"] == "terrain-layouts-2026-06-12"
    assert payload["cache_status"]["status"] == "hash_match"
    assert payload["extraction_method"] == "terrain-footprint-vector-v1"
    assert payload["outlines"] == [
        {
            "bounds": [100.0, 100.0, 400.0, 420.0],
            "footprint_id": "terrain-footprint-p1-01",
            "page_number": 1,
            "path_command_count": 1,
            "point_count": 4,
        }
    ]


def test_terrain_footprint_evidence_api_does_not_parse_missing_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_terrain_footprint_manifest(tmp_path, expected_sha256="0" * 64)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    monkeypatch.setattr(fixtures_module, "extract_terrain_footprint_outlines", _raise_if_called)
    client = TestClient(app)

    response = client.get("/api/extraction/terrain-footprints")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"]["status"] == "missing"
    assert payload["outlines"] == []


def test_terrain_footprint_evidence_api_does_not_parse_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "data" / "pdfs" / "terrainareafootprints.pdf"
    pdf_path.parent.mkdir(parents=True)
    _write_synthetic_terrain_footprint_pdf(pdf_path)
    _write_terrain_footprint_manifest(tmp_path, expected_sha256="0" * 64)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    monkeypatch.setattr(fixtures_module, "extract_terrain_footprint_outlines", _raise_if_called)
    client = TestClient(app)

    response = client.get("/api/extraction/terrain-footprints")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"]["status"] == "hash_mismatch"
    assert payload["outlines"] == []


def test_footprint_match_evidence_api_returns_provisional_matches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_and_terrain_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.get("/api/layouts/event-companion-page-1/footprint-matches")

    assert response.status_code == 200
    payload = response.json()
    assert payload["layout_id"] == "event-companion-page-1"
    assert payload["cache_status"]["status"] == "hash_match"
    assert payload["extraction_method"] == "terrain-footprint-match-v1"
    assert [
        (match["feature_id"], match["template_id"], match["status"], match["review_reason"])
        for match in payload["matches"]
    ] == [
        ("terrain-01", "terrain-footprint-p1-01", "candidate", "best_aspect_match"),
    ]

    detail_response = client.get("/api/layouts/event-companion-page-1")
    assert detail_response.status_code == 200
    record_codes = {
        record["code"] for record in detail_response.json()["layout"]["validation_records"]
    }
    assert "terrain_footprint_match_candidates" in record_codes
    assert "terrain_footprint_match_review_required" in record_codes


def test_auto_reviewed_footprint_match_evidence_makes_extracted_layout_analysis_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_and_terrain_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    match_response = client.get("/api/layouts/event-companion-page-1/footprint-matches")
    los_response = client.post(
        "/api/layouts/event-companion-page-1/los",
        json={
            "source": {"x": 2.0, "y": 40.0},
            "target": {"x": 42.0, "y": 40.0},
        },
    )

    assert match_response.status_code == 200
    assert match_response.json()["matches"]
    assert los_response.status_code == 200
    assert "terrain_footprint_match_review_required" in los_response.json()["validation_state"][
        "accepted_warning_codes"
    ]
    assert los_response.json()["validation_state"]["unresolved_warning_codes"] == []


def test_footprint_match_evidence_api_does_not_parse_hash_mismatched_templates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_and_terrain_repo(tmp_path, terrain_sha256="0" * 64)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    monkeypatch.setattr(fixtures_module, "extract_terrain_footprint_templates", _raise_if_called)
    client = TestClient(app)

    response = client.get("/api/layouts/event-companion-page-1/footprint-matches")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"]["status"] == "hash_mismatch"
    assert payload["matches"] == []


def test_footprint_match_evidence_api_returns_404_for_missing_layout() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/missing-layout/footprint-matches")

    assert response.status_code == 404
    assert response.json()["detail"] == "Layout not found: missing-layout"


def test_visual_sanity_api_returns_deterministic_shape_alignment_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_companion_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.get("/api/layouts/event-companion-page-1/visual-sanity")

    assert response.status_code == 200
    payload = response.json()
    checks_by_code = {check["code"]: check for check in payload["checks"]}
    assert payload["layout_id"] == "event-companion-page-1"
    assert payload["status"] == "passed"
    assert payload["extraction_method"] == "event-companion-cv-sanity-v1"
    assert payload["vision_advisory"]["status"] == "not_run"
    assert checks_by_code["board_raster_alignment"]["status"] == "passed"
    assert checks_by_code["deployment_raster_alignment"]["match_count"] == 2
    assert checks_by_code["terrain_raster_alignment"]["match_count"] == 1


def test_visual_sanity_api_returns_404_for_missing_layout() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/missing-layout/visual-sanity")

    assert response.status_code == 404
    assert response.json()["detail"] == "Layout not found: missing-layout"


def test_footprint_normalization_api_returns_size_option_matches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_companion_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.get("/api/layouts/event-companion-page-1/footprint-normalization")

    assert response.status_code == 200
    payload = response.json()
    assert payload["layout_id"] == "event-companion-page-1"
    assert payload["source_document_id"] == "event-companion-2026-06-12"
    assert payload["cache_status"]["status"] == "hash_match"
    assert payload["source_page"] == 1
    assert payload["status"] == "passed"
    assert payload["extraction_method"] == "terrain-footprint-normalization-v1"
    assert payload["options"] == [
        {
            "count": 1,
            "feature_ids": ["terrain-01"],
            "height_inches": 10.0,
            "option_id": "footprint-size-10x10",
            "width_inches": 10.0,
        }
    ]
    assert payload["detected_elements"][0]["element_id"] == "terrain-image-01"
    assert payload["detected_elements"][0]["feature_id"] == "terrain-01"
    assert payload["matches"][0]["option_id"] == "footprint-size-10x10"
    assert payload["matches"][0]["feature_id"] == "terrain-01"
    assert payload["matches"][0]["status"] == "matched"


def test_footprint_normalization_api_returns_404_for_missing_layout() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/missing-layout/footprint-normalization")

    assert response.status_code == 404
    assert response.json()["detail"] == "Layout not found: missing-layout"


def test_terrain_symmetry_api_returns_advisory_report() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/synthetic-alpha/terrain-symmetry")

    assert response.status_code == 200
    payload = response.json()
    assert payload["layout_id"] == "synthetic-alpha"
    assert payload["extraction_method"] == "terrain-symmetry-v1"
    assert payload["symmetry_kind"] == "rotational_180"
    assert payload["feature_count"] == 2
    assert payload["matched_feature_count"] >= 0
    assert "max_residual_inches" in payload
    assert "matches" in payload


def test_terrain_symmetry_api_returns_404_for_missing_layout() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/missing-layout/terrain-symmetry")

    assert response.status_code == 404
    assert response.json()["detail"] == "Layout not found: missing-layout"


def test_terrain_reconciliation_api_returns_process_and_candidate_report() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/synthetic-alpha/terrain-reconciliation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["layout_id"] == "synthetic-alpha"
    assert payload["extraction_method"] == "terrain-reconciliation-v1"
    assert payload["process_steps"] == [
        "standard_terrain_options",
        "image_extraction",
        "grid_snap",
        "measurement_corner_check",
        "symmetry_candidate_check",
        "final_reconciliation",
    ]
    assert "standard_options" in payload
    assert "measurement_checks" in payload
    assert "alternatives" in payload
    assert payload["symmetry_status"] in {"passed", "warning"}


def test_terrain_reconciliation_api_returns_404_for_missing_layout() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/missing-layout/terrain-reconciliation")

    assert response.status_code == 404
    assert response.json()["detail"] == "Layout not found: missing-layout"


def test_source_underlay_api_returns_board_cropped_png_for_extracted_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_temp_event_companion_repo(tmp_path)
    monkeypatch.setattr(app_module, "fixtures", FixtureRepository(tmp_path))
    client = TestClient(app)

    response = client.get("/api/layouts/event-companion-page-1/source-underlay.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
    image = fitz.Pixmap(response.content)
    assert image.width == 880
    assert image.height == 1200


def test_source_underlay_api_returns_404_for_fixture_layout() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/synthetic-alpha/source-underlay.png")

    assert response.status_code == 404
    assert response.json()["detail"] == "Source underlay not available: synthetic-alpha"


def _write_temp_event_companion_repo(repo_root: Path) -> None:
    pdf_path = repo_root / "data" / "pdfs" / "event_companion.pdf"
    pdf_path.parent.mkdir(parents=True)
    _write_synthetic_event_layout_pdf(pdf_path)
    manifest_path = repo_root / "fixtures" / "source_manifest.official.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "cache_path": "data/pdfs/event_companion.pdf",
                        "document_id": "event-companion-2026-06-12",
                        "expected_sha256": sha256(pdf_path.read_bytes()).hexdigest(),
                        "kind": "event_companion",
                        "redistribution": "do-not-commit",
                        "url": "https://assets.warhammer-community.com/example-event.pdf",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_temp_event_and_terrain_repo(
    repo_root: Path,
    *,
    terrain_sha256: str | None = None,
) -> None:
    event_pdf_path = repo_root / "data" / "pdfs" / "event_companion.pdf"
    terrain_pdf_path = repo_root / "data" / "pdfs" / "terrainareafootprints.pdf"
    event_pdf_path.parent.mkdir(parents=True)
    _write_synthetic_event_layout_pdf(event_pdf_path)
    _write_synthetic_terrain_footprint_pdf(terrain_pdf_path)
    manifest_path = repo_root / "fixtures" / "source_manifest.official.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "cache_path": "data/pdfs/event_companion.pdf",
                        "document_id": "event-companion-2026-06-12",
                        "expected_sha256": sha256(event_pdf_path.read_bytes()).hexdigest(),
                        "kind": "event_companion",
                        "redistribution": "do-not-commit",
                        "url": "https://assets.warhammer-community.com/example-event.pdf",
                    },
                    {
                        "cache_path": "data/pdfs/terrainareafootprints.pdf",
                        "document_id": "terrain-layouts-2026-06-12",
                        "expected_sha256": terrain_sha256
                        or sha256(terrain_pdf_path.read_bytes()).hexdigest(),
                        "kind": "terrain_layouts",
                        "redistribution": "do-not-commit",
                        "url": "https://assets.warhammer-community.com/example-terrain.pdf",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_synthetic_event_layout_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=500, height=700)
    board = fitz.Rect(100, 100, 320, 400)
    page.insert_text((220, 80), "LAYOUT A")
    page.draw_rect(board, color=(0.137, 0.122, 0.125), width=2.4)
    page.draw_rect(fitz.Rect(100, 100, 320, 200), color=None, fill=(0.618, 0.040, 0.056))
    page.draw_rect(fitz.Rect(100, 300, 320, 400), color=None, fill=(0.000, 0.241, 0.408))
    page.draw_rect(
        fitz.Rect(140, 160, 190, 210),
        color=(0.137, 0.122, 0.125),
        fill=(0.820, 0.826, 0.832),
        width=0.3,
    )
    page.draw_rect(
        fitz.Rect(150, 190, 162, 202),
        color=(1.0, 1.0, 1.0),
        fill=(0.000, 0.452, 0.378),
        width=0.2,
    )
    page.insert_text((158, 185), "AB")
    document.save(pdf_path)


def _write_temp_terrain_footprint_repo(repo_root: Path) -> None:
    pdf_path = repo_root / "data" / "pdfs" / "terrainareafootprints.pdf"
    pdf_path.parent.mkdir(parents=True)
    _write_synthetic_terrain_footprint_pdf(pdf_path)
    _write_terrain_footprint_manifest(
        repo_root,
        expected_sha256=sha256(pdf_path.read_bytes()).hexdigest(),
    )


def _write_temp_rules_repo(repo_root: Path) -> None:
    pdf_path = repo_root / "data" / "pdfs" / "core_rules.pdf"
    pdf_path.parent.mkdir(parents=True)
    _write_synthetic_rules_pdf(pdf_path)
    _write_rules_manifest(
        repo_root,
        expected_sha256=sha256(pdf_path.read_bytes()).hexdigest(),
    )


def _write_rules_manifest(repo_root: Path, *, expected_sha256: str) -> None:
    manifest_path = repo_root / "fixtures" / "source_manifest.official.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "cache_path": "data/pdfs/core_rules.pdf",
                        "document_id": "core-rules-2026-06-01",
                        "expected_sha256": expected_sha256,
                        "kind": "rules",
                        "redistribution": "do-not-commit",
                        "url": "https://assets.warhammer-community.com/example-rules.pdf",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_duplicate_rules_manifest(repo_root: Path) -> None:
    manifest_path = repo_root / "fixtures" / "source_manifest.official.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "cache_path": "data/pdfs/core_rules.pdf",
                        "document_id": "core-rules-2026-06-01",
                        "expected_sha256": "0" * 64,
                        "kind": "rules",
                        "redistribution": "do-not-commit",
                        "url": "https://assets.warhammer-community.com/example-rules.pdf",
                    },
                    {
                        "cache_path": "data/pdfs/core_rules_updated.pdf",
                        "document_id": "core-rules-2026-06-02",
                        "expected_sha256": "1" * 64,
                        "kind": "rules",
                        "redistribution": "do-not-commit",
                        "url": "https://assets.warhammer-community.com/example-rules-2.pdf",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_terrain_footprint_manifest(repo_root: Path, *, expected_sha256: str) -> None:
    manifest_path = repo_root / "fixtures" / "source_manifest.official.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "cache_path": "data/pdfs/terrainareafootprints.pdf",
                        "document_id": "terrain-layouts-2026-06-12",
                        "expected_sha256": expected_sha256,
                        "kind": "terrain_layouts",
                        "redistribution": "do-not-commit",
                        "url": "https://assets.warhammer-community.com/example-terrain.pdf",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _raise_if_called(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("extract_terrain_footprint_outlines should not be called")


def _write_synthetic_terrain_footprint_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=500, height=500)
    shape = page.new_shape()
    shape.draw_polyline(
        [
            fitz.Point(100, 100),
            fitz.Point(400, 100),
            fitz.Point(400, 420),
            fitz.Point(100, 420),
            fitz.Point(100, 100),
        ]
    )
    shape.finish(color=(0.0, 0.66, 0.31), width=2.0)
    shape.commit()
    page.draw_line(
        fitz.Point(20, 20),
        fitz.Point(35, 20),
        color=(0.0, 0.66, 0.31),
        width=2.0,
    )
    document.save(pdf_path)


def _write_synthetic_rules_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    for page_number in range(1, 51):
        page = document.new_page(width=500, height=700)
        if page_number == 24:
            page.insert_text((72, 72), "VISIBILITY 06.01")
            page.insert_text(
                (72, 96),
                "Line of sight fixture anchor.",
            )
            page.insert_text((72, 120), "observing model fixture anchor.")
        if page_number == 46:
            page.insert_text((72, 72), "TERRAIN CATEGORIES 13.02")
            page.insert_text((72, 96), "EXPOSED 13.03")
            page.insert_text((72, 120), "LIGHT 13.04")
            page.insert_text((72, 144), "DENSE 13.05")
            page.insert_text((72, 168), "movement and visibility fixture anchor.")
        if page_number == 48:
            page.insert_text((72, 72), "TERRAIN AND MOVEMENT 13.06")
            page.insert_text((72, 96), "Exposed/Light")
            page.insert_text((72, 120), "vertically fixture anchor.")
        if page_number == 50:
            page.insert_text((72, 72), "TERRAIN AND VISIBILITY 13.07")
            page.insert_text((72, 84), "Terrain can affect visibility")
            page.insert_text((72, 90), "depending on whether fixture anchor.")
            page.insert_text((72, 96), "OBSCURING 13.10")
            page.insert_text((72, 120), "SOLID 13.11")
            page.insert_text((72, 144), "Dense terrain features fixture anchor.")
            page.insert_text((72, 168), "ground level fixture anchor.")
    document.save(pdf_path)


def _write_toc_only_rules_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=500, height=700)
    for index, label in enumerate(
        [
            "VISIBILITY 06.01",
            "Line of sight",
            "TERRAIN CATEGORIES 13.02",
            "EXPOSED 13.03",
            "LIGHT 13.04",
            "DENSE 13.05",
            "TERRAIN AND MOVEMENT 13.06",
            "Exposed/Light",
            "TERRAIN AND VISIBILITY 13.07",
            "Terrain can affect visibility",
            "OBSCURING 13.10",
            "SOLID 13.11",
            "Dense terrain features",
        ]
    ):
        page.insert_text((72, 72 + index * 20), label)
    document.save(pdf_path)
