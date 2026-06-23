from __future__ import annotations

import json
import re
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from urllib.parse import urlparse

RECEIPT_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")
LOCAL_COMPANION_HOSTS: Final = frozenset({"127.0.0.1", "localhost"})
REVIEWED_TTS_LUA_TEMPLATES: Final = frozenset(
    {
        Path("docs") / "tts" / "external_editor_health_receipt.lua",
        Path("docs") / "tts" / "manual_global_health_receipt.lua",
    }
)


def build_execute_lua_message(script: str, *, guid: str = "-1") -> bytes:
    if not script.strip():
        raise ValueError("Lua script must not be empty.")
    if not guid.strip():
        raise ValueError("TTS object guid must not be empty.")
    message = {
        "messageID": 3,
        "guid": guid,
        "script": script,
    }
    return json.dumps(message, separators=(",", ":")).encode("utf-8")


def render_lua_probe_template(
    template_path: Path,
    *,
    companion_base_url: str,
    receipt: str,
) -> str:
    safe_receipt = _validate_receipt(receipt)
    safe_companion_base_url = _validate_companion_base_url(companion_base_url)
    template = template_path.read_text(encoding="utf-8")
    return template.replace("__COMPANION_BASE_URL__", safe_companion_base_url).replace(
        "__RECEIPT__",
        safe_receipt,
    )


def resolve_reviewed_lua_template(script_file: Path, *, project_root: Path) -> Path:
    resolved_root = project_root.resolve()
    resolved_script = script_file.resolve()
    allowed = {
        (resolved_root / relative_path).resolve() for relative_path in REVIEWED_TTS_LUA_TEMPLATES
    }
    if resolved_script not in allowed:
        raise ValueError("Script file must be a reviewed TTS Lua template under docs/tts.")
    if not resolved_script.is_file():
        raise ValueError("Reviewed TTS Lua template does not exist.")
    return resolved_script


@dataclass(frozen=True)
class TtsExternalEditorClient:
    host: str = "127.0.0.1"
    port: int = 39999
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "host", _validate_tts_external_editor_host(self.host))
        if self.port < 1 or self.port > 65535:
            raise ValueError("TTS External Editor port must be between 1 and 65535.")

    def execute_lua(self, script: str, *, guid: str = "-1") -> None:
        payload = build_execute_lua_message(script, guid=guid)
        with socket.create_connection((self.host, self.port), timeout=self.timeout_seconds) as sock:
            sock.settimeout(self.timeout_seconds)
            sock.sendall(payload)
            sock.shutdown(socket.SHUT_WR)


def _validate_receipt(receipt: str) -> str:
    if not RECEIPT_PATTERN.fullmatch(receipt):
        raise ValueError(
            "TTS proof receipt must be 1-80 characters and contain only letters, numbers, "
            "underscore, dot, colon, or hyphen."
        )
    return receipt


def _validate_companion_base_url(companion_base_url: str) -> str:
    parsed = urlparse(companion_base_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError(
            "Companion base URL must include a valid port if a port is present."
        ) from exc
    if parsed.scheme != "http" or parsed.hostname not in LOCAL_COMPANION_HOSTS:
        raise ValueError("Companion base URL must be local HTTP on 127.0.0.1 or localhost.")
    if parsed.username or parsed.password:
        raise ValueError("Companion base URL must not include userinfo.")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("Companion base URL must be a local origin without path or query data.")
    hostname = parsed.hostname.lower()
    port_suffix = f":{port}" if port is not None else ""
    return f"http://{hostname}{port_suffix}"


def _validate_tts_external_editor_host(host: str) -> str:
    normalized = host.strip().lower()
    if normalized not in LOCAL_COMPANION_HOSTS:
        raise ValueError("TTS External Editor host must be loopback-only: 127.0.0.1 or localhost.")
    return normalized
