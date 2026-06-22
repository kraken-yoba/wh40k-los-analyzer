# Phase 9.5 Mission Source Metadata Housekeeping QA Pathway

Date: 2026-06-22

## Scope

This QA proves a behavior-preserving cleanup: mission-pack source metadata and warnings are
centralized, while the Phase 9 product behavior remains unchanged.

## Automated Checks

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

Expected:

- Mission source refs are unchanged from Phase 9.
- Default `input_hash` remains
  `sha256:01f1430011d73eec7f009f95dc8a4e5671b581dcdf7ecfdd0097020a5eefd2bc`.
- Default `result_id` remains `estimated:mission-pack:01f1430011d7`.
- Pack warnings and toolkit warning details share canonical text.
- The public `build_mission_pack_toolkit_result(...)` signature is unchanged; any test injection is
  private-helper-only.
- Public Google Sheet remains metadata-only with retrieval status `not_fetched`, trust
  `untrusted_candidate`, and no content hash.
- Input hash identity is derived from canonical source-ref metadata.
- Web and desktop tests pass without route or screen behavior changes.
- Desktop smoke still reports `mission_pack_estimate: true`.

## Browser QA

Open `/mission-pack` with the built-in Browser and verify:

- heading `Mission Pack`;
- primary mission records including `Battlefield Dominance` and `Sabotage`;
- public-sheet source row with sheet id and gid `1565185881`;
- source-pending/not-fetched/not-ingested warning copy;
- zero `<script>` tags;
- no traceback/internal-error text;
- no legal/optimal/recommended/likely/pairing-score wording;
- no console warning/error logs.

## Protected-Path Scan

Reject generated data/cache/log/build/dist paths, raw PDFs, images, screenshots, Google Sheet
exports, database/archive files, `.codex`, `.agents`, `data/codex-home*`, auth/session files,
credentials, other Codex/OpenAI state, and copied mission-card/rules text. Keep `AGENTS.md`
untracked and unstaged unless explicitly requested.
