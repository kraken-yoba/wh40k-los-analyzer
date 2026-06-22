# Phase 8.5 Damage Profile Defaults Housekeeping QA Pathway

Date: 2026-06-22

## Scope

This QA proves Phase 8.5 centralizes default manual Damage Profile values without changing behavior.

## Automated Checks

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py tests\test_application_service.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Expected:

- Default constants expose the same Phase 8A sample values.
- Service default state returns expected damage 0.50.
- Desktop initial controls match the canonical defaults.
- Full test suite remains green.
- Desktop smoke still reports `damage_profile_estimate: true`.

## Browser QA

Launch the local app and inspect with the built-in Browser:

- `/damage-profile`

Verify:

- Heading is `Damage Profile`.
- One form exists and zero `<script>` tags exist.
- Default route shows expected damage `0.50`.
- Default route shows distribution rows `49/64`, `14/64`, and `1/64`.
- Warning copy includes manual-estimate trust boundaries.
- Console warning/error logs for `127.0.0.1:8000` are empty.

If Browser control fails, retry with Computer Use and Firefox. If both fail, log exact blockers.

## Reviewer Checklist

- The slice is behavior-preserving.
- No new damage mechanic, roster/profile authority, official source text, or tactical
  recommendation behavior is introduced.
- Domain defaults do not absorb web form/query field names.
- All changed files are source, tests, or docs only.
