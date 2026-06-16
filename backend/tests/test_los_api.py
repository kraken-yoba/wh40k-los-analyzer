from fastapi.testclient import TestClient
from fortyk_los_backend.app import app


def test_point_los_api_returns_visibility_result() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/layouts/synthetic-alpha/los",
        json={
            "source": {"x": 2.0, "y": 20.0},
            "target": {"x": 42.0, "y": 20.0},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "blocking_blocker_ids": [],
        "method": "point-segment-v1",
        "sample_count": 1,
        "visible": True,
    }


def test_point_los_api_reports_blocking_wall() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/layouts/synthetic-alpha/los",
        json={
            "source": {"x": 2.0, "y": 4.0},
            "target": {"x": 42.0, "y": 4.0},
        },
    )

    assert response.status_code == 200
    assert response.json()["visible"] is False
    assert response.json()["blocking_blocker_ids"] == ["wall-a"]


def test_base_aware_los_api_accepts_base_diameters() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/layouts/synthetic-alpha/los",
        json={
            "source": {"x": 2.0, "y": 20.0},
            "target": {"x": 42.0, "y": 20.0},
            "source_base_diameter": 1.26,
            "target_base_diameter": 1.26,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["method"] == "disk-sample-v1"
    assert payload["sample_count"] == 289
    assert payload["boundary_sample_count"] == 16
    assert payload["visible"] is True


def test_los_api_rejects_invalid_base_sampling() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/layouts/synthetic-alpha/los",
        json={
            "source": {"x": 2.0, "y": 20.0},
            "target": {"x": 42.0, "y": 20.0},
            "source_base_diameter": 1.26,
            "target_base_diameter": 1.26,
            "boundary_sample_count": 7,
        },
    )

    assert response.status_code == 422


def test_los_api_rejects_non_finite_base_diameter_without_500() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/layouts/synthetic-alpha/los",
        content=(
            '{"source":{"x":2.0,"y":20.0},'
            '"target":{"x":42.0,"y":20.0},'
            '"source_base_diameter":Infinity,'
            '"target_base_diameter":1.26}'
        ),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422


def test_los_api_returns_404_for_unknown_layout() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/layouts/missing-layout/los",
        json={
            "source": {"x": 2.0, "y": 20.0},
            "target": {"x": 42.0, "y": 20.0},
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Layout not found: missing-layout"
