from __future__ import annotations

import json
import platform
import subprocess
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Final, cast
from urllib.parse import parse_qs, urlsplit

from warhammer_companion.application.tts_bridge import TtsBridgeService
from warhammer_companion.application.tts_external_editor import (
    RECEIPT_PATTERN,
    TtsExternalEditorClient,
    render_lua_probe_template,
    resolve_reviewed_lua_template,
)

REVIEWED_EXTERNAL_EDITOR_PROOF_TEMPLATE: Final = (
    Path("docs") / "tts" / "external_editor_health_receipt.lua"
)
REVIEWED_MANUAL_GLOBAL_PROOF_TEMPLATE: Final = (
    Path("docs") / "tts" / "manual_global_health_receipt.lua"
)
TTS_PROCESS_NAME_MARKER: Final = "tabletop"
TTS_PROOF_HEADER_NAME: Final = "X-Warhammer-TTS-Proof"

LuaExecutor = Callable[[str], None]
ManualProofReadyCallback = Callable[[str, str, str], None]
ProcessVerifier = Callable[[str, int], "TtsExternalEditorProcessCheck"]


@dataclass(frozen=True)
class TtsReceiptObservation:
    method: str
    path: str
    status_code: int


@dataclass(frozen=True)
class TtsExternalEditorProcessCheck:
    verified: bool
    process_name: str | None = None
    blocker: str | None = None


@dataclass(frozen=True)
class TtsHealthProofResult:
    receipt: str
    proof_server_host: str | None
    proof_server_port: int | None
    proof_server_owned_listener: bool
    tts_external_editor_process_verified: bool
    tts_external_editor_process_name: str | None
    external_editor_message_sent: bool
    companion_receipt_observed: bool
    live_tts_round_trip_observed: bool
    readiness: str
    source: str
    blocker: str | None
    receipt_endpoint_path: str | None = None
    receipt_status_code: int | None = None

    def to_sanitized_dict(self) -> dict[str, object]:
        return {
            "schema_version": "tts-health-proof/v0",
            "receipt": self.receipt,
            "proof_server_host": self.proof_server_host,
            "proof_server_port": self.proof_server_port,
            "proof_server_owned_listener": self.proof_server_owned_listener,
            "tts_external_editor_process_verified": (self.tts_external_editor_process_verified),
            "tts_external_editor_process_name": self.tts_external_editor_process_name,
            "external_editor_message_sent": self.external_editor_message_sent,
            "companion_receipt_observed": self.companion_receipt_observed,
            "live_tts_round_trip_observed": self.live_tts_round_trip_observed,
            "readiness": self.readiness,
            "source": self.source,
            "receipt_endpoint_path": self.receipt_endpoint_path,
            "receipt_status_code": self.receipt_status_code,
            "blocker": self.blocker,
        }


@dataclass(frozen=True)
class TtsManualHealthProofResult:
    receipt: str
    proof_server_host: str | None
    proof_server_port: int | None
    proof_server_owned_listener: bool
    companion_receipt_observed: bool
    live_tts_round_trip_observed: bool
    readiness: str
    source: str
    blocker: str | None
    receipt_endpoint_path: str | None = None
    receipt_status_code: int | None = None

    def to_sanitized_dict(self) -> dict[str, object]:
        return {
            "schema_version": "tts-manual-health-proof/v0",
            "receipt": self.receipt,
            "proof_server_host": self.proof_server_host,
            "proof_server_port": self.proof_server_port,
            "proof_server_owned_listener": self.proof_server_owned_listener,
            "companion_receipt_observed": self.companion_receipt_observed,
            "live_tts_round_trip_observed": self.live_tts_round_trip_observed,
            "readiness": self.readiness,
            "source": self.source,
            "receipt_endpoint_path": self.receipt_endpoint_path,
            "receipt_status_code": self.receipt_status_code,
            "blocker": self.blocker,
        }


def generate_receipt() -> str:
    return f"tts-proof-{uuid.uuid4().hex[:12]}"


