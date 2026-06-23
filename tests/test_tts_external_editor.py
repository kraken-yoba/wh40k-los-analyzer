from __future__ import annotations

import json
import socket
import subprocess
import threading
import urllib.request
from pathlib import Path

import pytest
from typer.testing import CliRunner

from warhammer_companion.application import tts_live_proof
from warhammer_companion.application.tts_external_editor import (
    TtsExternalEditorClient,
    build_execute_lua_message,
    render_lua_probe_template,
    resolve_reviewed_lua_template,
)
from warhammer_companion.application.tts_live_proof import (
    TtsExternalEditorProcessCheck,
    run_tts_health_proof,
    verify_tts_external_editor_process,
)
from warhammer_companion.cli import cli


def test_execute_lua_message_targets_global_script() -> None:
    message = build_execute_lua_message('print("hello")')

    assert json.loads(message.decode("utf-8")) == {
        "messageID": 3,
        "guid": "-1",
        "script": 'print("hello")',
    }


def test_render_lua_probe_template_replaces_reviewed_placeholders(tmp_path: Path) -> None:
    template_path = tmp_path / "probe.lua"
    template_path.write_text(
        'local url = "__COMPANION_BASE_URL__/api/tts/health?receipt=__RECEIPT__"',
        encoding="utf-8",
    )

    script = render_lua_probe_template(
        template_path,
        companion_base_url="http://127.0.0.1:8000",
        receipt="phase1-123",
    )

    assert "__RECEIPT__" not in script
    assert "__COMPANION_BASE_URL__" not in script
    assert "http://127.0.0.1:8000/api/tts/health?receipt=phase1-123" in script


@pytest.mark.parametrize(
    "base_url",
    [
        'http://127.0.0.1:8000/bad"path',
        "http://user:pass@127.0.0.1:8000",
        "http://127.0.0.1:8000/path",
        "https://127.0.0.1:8000",
        "http://192.0.2.10:8000",
    ],
)
def test_render_lua_probe_template_rejects_unsafe_base_urls(
    tmp_path: Path,
    base_url: str,
) -> None:
    template_path = tmp_path / "probe.lua"
    template_path.write_text('print("__COMPANION_BASE_URL__")', encoding="utf-8")

    with pytest.raises(ValueError, match="Companion base URL"):
        render_lua_probe_template(
            template_path,
            companion_base_url=base_url,
            receipt="phase1-123",
        )


def test_render_lua_probe_template_rejects_unsafe_receipt(tmp_path: Path) -> None:
    template_path = tmp_path / "probe.lua"
    template_path.write_text('print("__RECEIPT__")', encoding="utf-8")

    with pytest.raises(ValueError, match="receipt"):
        render_lua_probe_template(
            template_path,
            companion_base_url="http://127.0.0.1:8000",
            receipt='bad"; os.execute("x")',
        )


def test_external_editor_client_rejects_non_loopback_host() -> None:
    with pytest.raises(ValueError, match="TTS External Editor host"):
        TtsExternalEditorClient(host="192.0.2.10")


def test_resolve_reviewed_lua_template_rejects_arbitrary_script(tmp_path: Path) -> None:
    script_path = tmp_path / "external_editor_health_receipt.lua"
    script_path.write_text("print('not repo reviewed')", encoding="utf-8")

    with pytest.raises(ValueError, match="reviewed TTS Lua template"):
        resolve_reviewed_lua_template(script_path, project_root=Path.cwd())


def test_external_editor_client_sends_execute_lua_to_local_tts_socket() -> None:
    captured: list[bytes] = []
    ready = threading.Event()

    def run_server() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            host, port = server.getsockname()
            captured.append(f"{host}:{port}".encode("ascii"))
            ready.set()
            connection, _ = server.accept()
            with connection:
                chunks: list[bytes] = []
                while True:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                captured.append(b"".join(chunks))

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    assert ready.wait(timeout=2)
    host, raw_port = captured[0].decode("ascii").split(":")

    TtsExternalEditorClient(host=host, port=int(raw_port), timeout_seconds=2).execute_lua(
        'print("probe")'
    )
    thread.join(timeout=2)

    sent = json.loads(captured[1].decode("utf-8"))
    assert sent == {"messageID": 3, "guid": "-1", "script": 'print("probe")'}


