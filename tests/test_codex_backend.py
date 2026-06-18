from __future__ import annotations

import importlib.metadata
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

import warhammer_companion.integrations.codex_backend as codex_backend_module
from warhammer_companion.integrations.codex_backend import (
    CodexBackend,
    _app_codex_home,
    sanitize_status_message,
)


def test_codex_backend_reports_authenticated_chatgpt_account() -> None:
    backend = CodexBackend(codex_factory=lambda: _FakeCodex(account=_chatgpt_account()))

    status = backend.current_status()

    assert status.sdk_available
    assert status.authenticated
    assert status.account_label == "ChatGPT account a***@example.com"
    assert status.auth_method == "chatgpt"
    assert status.runtime_source == "openai-codex bundled runtime"
    assert status.runtime_package_version
    assert status.state_home
    assert status.can_logout
    assert status.can_login


def test_codex_backend_reports_missing_sdk() -> None:
    backend = CodexBackend(codex_factory=None, sdk_importer=lambda: None)

    status = backend.current_status()

    assert not status.sdk_available
    assert not status.authenticated
    assert status.state == "sdk-missing"
    assert "openai-codex" in status.detail


def test_codex_backend_sanitizes_runtime_errors() -> None:
    def broken_factory() -> _FakeCodex:
        raise RuntimeError("login failed with token sk-secret1234567890abcdef")

    backend = CodexBackend(codex_factory=broken_factory)

    status = backend.current_status()

    assert status.state == "runtime-error"
    assert "sk-secret" not in status.detail
    assert "[redacted]" in status.detail


def test_codex_backend_starts_browser_login_and_redacts_live_status() -> None:
    fake_codex = _FakeCodex(account=None)
    backend = CodexBackend(codex_factory=lambda: fake_codex)

    start = backend.start_chatgpt_login()

    assert start.method == "browser"
    assert start.auth_url == "https://auth.example/login"
    assert start.user_code is None
    assert backend.current_status().active_login_label == "Browser login pending"


def test_codex_backend_starts_device_code_login() -> None:
    fake_codex = _FakeCodex(account=None)
    backend = CodexBackend(codex_factory=lambda: fake_codex)

    start = backend.start_chatgpt_device_code_login()

    assert start.method == "device-code"
    assert start.verification_url == "https://auth.example/device"
    assert start.user_code == "ABCD-EFGH"


def test_codex_backend_logout_uses_codex_and_clears_pending_login() -> None:
    fake_codex = _FakeCodex(account=_chatgpt_account())
    backend = CodexBackend(codex_factory=lambda: fake_codex)
    backend.start_chatgpt_login()

    backend.logout()

    assert fake_codex.logged_out
    assert backend.current_status().active_login_label is None


def test_status_sanitizer_redacts_long_token_like_strings() -> None:
    message = sanitize_status_message("error token=eyJabcdefghijklmnopqrstuvwxyz1234567890")

    assert "eyJ" not in message
    assert "[redacted]" in message


def test_openai_codex_dependency_is_declared() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    assert any(dependency.startswith("openai-codex") for dependency in dependencies)

    version = importlib.metadata.version("openai-codex")

    assert version


def test_openai_codex_cli_runtime_dependency_is_installed() -> None:
    version = importlib.metadata.version("openai-codex-cli-bin")

    assert version


def test_default_codex_home_is_app_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local-app-data"))
    monkeypatch.delenv("WARHAMMER_COMPANION_CODEX_HOME", raising=False)
    monkeypatch.delenv("CODEX_SHELL", raising=False)
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    monkeypatch.setattr(
        codex_backend_module,
        "_portable_codex_home",
        lambda: tmp_path / "project" / "data" / "codex-home",
    )

    if os.name == "nt":
        expected = tmp_path / "local-app-data" / "WarhammerTournamentCompanion" / "codex-home"
    else:
        expected = (
            Path.home() / ".local" / "state" / "warhammer-tournament-companion" / "codex-home"
        )
    assert _app_codex_home() == expected


