# Phase 6.5 Threat Housekeeping QA Pathway

Date: 2026-06-22

## Scope

This QA proves Phase 6.5 is behavior-preserving. The slice may expose shared geometry helper code
and remove duplicate board-fit math, but it must not change threat range, movement reach, web route
behavior, desktop navigation, SVG output, source/readiness semantics, or generated data.

## Automated Checks

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_threat_range_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_threat_range_geometry.py tests\test_desktop_app.py tests\test_web_server.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- The shared `base_center_region(...)` helper test passes.
- Existing movement reach and threat range tests pass unchanged except for import updates.
- Full static checks and tests pass.
- Desktop smoke still reports `movement_reach_svg` and `threat_range_svg`.

## Browser QA

If the implementation touches only helper extraction and no web/desktop/rendering code, Browser QA
may be recorded as not required for this slice. If reviewers request runtime proof anyway, launch
the app and verify:

- `/movement-reach` renders one SVG map and one `.movement-envelope-image`.
- `/threat-range` renders one SVG map and one `.threat-projection-image`.
- Both pages contain no `<script>` tags and no console warnings or errors.

If Browser fails, retry with Computer Use and Firefox. If both fail, log the exact blocker.

## Protected-Path Scan

Before staging:

```powershell
$changed = @()
$changed += git diff --name-only
$changed += git diff --cached --name-only
$changed += git ls-files --others --exclude-standard
$changed | Sort-Object -Unique
```

Reject generated data/cache/log/build/dist paths, raw PDFs, roster archives, image/database files,
credentials, Codex state, and unexpected official-source artifacts. Keep `AGENTS.md` untracked and
unstaged unless explicitly requested.

## Reviewer Checklist

- Cleanup is small enough for a `.5` phase.
- No new player-facing tool behavior is introduced.
- Movement and threat tools use one base-center board-fit helper.
- Threat validation still returns `blocked` with no overlays for overhanging source bases.
- No web route, template, desktop screen, SVG class, source-trust, or readiness behavior changes.
- The final commit contains only docs, helper refactor code, and focused tests for this slice.