def test_tts_execute_lua_cli_sends_reviewed_probe_template(tmp_path: Path) -> None:
    captured: list[bytes] = []
    ready = threading.Event()

    def run_server() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            host, port = server.getsockname()
            captured.append(f"{host}:{port}".encode("ascii"))
            ready.set()
            connection, _ = server.accept()
            with connection:
                captured.append(connection.recv(4096))

    project_root = Path.cwd()
    template_path = project_root / "docs" / "tts" / "external_editor_health_receipt.lua"
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    assert ready.wait(timeout=2)
    host, raw_port = captured[0].decode("ascii").split(":")

    result = CliRunner().invoke(
        cli,
        [
            "tts-execute-lua",
            "--script-file",
            str(template_path),
            "--receipt",
            "cli-proof-1",
            "--companion-base-url",
            "http://127.0.0.1:8000",
            "--host",
            host,
            "--port",
            raw_port,
        ],
    )
    thread.join(timeout=2)

    assert result.exit_code == 0
    assert "Sent TTS External Editor Execute Lua message" in result.output
    sent = json.loads(captured[1].decode("utf-8"))
    assert sent["messageID"] == 3
    assert sent["guid"] == "-1"
    assert "cli-proof-1" in sent["script"]
    assert "http://127.0.0.1:8000" in sent["script"]


def test_tts_execute_lua_cli_rejects_unreviewed_template(tmp_path: Path) -> None:
    template_path = tmp_path / "probe.lua"
    template_path.write_text('print("__RECEIPT__")', encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        [
            "tts-execute-lua",
            "--script-file",
            str(template_path),
            "--receipt",
            "cli-proof-1",
        ],
    )

    assert result.exit_code == 1
    assert "reviewed TTS Lua template" in result.output


def test_tts_execute_lua_cli_rejects_non_loopback_host() -> None:
    template_path = Path.cwd() / "docs" / "tts" / "external_editor_health_receipt.lua"

    result = CliRunner().invoke(
        cli,
        [
            "tts-execute-lua",
            "--script-file",
            str(template_path),
            "--receipt",
            "cli-proof-1",
            "--host",
            "192.0.2.10",
        ],
    )

    assert result.exit_code == 1
    assert "loopback-only" in result.output


def test_tts_health_proof_uses_runner_owned_server_and_fake_external_editor() -> None:
    captured = _start_fake_external_editor_that_calls_rendered_health_url()

    result = run_tts_health_proof(
        receipt="proof-123",
        project_root=Path.cwd(),
        host=captured.host,
        port=captured.port,
        process_check=_verified_tts_process,
        timeout_seconds=2,
    )
    captured.thread.join(timeout=2)

    assert result.proof_server_owned_listener is True
    assert result.tts_external_editor_process_verified is True
    assert result.external_editor_message_sent is True
    assert result.companion_receipt_observed is True
    assert result.live_tts_round_trip_observed is True
    assert result.readiness == "contracts-only"
    assert result.source == "TTS External Editor WebRequest.custom"
    assert result.blocker is None
    assert result.receipt_endpoint_path == "/api/tts/health"
    assert result.receipt_status_code == 200
    assert "proof-123" in captured.script
    assert "WebRequest.custom" in captured.script


def test_tts_health_proof_reports_external_editor_unavailable_without_receipt() -> None:
    def fail_to_send(_script: str) -> None:
        raise ConnectionRefusedError("connection refused")

    result = run_tts_health_proof(
        receipt="proof-123",
        project_root=Path.cwd(),
        execute_lua=fail_to_send,
        process_check=_verified_tts_process,
        timeout_seconds=0.01,
    )

    assert result.proof_server_owned_listener is True
    assert result.tts_external_editor_process_verified is True
    assert result.external_editor_message_sent is False
    assert result.companion_receipt_observed is False
    assert result.live_tts_round_trip_observed is False
    assert result.blocker == "tts-external-editor-unavailable"