def test_codex_home_falls_back_to_portable_state_when_user_data_is_blocked(
    tmp_path: Path,
    monkeypatch,
) -> None:
    preferred = tmp_path / "blocked-user-data" / "WarhammerTournamentCompanion" / "codex-home"
    portable = tmp_path / "project" / "data" / "codex-home"
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "blocked-user-data"))
    monkeypatch.delenv("WARHAMMER_COMPANION_CODEX_HOME", raising=False)
    monkeypatch.delenv("CODEX_SHELL", raising=False)
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    monkeypatch.setattr(codex_backend_module, "_default_codex_home", lambda: preferred)
    monkeypatch.setattr(codex_backend_module, "_portable_codex_home", lambda: portable)

    def fake_writable_dir(path: Path) -> bool:
        return path != preferred

    monkeypatch.setattr(codex_backend_module, "_ensure_writable_dir", fake_writable_dir)

    assert _app_codex_home() == portable


def test_codex_home_uses_portable_state_inside_codex_shell(
    tmp_path: Path,
    monkeypatch,
) -> None:
    portable = tmp_path / "project" / "data" / "codex-home"
    monkeypatch.delenv("WARHAMMER_COMPANION_CODEX_HOME", raising=False)
    monkeypatch.setenv("CODEX_SHELL", "1")
    monkeypatch.setattr(codex_backend_module, "_portable_codex_home", lambda: portable)

    assert _app_codex_home() == portable


def test_existing_portable_codex_home_takes_precedence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    preferred = tmp_path / "user-data" / "WarhammerTournamentCompanion" / "codex-home"
    portable = tmp_path / "project" / "data" / "codex-home"
    portable.mkdir(parents=True)
    monkeypatch.delenv("WARHAMMER_COMPANION_CODEX_HOME", raising=False)
    monkeypatch.delenv("CODEX_SHELL", raising=False)
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    monkeypatch.setattr(codex_backend_module, "_default_codex_home", lambda: preferred)
    monkeypatch.setattr(codex_backend_module, "_portable_codex_home", lambda: portable)

    assert _app_codex_home() == portable


def test_codex_home_can_be_overridden_for_standalone_packaging(
    tmp_path: Path,
    monkeypatch,
) -> None:
    configured = tmp_path / "state"
    monkeypatch.setenv("WARHAMMER_COMPANION_CODEX_HOME", str(configured))

    assert _app_codex_home() == configured


@dataclass
class _FakeRoot:
    type: str
    email: str | None = None
    plan_type: str | None = None


@dataclass
class _FakeAccount:
    root: _FakeRoot


@dataclass
class _FakeAccountResponse:
    account: _FakeAccount | None
    requires_openai_auth: bool = True


class _FakeMetadata:
    serverInfo = type("ServerInfo", (), {"name": "Codex Test", "version": "0.1"})()


class _FakeLoginHandle:
    login_id = "login-1"
    auth_url = "https://auth.example/login"
    verification_url = "https://auth.example/device"
    user_code = "ABCD-EFGH"

    def wait(self) -> None:
        return None

    def cancel(self) -> None:
        return None


class _FakeCodex:
    def __init__(self, account: _FakeAccount | None):
        self._account = account
        self.metadata = _FakeMetadata()
        self.logged_out = False
        self.closed = False

    def account(self, *, refresh_token: bool = False) -> _FakeAccountResponse:
        return _FakeAccountResponse(account=self._account)

    def login_chatgpt(self) -> _FakeLoginHandle:
        return _FakeLoginHandle()

    def login_chatgpt_device_code(self) -> _FakeLoginHandle:
        return _FakeLoginHandle()

    def logout(self) -> None:
        self.logged_out = True

    def close(self) -> None:
        self.closed = True


def _chatgpt_account() -> _FakeAccount:
    return _FakeAccount(_FakeRoot(type="chatgpt", email="alice@example.com", plan_type="plus"))
