from __future__ import annotations

import json
from collections.abc import Mapping
from hashlib import sha256
from typing import Any

from pydantic import ValidationError

from warhammer_companion.domain.tts import (
    TTS_BRIDGE_RESPONSE_SCHEMA_VERSION,
    TtsBoardSnapshot,
    TtsBridgeError,
    TtsBridgeResponse,
)


class TtsBridgeService:
    def health(self) -> TtsBridgeResponse:
        return _success(
            {
                "response_schema_version": TTS_BRIDGE_RESPONSE_SCHEMA_VERSION,
                "host_only": True,
                "local_companion_required": True,
                "live_tts_round_trip_observed": False,
                "readiness": "contracts-only",
            }
        )

    def accept_snapshot(self, snapshot: TtsBoardSnapshot) -> TtsBridgeResponse:
        return _success(
            {
                "response_schema_version": TTS_BRIDGE_RESPONSE_SCHEMA_VERSION,
                "snapshot_schema_version": snapshot.schema_version,
                "input_hash": _snapshot_hash(snapshot),
                "object_counts": snapshot.object_counts(),
                "diagnostic_warning_labels": _diagnostic_warning_labels(snapshot),
                "host_only": snapshot.host_context.host_only,
                "local_companion_required": snapshot.host_context.local_companion_required,
                "live_tts_round_trip_observed": False,
                "readiness": "contracts-only",
            }
        )

    def accept_snapshot_payload(self, payload: object) -> TtsBridgeResponse:
        if not isinstance(payload, Mapping):
            return failure_response(
                "invalid-json-object",
                "Snapshot payload must be a JSON object.",
                (),
            )
        try:
            snapshot = TtsBoardSnapshot.model_validate(payload)
        except ValidationError as exc:
            return _validation_failure(exc)
        return self.accept_snapshot(snapshot)


def _success(data: dict[str, object]) -> TtsBridgeResponse:
    return TtsBridgeResponse(ok=True, data=data)


def failure_response(code: str, message: str, field_path: tuple[str, ...]) -> TtsBridgeResponse:
    return TtsBridgeResponse(
        ok=False,
        error=TtsBridgeError(
            code=code,
            message=message,
            field_path=field_path,
        ),
    )


def _validation_failure(exc: ValidationError) -> TtsBridgeResponse:
    return failure_response(
        "invalid-snapshot",
        "Snapshot payload failed validation.",
        _first_error_path(exc),
    )


def _first_error_path(exc: ValidationError) -> tuple[str, ...]:
    errors = exc.errors(include_input=False)
    if not errors:
        return ()
    location = errors[0].get("loc", ())
    if not isinstance(location, tuple):
        return ()
    return tuple(str(part) for part in location)


def _snapshot_hash(snapshot: TtsBoardSnapshot) -> str:
    payload: dict[str, Any] = snapshot.model_dump(mode="json")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


def _diagnostic_warning_labels(snapshot: TtsBoardSnapshot) -> list[str]:
    if snapshot.diagnostic_los is None:
        return []
    return ["diagnostic-physics-cast"]
