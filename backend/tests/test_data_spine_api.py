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


def test_los_api_blocks_unreviewed_extracted_event_companion_layout(
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

    assert response.status_code == 409
    assert response.json()["detail"]["status"] == "blocked"
    assert "placement_proxy_not_los_ready" in response.json()["detail"]["record_codes"]


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


def test_footprint_match_evidence_does_not_make_extracted_layout_analysis_ready(
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
    assert los_response.status_code == 409
    assert "terrain_footprint_match_review_required" in los_response.json()["detail"][
        "record_codes"
    ]


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
