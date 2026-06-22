# Phase 9.5 Mission Source Metadata Housekeeping Plan

Date: 2026-06-22

Goal: centralize mission-pack source metadata and warning text without changing runtime behavior.

## Task 1: Guardrail Tests

- [ ] Add focused tests in `tests/test_mission_pack_toolkit.py` proving:
  - canonical source refs are used by the toolkit payload;
  - default `input_hash` remains
    `sha256:01f1430011d73eec7f009f95dc8a4e5671b581dcdf7ecfdd0097020a5eefd2bc`;
  - default `result_id` remains `estimated:mission-pack:01f1430011d7`;
  - pack warnings and toolkit warning details share the same canonical warning text;
  - changing source metadata through private helper input changes the input hash;
  - public-sheet metadata remains `not_fetched`, `untrusted_candidate`, and `content_hash=None`.

## Task 2: Refactor Mission-Pack Builder

- [ ] Add internal canonical warning constants in `application/mission_pack.py`.
- [ ] Add a canonical source-ref helper, such as `_mission_source_refs()`.
- [ ] Update `build_mission_pack_toolkit_result(...)` to use the helper.
- [ ] Update `_mission_pack_hash(...)` to derive public-sheet hash fields from the source-ref object
  instead of duplicate literals.
- [ ] Preserve output values and the public `build_mission_pack_toolkit_result(...)` signature.
- [ ] Keep any test injection private to `_mission_pack_hash(...)` or another private helper.

## Task 3: Documentation And Work Log

- [ ] Update `docs/work-log/player-toolkit-implementation.md` with Phase 9.5 purpose, decisions,
  verification, and review outcomes.

## Task 4: Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Browser QA:

- Launch local app.
- Open `/mission-pack`.
- Verify heading, primary mission records, public-sheet source row, source-pending/not-fetched/
  not-ingested warnings, zero `<script>` tags, no traceback/internal-error text, no forbidden
  recommendation wording, and no console warning/error logs.

## Task 5: Commit

- [ ] Protected-path scan excludes generated/raw/cache/log/build/dist/PDF/database/archive/image
  paths, `.codex`, `.agents`, `data/codex-home*`, auth/session files, credentials, Google Sheet
  exports, screenshots, other Codex/OpenAI state, and card text.
- [ ] Keep `AGENTS.md` untracked and unstaged.
- [ ] Commit as one atomic Phase 9.5 housekeeping commit.
