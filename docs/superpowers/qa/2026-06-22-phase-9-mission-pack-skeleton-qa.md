# Phase 9 Mission Pack Skeleton QA Pathway

Date: 2026-06-22

## Scope

This QA proves Phase 9 adds source-safe mission pack records and a cautious Mission Pack surface
without scraping public sheets, storing images, copying card text, or implementing scoring
mechanics.

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

- Mission records are deduplicated from existing official layout metadata.
- Every mission record has source refs and page anchors.
- Result readiness is `estimated`; no trusted result is emitted.
- Public Google Sheet is represented only as untrusted source metadata.
- Public Google Sheet metadata contains only the supplied URL, sheet id, gid `1565185881`,
  retrieval status `not_fetched`, trust `untrusted_candidate`, and no content hash.
- No card images, full card text, or external-sheet payloads appear in source/tests/docs.
- Web and desktop tests pass.
- Desktop smoke reports `mission_pack_estimate: true`.

## Browser QA

Launch the local app and inspect with the built-in Browser:

- `/mission-pack`

Verify:

- Heading is `Mission Pack`.
- Primary mission records are visible.
- Source-pending and public-sheet-not-ingested warnings are visible.
- Zero `<script>` tags exist.
- No legal/optimal/recommended/likely/pairing-score wording is visible.
- No traceback/internal-error text is visible.
- Console warning/error logs for `127.0.0.1:8000` are empty.

If Browser control fails, retry with Computer Use and Firefox. If both fail, log exact blockers.

## Protected-Path Scan

Reject generated data/cache/log/build/dist paths, raw PDFs, images, screenshots, Google Sheet
exports, database/archive files, credentials, Codex state, and copied mission-card/rules text. Keep
`AGENTS.md` untracked and unstaged unless explicitly requested.

## Reviewer Checklist

- This is a skeleton/source-record phase, not scoring analytics.
- No public sheet fetch occurs.
- No protected mission-card image or full card text is committed.
- Mission mechanics are source-pending and output remains estimated.