def test_tts_health_proof_refuses_unverified_external_editor_process() -> None:
    sent_scripts: list[str] = []

    result = run_tts_health_proof(
        receipt="proof-123",
        project_root=Path.cwd(),
        execute_lua=sent_scripts.append,
        process_check=lambda _host, _port: TtsExternalEditorProcessCheck(
            verified=False,
            blocker="tts-external-editor-process-unverified",
        ),
        timeout_seconds=0.01,
    )

    assert sent_scripts == []
    assert result.proof_server_owned_listener is False
    assert result.tts_external_editor_process_verified is False
    assert result.external_editor_message_sent is False
    assert result.companion_receipt_observed is False
    assert result.live_tts_round_trip_observed is False
    assert result.blocker == "tts-external-editor-process-unverified"


@pytest.mark.parametrize(
    "exc",
    [
        subprocess.TimeoutExpired("powershell", timeout=5),
        OSError("cannot start powershell"),
    ],
)
def test_tts_external_editor_process_check_fails_closed_on_subprocess_errors(
    monkeypatch: pytest.MonkeyPatch,
    exc: Exception,
) -> None:
    def raise_subprocess_error(
        *_args: object, **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        raise exc

    monkeypatch.setattr(tts_live_proof.platform, "system", lambda: "Windows")
    monkeypatch.setattr(tts_live_proof.subprocess, "run", raise_subprocess_error)

    result = verify_tts_external_editor_process("127.0.0.1", 39999)

    assert result.verified is False
    assert result.blocker == "tts-external-editor-process-unverified"


def test_tts_health_proof_rejects_empty_explicit_receipt() -> None:
    with pytest.raises(ValueError, match="receipt"):
        run_tts_health_proof(
            receipt="",
            project_root=Path.cwd(),
            execute_lua=lambda _script: None,
            timeout_seconds=0,
        )


def test_tts_proof_health_cli_outputs_sanitized_live_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _start_fake_external_editor_that_calls_rendered_health_url()

    monkeypatch.setattr(tts_live_proof, "verify_tts_external_editor_process", _verified_tts_process)
    result = CliRunner().invoke(
        cli,
        [
            "tts-proof-health",
            "--receipt",
            "cli-proof-2",
            "--host",
            captured.host,
            "--port",
            str(captured.port),
            "--wait-seconds",
            "2",
        ],
    )
    captured.thread.join(timeout=2)

    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["live_tts_round_trip_observed"] is True
    assert output["tts_external_editor_process_verified"] is True
    assert output["companion_receipt_observed"] is True
    assert output["receipt"] == "cli-proof-2"
    assert output["readiness"] == "contracts-only"
    assert output["source"] == "TTS External Editor WebRequest.custom"
    assert "server.log" not in result.output
    assert "C:" not in result.output
    assert "cli-proof-2" in captured.script


class _CapturedExternalEditor:
    def __init__(self, *, host: str, port: int, thread: threading.Thread) -> None:
        self.host = host
        self.port = port
        self.thread = thread
        self.script = ""


def _start_fake_external_editor_that_calls_rendered_health_url() -> _CapturedExternalEditor:
    ready = threading.Event()
    captured = _CapturedExternalEditor(host="127.0.0.1", port=0, thread=threading.Thread())

    def run_server() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            host, port = server.getsockname()
            captured.host = host
            captured.port = port
            ready.set()
            connection, _ = server.accept()
            with connection:
                payload = _receive_all(connection)
            message = json.loads(payload.decode("utf-8"))
            captured.script = message["script"]
            url = _rendered_health_url_from_lua(captured.script)
            with urllib.request.urlopen(url, timeout=2) as response:
                assert response.status == 200

    captured.thread = threading.Thread(target=run_server, daemon=True)
    captured.thread.start()
    assert ready.wait(timeout=2)
    return captured


def _receive_all(connection: socket.socket) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = connection.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _rendered_health_url_from_lua(script: str) -> str:
    base_url = _lua_string_assignment(script, "COMPANION_BASE_URL")
    receipt = _lua_string_assignment(script, "RECEIPT")
    return f"{base_url}/api/tts/health?receipt={receipt}"


def _lua_string_assignment(script: str, name: str) -> str:
    marker = f'local {name} = "'
    start = script.index(marker) + len(marker)
    end = script.index('"', start)
    return script[start:end]


def _verified_tts_process(_host: str, _port: int) -> TtsExternalEditorProcessCheck:
    return TtsExternalEditorProcessCheck(
        verified=True,
        process_name="Tabletop Simulator",
        blocker=None,
    )
