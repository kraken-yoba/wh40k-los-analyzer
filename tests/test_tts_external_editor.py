from __future__ import annotations

import json
import socket
import threading
from pathlib import Path

import pytest
from typer.testing import CliRunner

from warhammer_companion.application.tts_external_editor import (
    TtsExternalEditorClient,
    build_execute_lua_message,
    render_lua_probe_template,
    resolve_reviewed_lua_template,
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
