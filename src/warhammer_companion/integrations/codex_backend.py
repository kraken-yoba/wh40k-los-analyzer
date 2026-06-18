from __future__ import annotations

import importlib
import importlib.metadata
import os
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

_DEFAULT_FACTORY = object()

CodexFactory = Callable[[], Any]
SdkImporter = Callable[[], CodexFactory | None]
BackendState = Literal[
    "sdk-missing",
    "runtime-error",
    "not-authenticated",
    "authenticated",
]
LoginMethod = Literal["browser", "device-code"]


@dataclass(frozen=True)
class CodexBackendStatus:
    state: BackendState
    label: str
    detail: str
    sdk_available: bool
    sdk_version: str | None
    runtime_label: str | None
    runtime_source: str
    runtime_package_version: str | None
    state_home: str | None
    authenticated: bool
    auth_method: str | None
    account_label: str
    requires_openai_auth: bool | None
    can_login: bool
    can_logout: bool
    active_login_label: str | None


@dataclass(frozen=True)
class CodexLoginStart:
    method: LoginMethod
    login_id: str
    auth_url: str | None = None
    verification_url: str | None = None
    user_code: str | None = None


@dataclass
class _ActiveLogin:
    method: LoginMethod
    login_id: str
    codex: Any
    handle: Any
    auth_url: str | None = None
    verification_url: str | None = None
    user_code: str | None = None

    @property
    def label(self) -> str:
        return "Browser login pending" if self.method == "browser" else "Device code login pending"

    def cancel_and_close(self) -> None:
        try:
            cancel = getattr(self.handle, "cancel", None)
            if callable(cancel):
                cancel()
        finally:
            _close_codex(self.codex)


class CodexBackend:
    def __init__(
        self,
        codex_factory: CodexFactory | None | object = _DEFAULT_FACTORY,
        *,
        sdk_importer: SdkImporter = lambda: _import_codex_factory(),
    ) -> None:
        self._sdk_importer = sdk_importer
        self._codex_factory: CodexFactory | None | object = codex_factory
        self._active_login: _ActiveLogin | None = None

    def current_status(self) -> CodexBackendStatus:
        factory = self._resolved_factory()
        sdk_version = _sdk_version()
        runtime_package_version = _runtime_package_version()
        state_home = str(_app_codex_home())
        if factory is None:
            return CodexBackendStatus(
                state="sdk-missing",
                label="Codex SDK not installed",
                detail=(
                    "Install the openai-codex Python package to enable local Codex "
                    "app-server login and visual categorizer jobs."
                ),
                sdk_available=False,
                sdk_version=sdk_version,
                runtime_label=None,
                runtime_source="openai-codex Python package",
                runtime_package_version=runtime_package_version,
                state_home=state_home,
                authenticated=False,
                auth_method=None,
                account_label="Unavailable",
                requires_openai_auth=None,
                can_login=False,
                can_logout=False,
                active_login_label=None,
            )

        codex: Any | None = None
        try:
            codex = factory()
            metadata = getattr(codex, "metadata", None)
            runtime_label = _runtime_label(metadata)
            account_response = codex.account(refresh_token=False)
            account = getattr(account_response, "account", None)
            requires_openai_auth = cast(
                bool | None,
                getattr(account_response, "requires_openai_auth", None),
            )
            if account is None:
                return CodexBackendStatus(
                    state="not-authenticated",
                    label="Codex SDK ready",
                    detail="No Codex account is signed in. Start a Codex ChatGPT login flow.",
                    sdk_available=True,
                    sdk_version=sdk_version,
                    runtime_label=runtime_label,
                    runtime_source="openai-codex bundled runtime",
                    runtime_package_version=runtime_package_version,
                    state_home=state_home,
                    authenticated=False,
                    auth_method=None,
                    account_label="Not signed in",
                    requires_openai_auth=requires_openai_auth,
                    can_login=True,
                    can_logout=False,
                    active_login_label=self._active_login.label if self._active_login else None,
                )
            root = getattr(account, "root", account)
            auth_method = cast(str | None, getattr(root, "type", None))
            active_login = self._active_login
            if active_login is not None:
                active_login.cancel_and_close()
                self._active_login = None
            return CodexBackendStatus(
                state="authenticated",
                label="Codex account signed in",
                detail="Codex credentials are managed by Codex local auth storage, not this app.",
                sdk_available=True,
                sdk_version=sdk_version,
                runtime_label=runtime_label,
                runtime_source="openai-codex bundled runtime",
                runtime_package_version=runtime_package_version,
                state_home=state_home,
                authenticated=True,
                auth_method=auth_method,
                account_label=_account_label(root),
                requires_openai_auth=requires_openai_auth,
                can_login=True,
                can_logout=True,
                active_login_label=None,
            )
        except Exception as exc:
            return CodexBackendStatus(
                state="runtime-error",
                label="Codex runtime unavailable",
                detail=sanitize_status_message(str(exc)),
                sdk_available=True,
                sdk_version=sdk_version,
                runtime_label=None,
                runtime_source="openai-codex bundled runtime",
                runtime_package_version=runtime_package_version,
                state_home=state_home,
                authenticated=False,
                auth_method=None,
                account_label="Unavailable",
                requires_openai_auth=None,
                can_login=False,
                can_logout=False,
                active_login_label=self._active_login.label if self._active_login else None,
            )
        finally:
            if codex is not None:
                _close_codex(codex)

    def start_chatgpt_login(self) -> CodexLoginStart:
        factory = self._require_factory()
        self._cancel_active_login()
        codex = factory()
        try:
            handle = codex.login_chatgpt()
            active = _ActiveLogin(
                method="browser",
                login_id=str(handle.login_id),
                codex=codex,
                handle=handle,
                auth_url=str(handle.auth_url),
            )
            self._active_login = active
            return CodexLoginStart(
                method="browser",
                login_id=active.login_id,
                auth_url=active.auth_url,
            )
        except Exception:
            _close_codex(codex)
            raise

    def start_chatgpt_device_code_login(self) -> CodexLoginStart:
        factory = self._require_factory()
        self._cancel_active_login()
        codex = factory()
        try:
            handle = codex.login_chatgpt_device_code()
            active = _ActiveLogin(
                method="device-code",
                login_id=str(handle.login_id),
                codex=codex,
                handle=handle,
                verification_url=str(handle.verification_url),
                user_code=str(handle.user_code),
            )
            self._active_login = active
            return CodexLoginStart(
                method="device-code",
                login_id=active.login_id,
                verification_url=active.verification_url,
                user_code=active.user_code,
            )
        except Exception:
            _close_codex(codex)
            raise

    def logout(self) -> None:
        factory = self._require_factory()
        self._cancel_active_login()
        codex = factory()
        try:
            codex.logout()
        finally:
            _close_codex(codex)

    def _require_factory(self) -> CodexFactory:
        factory = self._resolved_factory()
        if factory is None:
            raise RuntimeError("openai-codex Python SDK is not installed")
        return factory

    def _resolved_factory(self) -> CodexFactory | None:
        if self._codex_factory is not _DEFAULT_FACTORY:
            return cast(CodexFactory | None, self._codex_factory)
        factory = self._sdk_importer()
        return factory if factory is not None else None

    def _cancel_active_login(self) -> None:
        if self._active_login is not None:
            self._active_login.cancel_and_close()
            self._active_login = None


