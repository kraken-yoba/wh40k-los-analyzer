# Phase 7.5 Exposure Mode Housekeeping QA Pathway

Date: 2026-06-22

## Scope

This QA proves the housekeeping slice centralizes exposure-mode predicate semantics without changing
Deployment Exposure behavior.

## Automated Checks

Focused red/green command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py::test_exposure_mode_helpers_cover_all_supported_modes -q
```

Focused behavior-preservation batch:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q
```

Final validation:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- Exposure helper matrix matches the Phase 7 mode semantics.
- Unsupported raw exposure mode still blocks with `invalid-exposure-mode` and no overlays.
- Service rendering shows `coverage-image` iff the mode includes LOS and `threat-projection-image`
  iff the mode includes threat.
- Deployment Exposure candidate, threat, LOS, and placement diagnostics remain unchanged.
- Web and desktop still render through `WarhammerCompanionService`.
- No new warnings beyond the existing Starlette `TestClient` deprecation warning.

## Browser QA

Launch the local app and inspect with the built-in Browser:

- `/deployment-exposure`
- `/deployment-exposure?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=6&enemy_threat=2&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`
- `/deployment-exposure?packet_id=official-event-companion-page-52&deployment_zone_id=defender&friendly_x=29.34&friendly_y=10.00&friendly_base=1.57&enemy_x=14.66&enemy_y=49.99&enemy_base=1.57&enemy_move=6&enemy_threat=2&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`

For each route, verify:

- One `<svg class="map-svg">` exists.
- One form exists and zero `<script>` tags exist.
- `safe-zone-outline`, `threat-projection-image`, `coverage-image`, `model-base`, and
  `threat-source-base` are present.
- Visible warning copy still says the result is estimated and not a placement planner.
- Visible copy avoids `legal`, `safe`, `recommended`, `optimal`, `likely`, and `guaranteed`.
- Console warning/error logs for `127.0.0.1:8000` are empty.

If Browser control fails, retry with Computer Use and Firefox. If both fail, log exact blockers.

## Protected-Path Scan

Before staging, list changed and untracked files:

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

- Scope remains behavior-preserving.
- No route, template, desktop layout, renderer, geometry, or user-facing copy changes.
- Duplicate predicate helpers are removed from application/service layers.
- Tests prove unsupported raw exposure modes still block.
- Tests prove the helpers mean component inclusion, not selected risk composition.
- Browser QA covers page 9 and page 52 because the service still controls overlay selection.