def run_tts_health_proof(
    *,
    project_root: Path,
    receipt: str | None = None,
    host: str = "127.0.0.1",
    port: int = 39999,
    execute_lua: LuaExecutor | None = None,
    process_check: ProcessVerifier | None = None,
    timeout_seconds: float = 30.0,
) -> TtsHealthProofResult:
    safe_receipt = _validate_receipt(generate_receipt() if receipt is None else receipt)
    if timeout_seconds < 0:
        raise ValueError("Timeout seconds must be non-negative.")

    verifier = process_check or verify_tts_external_editor_process
    external_editor_process = verifier(host, port)
    if not external_editor_process.verified:
        return _health_result(
            receipt=safe_receipt,
            proof_server=None,
            external_editor_process=external_editor_process,
            external_editor_message_sent=False,
            blocker=external_editor_process.blocker or "tts-external-editor-process-unverified",
        )

    try:
        with _RunnerOwnedHealthServer(receipt=safe_receipt) as proof_server:
            script = _render_reviewed_external_editor_script(
                project_root=project_root,
                companion_base_url=proof_server.base_url,
                receipt=safe_receipt,
            )
            try:
                if execute_lua is None:
                    TtsExternalEditorClient(host=host, port=port).execute_lua(script)
                else:
                    execute_lua(script)
            except OSError:
                return _health_result(
                    receipt=safe_receipt,
                    proof_server=proof_server,
                    external_editor_process=external_editor_process,
                    external_editor_message_sent=False,
                    blocker="tts-external-editor-unavailable",
                )
            except ValueError:
                return _health_result(
                    receipt=safe_receipt,
                    proof_server=proof_server,
                    external_editor_process=external_editor_process,
                    external_editor_message_sent=False,
                    blocker="proof-configuration-invalid",
                )

            observation = proof_server.wait_for_receipt(timeout_seconds=timeout_seconds)
            return _health_result(
                receipt=safe_receipt,
                proof_server=proof_server,
                external_editor_process=external_editor_process,
                external_editor_message_sent=True,
                blocker=None if observation is not None else "companion-receipt-not-observed",
                observation=observation,
            )
    except OSError:
        return _health_result(
            receipt=safe_receipt,
            proof_server=None,
            external_editor_process=external_editor_process,
            external_editor_message_sent=False,
            blocker="proof-server-bind-failed",
        )


def run_tts_manual_health_proof(
    *,
    project_root: Path,
    receipt: str | None = None,
    timeout_seconds: float = 60.0,
    on_server_ready: ManualProofReadyCallback | None = None,
) -> TtsManualHealthProofResult:
    safe_receipt = _validate_receipt(generate_receipt() if receipt is None else receipt)
    if timeout_seconds < 0:
        raise ValueError("Timeout seconds must be non-negative.")

    try:
        with _RunnerOwnedHealthServer(receipt=safe_receipt) as proof_server:
            script = _render_reviewed_manual_global_script(
                project_root=project_root,
                companion_base_url=proof_server.base_url,
                receipt=safe_receipt,
            )
            if on_server_ready is not None:
                on_server_ready(proof_server.base_url, safe_receipt, script)
            observation = proof_server.wait_for_receipt(timeout_seconds=timeout_seconds)
            return _manual_health_result(
                receipt=safe_receipt,
                proof_server=proof_server,
                blocker=None if observation is not None else "companion-receipt-not-observed",
                observation=observation,
            )
    except OSError:
        return _manual_health_result(
            receipt=safe_receipt,
            proof_server=None,
            blocker="proof-server-bind-failed",
        )


def verify_tts_external_editor_process(host: str, port: int) -> TtsExternalEditorProcessCheck:
    _ = TtsExternalEditorClient(host=host, port=port)
    if platform.system() != "Windows":
        return TtsExternalEditorProcessCheck(
            verified=False,
            blocker="tts-external-editor-process-check-unsupported",
        )

    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "$conn = Get-NetTCPConnection "
                    f"-LocalPort {port} -State Listen -ErrorAction SilentlyContinue | "
                    "Select-Object -First 1; "
                    "if ($null -eq $conn) { exit 2 }; "
                    "$proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue; "
                    "if ($null -eq $proc) { exit 3 }; "
                    "[pscustomobject]@{ProcessName=$proc.ProcessName} | ConvertTo-Json -Compress"
                ),
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return TtsExternalEditorProcessCheck(
            verified=False,
            blocker="tts-external-editor-process-unverified",
        )
    if completed.returncode != 0:
        return TtsExternalEditorProcessCheck(
            verified=False,
            blocker="tts-external-editor-unavailable",
        )
    try:
        process_info = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return TtsExternalEditorProcessCheck(
            verified=False,
            blocker="tts-external-editor-process-unverified",
        )
    process_name = process_info.get("ProcessName") if isinstance(process_info, dict) else None
    if not isinstance(process_name, str):
        return TtsExternalEditorProcessCheck(
            verified=False,
            blocker="tts-external-editor-process-unverified",
        )
    if TTS_PROCESS_NAME_MARKER not in process_name.lower():
        return TtsExternalEditorProcessCheck(
            verified=False,
            process_name=process_name,
            blocker="tts-external-editor-process-unverified",
        )
    return TtsExternalEditorProcessCheck(
        verified=True,
        process_name=process_name,
        blocker=None,
    )


def _render_reviewed_external_editor_script(
    *,
    project_root: Path,
    companion_base_url: str,
    receipt: str,
) -> str:
    template = resolve_reviewed_lua_template(
        project_root / REVIEWED_EXTERNAL_EDITOR_PROOF_TEMPLATE,
        project_root=project_root,
    )
    return render_lua_probe_template(
        template,
        companion_base_url=companion_base_url,
        receipt=receipt,
    )


