# Phase 11.5 Pairing Label Normalization Housekeeping QA Pathway

Date: 2026-06-22

## Purpose

Prove Phase 11.5 extracts Team Pairing label normalization without changing labels, blocker ids,
input hashes, route output, desktop output, or source/privacy behavior.

## Automated QA

Run:

```powershell
git status --short --branch
.\.venv\Scripts\python.exe -m pytest tests\test_matchup_matrix_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Expected:

- Characterization tests confirm default input hash/result id, blocked-case input hashes/result ids,
  normalized labels, and blocker ids.
- Focused app tests pass.
- Ruff and mypy pass.
- Full pytest passes.
- Desktop smoke reports `team_pairing_matrix_degraded: true`.

## Manual QA

Open or request the equivalent rendered routes:

- `/team-pairing`
- `/team-pairing?friendly_lists=Alpha%20%20Prime%2C%2C%20%20Beta%0AControl%07Name&opponent_lists=Gamma%2C%2C%20Delta`
- `/team-pairing?friendly_lists=&opponent_lists=Gamma%0ADelta`
- `/team-pairing?friendly_lists=%3Cscript%3Ealert(1)%3C%2Fscript%3E&opponent_lists=Gamma`
- `/team-pairing?friendly_lists=A%0AB%0AC%0AD%0AE%0AF%0AG%0AH%0AI&opponent_lists=Gamma`

Expected:

- Output matches Phase 11A behavior: degraded default matrix, normalized labels in order, and
  blocked empty-friendly-label state.
- Script-shaped labels remain escaped/plain text.
- Overflow-label routes remain blocked with `too-many-friendly-lists`.
- No new visible copy or UI controls appear.
- No source URLs, public sheet id/gid, source payloads, SVG/image payloads, traceback, internal
  server error text, or custom JavaScript appear.

## Review And Commit Gate

- Consultant/spec-compliance reviewer approves behavior-preserving scope.
- Adversarial reviewer approves no hidden behavior change or source leak.
- Protected-source scan is clean.
- One atomic Phase 11.5 commit is created.
