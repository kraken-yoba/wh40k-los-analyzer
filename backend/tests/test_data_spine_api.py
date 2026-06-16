from fastapi.testclient import TestClient
from fortyk_los_backend.app import app

SYNTHETIC_ALPHA_HASH = "91092527a7961fac123f3fbfdf0bc7ba70ea056b17b640323ddea16b78ec18cb"


def test_layout_list_api_returns_synthetic_fixture() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts")

    assert response.status_code == 200
    payload = response.json()
    assert payload["layouts"] == [
        {
            "layout_id": "synthetic-alpha",
            "name": "Synthetic Alpha",
            "layout_hash": SYNTHETIC_ALPHA_HASH,
        }
    ]


def test_layout_detail_api_returns_canonical_layout_and_hash() -> None:
    client = TestClient(app)

    response = client.get("/api/layouts/synthetic-alpha")

    assert response.status_code == 200
    payload = response.json()
    assert payload["layout_hash"] == SYNTHETIC_ALPHA_HASH
    assert payload["layout"]["board"] == {"height": 60.0, "unit": "inch", "width": 44.0}
    assert payload["layout"]["terrain_features"][0]["feature_id"] == "ruin-a"


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
    assert "assets.warhammer-community.com" in documents["core-rules-2026-06-01"]["url"]
