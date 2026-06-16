from fastapi.testclient import TestClient
from fortyk_los_backend.app import app


def test_index_serves_local_gui_shell() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Warhammer 40k LOS Analyzer" in response.text
    assert "Infrastructure ready" in response.text
    assert "/static/app.js" in response.text
