# Packaging Notes

## Codex Backend

The app must package Codex through the Python dependency graph, not through a globally installed `codex` executable.

- `pyproject.toml` declares `openai-codex`.
- `openai-codex` depends on `openai-codex-cli-bin`, which provides the pinned Codex runtime used by the SDK.
- `CodexBackend` intentionally constructs `CodexConfig` without `codex_bin`, so the SDK uses its packaged runtime.
- Codex credentials and state are stored outside public map data.
- On Windows, the default state path is `%LOCALAPPDATA%\WarhammerTournamentCompanion\codex-home`.
- On Unix-like systems, the default state path is `$XDG_STATE_HOME/warhammer-tournament-companion/codex-home` or `~/.local/state/warhammer-tournament-companion/codex-home`.
- Standalone packagers can set `WARHAMMER_COMPANION_CODEX_HOME` to a different app-specific writable user-data directory.
- Portable builds can pre-create `data/codex-home`; when that directory already exists and is writable, the app uses it as the Codex state home.
- When the app is run from inside a Codex desktop shell, it prefers portable state under `data/codex-home` because the bundled Codex runtime inherits the shell sandbox and may not be able to use `%LOCALAPPDATA%`.
- If the preferred user-data directory cannot be created or written, the app falls back to portable state under `data/codex-home` in the current app working directory. This keeps development sandboxes and portable downloads functional while still preferring OS user-data storage for normal standalone releases.
- Do not read, display, copy, or bundle user `auth.json` files.

For PyInstaller or another frozen-app packager, include package metadata and binaries for:

- `openai_codex`
- `codex_cli_bin`
- `openai-codex`
- `openai-codex-cli-bin`

This keeps the release independent of whether the target machine has Codex Desktop or the Codex CLI already installed.

## Temporary TypeScript Exception Policy

The core app remains Python-first. A temporary TypeScript frontend component is allowed only when a specific browser interaction cannot be implemented acceptably with the server-rendered Python UI.

Any such exception must be:

- isolated behind a narrow UI boundary,
- documented with the reason Python-only was insufficient,
- removable without changing the Python domain model,
- excluded from ingestion and LOS geometry logic.

This Codex/categorizer slice did not require TypeScript.
