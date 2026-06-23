from __future__ import annotations

import json
from pathlib import Path

from warhammer_companion.application.tts_bridge import TtsBridgeService
from warhammer_companion.domain.tts import TtsBoardSnapshot

FIXTURE_PATH = Path("tests/fixtures/tts/minimal_snapshot.json")


def test_tts_bridge_health_reports_host_only_contracts_baseline() -> None:
    response = TtsBridgeService().health()

    assert response.ok
    assert response.error is None
    assert response.data["host_only"] is True
    assert response.data["local_companion_required"] is True
    assert response.data["live_tts_round_trip_observed"] is False
    assert response.data["readiness"] == "contracts-only"


def test_tts_bridge_accepts_snapshot_without_echoing_payload_body() -> None:
    snapshot = TtsBoardSnapshot.model_validate_json(FIXTURE_PATH.read_text(encoding="utf-8"))
    service = TtsBridgeService()

    first = service.accept_snapshot(snapshot)
    second = service.accept_snapshot(snapshot)

    assert first.ok
    assert first.error is None
    assert first.data == second.data
    assert first.data["input_hash"] == second.data["input_hash"]
    assert first.data["object_counts"] == {"attacker": 1, "target": 1, "terrain": 1}
    assert first.data["diagnostic_warning_labels"] == ["diagnostic-physics-cast"]
    assert "objects" not in first.data
    assert "diagnostic_los" not in first.data
    assert "snapshot" not in first.data


def test_tts_bridge_does_not_trust_payload_claimed_live_round_trip() -> None:
    snapshot = TtsBoardSnapshot.model_validate_json(FIXTURE_PATH.read_text(encoding="utf-8"))
    claimed_live_snapshot = snapshot.model_copy(
        update={
            "host_context": snapshot.host_context.model_copy(
                update={"live_tts_round_trip_observed": True}
            )
        }
    )

    response = TtsBridgeService().accept_snapshot(claimed_live_snapshot)

    assert response.ok
    assert response.data["live_tts_round_trip_observed"] is False
    assert response.data["readiness"] == "contracts-only"


def test_tts_bridge_rejects_invalid_payload_with_sanitized_error() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["objects"][0]["name"] = "C:/Users/example/Saved Objects/bad.tts sk-test"
    payload["objects"][0]["object_kind"] = "bad-kind"

    response = TtsBridgeService().accept_snapshot_payload(payload)
    serialized = json.dumps(response.model_dump(mode="json"))

    assert not response.ok
    assert response.error is not None
    assert response.error.code == "invalid-snapshot"
    assert response.error.field_path == ("objects", "0", "object_kind")
    assert "Saved Objects" not in serialized
    assert ".tts" not in serialized
    assert "sk-test" not in serialized
    assert "bad-kind" not in serialized
