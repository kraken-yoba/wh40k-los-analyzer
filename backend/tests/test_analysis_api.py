from fastapi.testclient import TestClient
from fortyk_los_backend.app import app


def test_heatmap_api_returns_firing_lane_cells() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/layouts/synthetic-alpha/heatmap",
        json={
            "source_region": {"x_min": 2.0, "y_min": 20.0, "x_max": 42.0, "y_max": 20.0},
            "target_grid": {
                "x_min": 2.0,
                "y_min": 20.0,
                "x_max": 42.0,
                "y_max": 20.0,
                "step": 20.0,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_sample_count"] == 2
    assert len(payload["cells"]) == 3
    assert payload["max_visible_source_count"] >= 1


def test_exposure_api_returns_reachable_and_exposed_counts() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/layouts/synthetic-alpha/exposure",
        json={
            "deployment_zone_id": "attacker",
            "movement_distance": 2.0,
            "threat_region": {"x_min": 42.0, "y_min": 20.0, "x_max": 42.0, "y_max": 20.0},
            "sample_step": 10.0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reachable_sample_count"] > 0
    assert 0.0 <= payload["exposed_fraction"] <= 1.0


def test_terrain_coverage_api_returns_feature_delta() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/layouts/synthetic-alpha/terrain/ruin-a/coverage",
        json={
            "source_region": {"x_min": 2.0, "y_min": 4.0, "x_max": 2.0, "y_max": 4.0},
            "target_grid": {"x_min": 42.0, "y_min": 4.0, "x_max": 42.0, "y_max": 4.0, "step": 1.0},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["feature_id"] == "ruin-a"
    assert payload["coverage_delta"] >= 1