def sanitize_status_message(message: str) -> str:
    sanitized = re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", message)
    sanitized = re.sub(r"eyJ[A-Za-z0-9_.=-]{16,}", "[redacted]", sanitized)
    sanitized = re.sub(r"\b[A-Za-z0-9_-]{48,}\b", "[redacted]", sanitized)
    return sanitized[:500] if sanitized else "No diagnostic message was returned."


def _import_codex_factory() -> CodexFactory | None:
    try:
        module = importlib.import_module("openai_codex")
    except ImportError:
        return None
    codex_class = module.Codex
    config_class = module.CodexConfig

    def factory() -> Any:
        codex_home = _app_codex_home()
        codex_home.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)
        env.setdefault("CODEX_SQLITE_HOME", str(codex_home))
        return codex_class(config_class(env=env))

    return factory


def _sdk_version() -> str | None:
    try:
        return importlib.metadata.version("openai-codex")
    except importlib.metadata.PackageNotFoundError:
        return None


def _runtime_package_version() -> str | None:
    try:
        return importlib.metadata.version("openai-codex-cli-bin")
    except importlib.metadata.PackageNotFoundError:
        return None


def _app_codex_home() -> Path:
    configured = os.getenv("WARHAMMER_COMPANION_CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    portable = _portable_codex_home()
    if portable.exists() and _ensure_writable_dir(portable):
        return portable
    if _running_inside_codex_shell():
        if _ensure_writable_dir(portable):
            return portable
    preferred = _default_codex_home()
    if _ensure_writable_dir(preferred):
        return preferred
    portable = _portable_codex_home()
    if _ensure_writable_dir(portable):
        return portable
    return preferred


def _default_codex_home() -> Path:
    if os.name == "nt":
        local_app_data = os.getenv("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return (base / "WarhammerTournamentCompanion" / "codex-home").resolve()
    state_home = os.getenv("XDG_STATE_HOME")
    base = Path(state_home) if state_home else Path.home() / ".local" / "state"
    return (base / "warhammer-tournament-companion" / "codex-home").resolve()


def _portable_codex_home() -> Path:
    return (Path.cwd() / "data" / "codex-home").resolve()


def _running_inside_codex_shell() -> bool:
    return os.getenv("CODEX_SHELL") == "1" or bool(os.getenv("CODEX_THREAD_ID"))


def _ensure_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write-test"
        probe.write_text("", encoding="utf-8")
        probe.unlink(missing_ok=True)
        child_probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; import sys; "
                    "p=Path(sys.argv[1]); f=p/'.child-write-test'; "
                    "f.write_text('', encoding='utf-8'); f.unlink()"
                ),
                str(path),
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        if child_probe.returncode != 0:
            return False
    except OSError:
        return False
    except subprocess.SubprocessError:
        return False
    return True


def _runtime_label(metadata: Any) -> str | None:
    server_info = getattr(metadata, "serverInfo", None)
    if server_info is None:
        return None
    name = getattr(server_info, "name", None)
    version = getattr(server_info, "version", None)
    if name and version:
        return f"{name} {version}"
    return str(name or version) if name or version else None


def _account_label(account_root: Any) -> str:
    auth_type = getattr(account_root, "type", None)
    if auth_type == "chatgpt":
        email = _redact_email(cast(str | None, getattr(account_root, "email", None)))
        return f"ChatGPT account {email}" if email else "ChatGPT account"
    if auth_type == "apiKey":
        return "OpenAI API key"
    if auth_type:
        return f"Codex account ({auth_type})"
    return "Codex account"


def _redact_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local, domain = email.split("@", 1)
    first = local[:1] or "*"
    return f"{first}***@{domain}"


def _close_codex(codex: Any) -> None:
    close = getattr(codex, "close", None)
    if callable(close):
        close()
