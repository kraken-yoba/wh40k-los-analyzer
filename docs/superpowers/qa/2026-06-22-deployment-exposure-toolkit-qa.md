# Phase 7 Deployment Exposure Toolkit QA Pathway

Date: 2026-06-22

## Scope

This QA proves Phase 7 adds a deterministic manual deployment exposure diagnostic without claiming
source-backed placement compliance or introducing mission-aware optimization.

## Automated Checks

Run focused checks during implementation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_rendering_svg.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_web_server.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_desktop_app.py -q
```

Run final validation:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- Valid manual inputs return `estimated`.
- Invalid manual inputs return `blocked` with no overlays.
- Candidate staging center region is constrained by deployment zone, board fit, dense collision
  estimate, and selected risk assumption.
- No result claims source-backed placement compliance, optimization, recommendation, likelihood, or
  guaranteed outcomes.
- Web and desktop both render through the shared service.

## Browser QA

Launch the local app and inspect with the built-in Browser:

- `/deployment-exposure`
- `/deployment-exposure?deployment_zone_id=attacker&friendly_x=10&friendly_y=8&friendly_base=1.57&enemy_x=22&enemy_y=30&enemy_base=1.57&enemy_move=6&enemy_threat=2&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`
- `/deployment-exposure?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=6&enemy_threat=2&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`
- `/deployment-exposure?packet_id=official-event-companion-page-52&deployment_zone_id=defender&friendly_x=29.34&friendly_y=10.00&friendly_base=1.57&enemy_x=14.66&enemy_y=49.99&enemy_base=1.57&enemy_move=6&enemy_threat=2&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`

For each route, verify:

- One `<svg class="map-svg">` exists.
- The page contains one form and zero `<script>` tags.
- Default route renders a `safe-zone-outline`, friendly `model-base`, and enemy
  `threat-source-base`.
- Threat-inclusive modes render a `threat-projection-image`.
- LOS-inclusive modes render a `coverage-image`.
- Warning copy explicitly says the result is estimated and is not a placement planner.
- Visible copy avoids `legal`, `safe`, `recommended`, `optimal`, `likely`, and `guaranteed`.
- Console warning/error logs for `127.0.0.1:8000` are empty.

The page 9 and page 52 routes are mandatory regression checks because Phase 7 changes
deployment/exposure overlay behavior.

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

- Scope satisfies Phase 7 and does not enter Phase 8-10.
- Readiness and warning semantics prevent false placement-compliance, safe, or recommendation
  claims.
- Exposure and candidate-center geometry are deterministic and source-bounded.
- Web and desktop are thin adapters over the service.
- Browser QA covers the changed web route.
