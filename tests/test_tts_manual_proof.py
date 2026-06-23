from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from typer.testing import CliRunner

from warhammer_companion.application.tts_live_proof import run_tts_manual_health_proof
from warhammer_companion.cli import cli


def test_tts_manual_health_proof_accepts_exact_global_lua_receipt() -> None:
    scripts: list[str] = []

    def call_rendered_receipt(_base_url: str, _receipt: str, script: str) -> None:
        scripts.append(script)
        request = _build_tts_proof_request(script)
        with urllib.request.urlopen(request, timeout=2) as response:
            assert response.status == 200

    result = run_tts_manual_health_proof(
        project_root=Path.cwd(),
        receipt="manual-proof-1",
        timeout_seconds=2,
        on_server_ready=call_rendered_receipt,
    )

    assert result.proof_server_owned_listener is True
    assert result.companion_receipt_observed is True
    assert result.live_tts_round_trip_observed is True
    assert result.source == "TTS Global Lua WebRequest.custom"
    assert result.blocker is None
    assert result.receipt_endpoint_path == "/api/tts/health"
    assert result.receipt_status_code == 200
    assert "manual-proof-1" in scripts[0]
    assert "WebRequest.custom" in scripts[0]
    assert "Save & Play" not in scripts[0]


def test_tts_manual_health_proof_times_out_without_receipt() -> None:
    scripts: list[str] = []

    result = run_tts_manual_health_proof(
        project_root=Path.cwd(),
        receipt="manual-proof-2",
        timeout_seconds=0.01,
        on_server_ready=lambda _base_url, _receipt, script: scripts.append(script),
    )

    assert result.proof_server_owned_listener is True
    assert result.companion_receipt_observed is False
    assert result.live_tts_round_trip_observed is False
    assert result.source == "TTS Global Lua WebRequest.custom"
    assert result.blocker == "companion-receipt-not-observed"
    assert "manual-proof-2" in scripts[0]


def test_tts_manual_health_proof_rejects_plain_url_hit_without_proof_header() -> None:
    def call_without_header(_base_url: str, _receipt: str, script: str) -> None:
        url = _rendered_health_url_from_lua(script)
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(url, timeout=2)
        assert exc_info.value.code == 404

    result = run_tts_manual_health_proof(
        project_root=Path.cwd(),
        receipt="manual-proof-3",
        timeout_seconds=0.01,
        on_server_ready=call_without_header,
    )

    assert result.companion_receipt_observed is False
    assert result.live_tts_round_trip_observed is False
    assert result.blocker == "companion-receipt-not-observed"


def test_tts_manual_health_proof_rejects_wrong_receipt() -> None:
    def call_wrong_receipt(base_url: str, _receipt: str, script: str) -> None:
        request = urllib.request.Request(
            f"{base_url}/api/tts/health?receipt=wrong-receipt",
            headers={"X-Warhammer-TTS-Proof": _lua_string_assignment(script, "RECEIPT")},
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(request, timeout=2)
        assert exc_info.value.code == 404

    result = run_tts_manual_health_proof(
        project_root=Path.cwd(),
        receipt="manual-proof-4",
        timeout_seconds=0.01,
        on_server_ready=call_wrong_receipt,
    )

    assert result.companion_receipt_observed is False
    assert result.live_tts_round_trip_observed is False
    assert result.blocker == "companion-receipt-not-observed"


def test_tts_manual_health_cli_prints_reviewed_snippet_and_sanitized_result() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "tts-manual-health",
            "--receipt",
            "manual-cli-1",
            "--wait-seconds",
            "0",
        ],
    )

    assert result.exit_code == 1
    assert "Paste this reviewed Lua into TTS Global Lua and run it:" in result.output
    assert "manual-cli-1" in result.output
    assert "WebRequest.custom" in result.output
    assert "C:" not in result.output

    output = json.loads(result.output.strip().splitlines()[-1])
    assert output["live_tts_round_trip_observed"] is False
    assert output["source"] == "TTS Global Lua WebRequest.custom"
    assert output["blocker"] == "companion-receipt-not-observed"


def _build_tts_proof_request(script: str) -> urllib.request.Request:
    receipt = _lua_string_assignment(script, "RECEIPT")
    return urllib.request.Request(
        _rendered_health_url_from_lua(script),
        headers={"X-Warhammer-TTS-Proof": receipt},
    )


def _rendered_health_url_from_lua(script: str) -> str:
    base_url = _lua_string_assignment(script, "COMPANION_BASE_URL")
    receipt = _lua_string_assignment(script, "RECEIPT")
    return f"{base_url}/api/tts/health?receipt={receipt}"


def _lua_string_assignment(script: str, name: str) -> str:
    marker = f'local {name} = "'
    start = script.index(marker) + len(marker)
    end = script.index('"', start)
    return script[start:end]