def _render_reviewed_manual_global_script(
    *,
    project_root: Path,
    companion_base_url: str,
    receipt: str,
) -> str:
    template = resolve_reviewed_lua_template(
        project_root / REVIEWED_MANUAL_GLOBAL_PROOF_TEMPLATE,
        project_root=project_root,
    )
    return render_lua_probe_template(
        template,
        companion_base_url=companion_base_url,
        receipt=receipt,
    )


def _health_result(
    *,
    receipt: str,
    proof_server: _RunnerOwnedHealthServer | None,
    external_editor_process: TtsExternalEditorProcessCheck,
    external_editor_message_sent: bool,
    blocker: str | None,
    observation: TtsReceiptObservation | None = None,
) -> TtsHealthProofResult:
    receipt_observed = observation is not None
    proof_server_owned_listener = proof_server is not None
    return TtsHealthProofResult(
        receipt=receipt,
        proof_server_host=proof_server.host if proof_server is not None else None,
        proof_server_port=proof_server.port if proof_server is not None else None,
        proof_server_owned_listener=proof_server_owned_listener,
        tts_external_editor_process_verified=external_editor_process.verified,
        tts_external_editor_process_name=external_editor_process.process_name,
        external_editor_message_sent=external_editor_message_sent,
        companion_receipt_observed=receipt_observed,
        live_tts_round_trip_observed=(
            proof_server_owned_listener
            and external_editor_process.verified
            and external_editor_message_sent
            and receipt_observed
        ),
        readiness="contracts-only",
        source=(
            "TTS External Editor WebRequest.custom"
            if external_editor_process.verified
            else "unverified TTS External Editor process"
        ),
        receipt_endpoint_path=observation.path if observation is not None else None,
        receipt_status_code=observation.status_code if observation is not None else None,
        blocker=blocker,
    )


def _manual_health_result(
    *,
    receipt: str,
    proof_server: _RunnerOwnedHealthServer | None,
    blocker: str | None,
    observation: TtsReceiptObservation | None = None,
) -> TtsManualHealthProofResult:
    receipt_observed = observation is not None
    proof_server_owned_listener = proof_server is not None
    return TtsManualHealthProofResult(
        receipt=receipt,
        proof_server_host=proof_server.host if proof_server is not None else None,
        proof_server_port=proof_server.port if proof_server is not None else None,
        proof_server_owned_listener=proof_server_owned_listener,
        companion_receipt_observed=receipt_observed,
        live_tts_round_trip_observed=proof_server_owned_listener and receipt_observed,
        readiness="contracts-only",
        source="TTS manual Lua WebRequest.custom",
        receipt_endpoint_path=observation.path if observation is not None else None,
        receipt_status_code=observation.status_code if observation is not None else None,
        blocker=blocker,
    )


class _ReceiptState:
    def __init__(self, *, receipt: str) -> None:
        self.receipt = receipt
        self.event = threading.Event()
        self.observation: TtsReceiptObservation | None = None

    def record(self, observation: TtsReceiptObservation) -> None:
        self.observation = observation
        self.event.set()


class _RunnerOwnedHealthServer:
    def __init__(self, *, receipt: str) -> None:
        self._state = _ReceiptState(receipt=receipt)
        self._server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            _build_health_handler(self._state),
        )
        server_host, server_port = cast(tuple[str, int], self._server.server_address)
        self.host = server_host
        self.port = server_port
        self.base_url = f"http://{self.host}:{self.port}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> _RunnerOwnedHealthServer:
        self._thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    def wait_for_receipt(self, *, timeout_seconds: float) -> TtsReceiptObservation | None:
        if self._state.event.wait(timeout=timeout_seconds):
            return self._state.observation
        return None


def _build_health_handler(
    state: _ReceiptState,
) -> type[BaseHTTPRequestHandler]:
    class HealthProofHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlsplit(self.path)
            receipt_values = parse_qs(parsed.query, keep_blank_values=True).get("receipt")
            proof_header = self.headers.get(TTS_PROOF_HEADER_NAME)
            if (
                parsed.path == "/api/tts/health"
                and receipt_values == [state.receipt]
                and proof_header == state.receipt
            ):
                self._send_json_response(200, TtsBridgeService().health().model_dump(mode="json"))
                state.record(
                    TtsReceiptObservation(
                        method="GET",
                        path="/api/tts/health",
                        status_code=200,
                    )
                )
                return
            self._send_json_response(
                404,
                {
                    "ok": False,
                    "error": {
                        "code": "proof-receipt-not-found",
                        "message": "No matching TTS proof receipt was found.",
                        "field_path": [],
                    },
                },
            )

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_json_response(self, status_code: int, payload: object) -> None:
            encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return HealthProofHandler


def _validate_receipt(receipt: str) -> str:
    if not RECEIPT_PATTERN.fullmatch(receipt):
        raise ValueError(
            "TTS proof receipt must be 1-80 characters and contain only letters, numbers, "
            "underscore, dot, colon, or hyphen."
        )
    return receipt
