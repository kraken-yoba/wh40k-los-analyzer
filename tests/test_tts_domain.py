from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from warhammer_companion.domain.tts import (
    TTS_BOARD_SNAPSHOT_SCHEMA_VERSION,
    TtsBoardSnapshot,
    TtsDiagnosticLosProbe,
    TtsObjectRef,
    TtsVector3,
)

FIXTURE_PATH = Path("tests/fixtures/tts/minimal_snapshot.json")


def test_minimal_tts_snapshot_fixture_is_schema_valid() -> None:
    snapshot = TtsBoardSnapshot.model_validate_json(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert snapshot.schema_version == TTS_BOARD_SNAPSHOT_SCHEMA_VERSION
    assert snapshot.snapshot_id == "synthetic-phase-1-minimal"
    assert snapshot.host_context.local_companion_required
    assert snapshot.host_context.live_tts_round_trip_observed is False
    assert snapshot.object_counts() == {"attacker": 1, "target": 1, "terrain": 1}


def test_tts_snapshot_transform_round_trips_calibration_points_within_tolerance() -> None:
    snapshot = TtsBoardSnapshot.model_validate_json(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert snapshot.transform.max_round_trip_error_inches() <= 0.25
    upper_right = snapshot.transform.world_to_battlefield(TtsVector3(x=44.0, y=0.0, z=60.0))

    assert upper_right.as_tuple() == (44.0, 60.0)


def test_tts_object_kind_is_constrained() -> None:
    payload = {
        "guid": "badkind",
        "name": "Synthetic invalid role",
        "object_kind": "deployment-zone",
        "tags": ["tts-attacker"],
        "position": {"x": 1.0, "y": 0.0, "z": 1.0},
        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
        "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
        "provenance": "tagged",
    }

    with pytest.raises(ValidationError):
        TtsObjectRef.model_validate(payload)


def test_tts_snapshot_requires_attacker_target_and_terrain() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["objects"] = [obj for obj in payload["objects"] if obj["object_kind"] != "target"]

    with pytest.raises(ValidationError, match="attacker, target, and terrain"):
        TtsBoardSnapshot.model_validate(payload)


def test_diagnostic_los_probe_cannot_be_authoritative() -> None:
    payload = {
        "schema_version": "tts-diagnostic-los-probe/v0",
        "probe_id": "bad-authority",
        "source_guid": "attacker1",
        "target_guid": "target1",
        "start_world": {"x": 8.0, "y": 1.0, "z": 10.0},
        "end_world": {"x": 30.0, "y": 1.0, "z": 42.0},
        "hit": False,
        "hit_guid": None,
        "authoritative": True,
        "label": "Diagnostic physics cast",
    }

    with pytest.raises(ValidationError, match="diagnostic"):
        TtsDiagnosticLosProbe.model_validate(payload)
