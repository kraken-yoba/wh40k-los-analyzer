# Phase 5.5 Movement Housekeeping QA Pathway

Date: 2026-06-21

## Scope

This QA proves Phase 5.5 is behavior-preserving. The slice may extract shared helper code and
remove duplication, but it must not change movement reach, LOS, web route behavior, desktop
navigation, SVG class names, or source/readiness semantics.

## Automated Checks

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_desktop_screen_helpers.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_rendering_svg.py tests\test_desktop_app.py tests\test_web_server.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- Shared desktop helper test passes.
- Rendering tests still find `coverage-image`, `movement-envelope-image`,
  `movement-path-outline`, `movement-start-base`, and `movement-target-base`.
- Decoded PNG tests preserve representative raster semantics for `heatmap-image`,
  `coverage-image`, `hidden-coverage-image`, and `movement-envelope-image`.
- Desktop smoke still reports `los_svg`, `movement_reach_svg`, and `viewer_svg`.
- Full tests and static checks pass.

## Browser QA

Launch `.\.venv\Scripts\python.exe -m warhammer_companion.app` and use the built-in Browser:

- `/movement-reach` renders one SVG map and one `.movement-envelope-image`.
- `/los-checker` renders one SVG map and one `.coverage-image`.
- `/heatmap` renders one SVG map and one `.heatmap-image`.
- `/hidden-coverage` renders one SVG map and one `.hidden-coverage-image`.
- `/viewer` renders one SVG map.
- All three pages contain no `<script>` tags and no console warnings or errors.

Run the movement/heatmap smoke paths for the default official packet and a `layout_variant=B`
selector query. Include page-52-style selector coverage when practical.

If Browser fails, retry with Computer Use and Firefox. If both fail, log the blocker honestly and
keep shell/desktop evidence separate from manual Browser evidence.

## Protected-Path Scan

Before staging:

```powershell
$changed = @()
$changed += git diff --name-only
$changed += git diff --cached --name-only
$changed += git ls-files --others --exclude-standard
$changed | Sort-Object -Unique
```

Reject any unexpected generated/raw source, image, archive, database, log, cache, credential, or
Codex state path. Keep `AGENTS.md` untracked and unstaged.

## Reviewer Checklist

- Cleanup is behavior-preserving and small enough for a `.5` phase.
- No new feature behavior or UI surface is introduced.
- Public SVG classes and web routes are stable.
- Overlay-specific semantics remain separate; only binary raster plumbing is shared.
- Desktop screens still call `WarhammerCompanionService` and do not duplicate domain logic.
- The final commit contains only docs, helper/refactor code, and tests for this slice.
