# Movement Reach Toolkit QA Pathway

Date: 2026-06-21

## Scope

This pathway proves Phase 5 adds a manual single-model circular-base movement diagnostic without
claiming exact rules-legal movement and without adding roster/profile, coherency, pathfinding,
mission, threat, damage, analytics, AI, or custom JavaScript scope.

## Automated Checks

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_movement_reach_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_movement_reach_toolkit.py tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- Movement geometry and toolkit tests pass.
- Existing application/rendering/web/desktop tests pass.
- Static checks, full tests, packet validation, desktop smoke, and diff whitespace checks pass.

## TDD Red Step

Before implementation, run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_movement_reach_toolkit.py -q
```

Expected:

- The tests fail because movement reach modules and service methods do not exist.

## Browser Manual QA

Launch the local web app on an available loopback port.

Use built-in Browser to verify:

- `/movement-reach` renders a `Movement Reach` page, one SVG map, a movement-envelope overlay, and
  no console warnings or errors.
- `/movement-reach?layout_variant=B&start_x=12&start_y=12&target_x=18&target_y=18&base=1.57&move=6&mode=normal`
  preserves submitted values, selects Layout B, renders one SVG map, and shows endpoint diagnostic
  text with "Estimated 2D geometry" wording and without legal/safe/recommended/optimal/likely
  wording.
- Existing `/viewer`, `/heatmap`, `/los-checker`, `/hidden-coverage`, `/settings`, and `/map-data`
  smoke routes still render without console warnings or errors.

If built-in Browser fails:

- Record the exact Browser blocker.
- Try Computer Use with Firefox as the fallback.
- If both fail, preserve shell HTTP, screenshot, and desktop smoke evidence and mark manual UI QA
  blocked rather than implying it passed.

## Protected-Data And Artifact Checks

Review changed files and verify:

- No official PDFs, roster archives, community catalog files, public spreadsheet exports, processed
  packs, SQLite/database files, generated caches, screenshots, logs, or Codex state files are
  staged.
- No copied rules, card, datasheet, profile, roster, or mission-card text is added.
- `AGENTS.md` remains unstaged unless the user explicitly asks to commit it.

Suggested changed-path scan:

```powershell
$changed = @()
$changed += git diff --name-only
$changed += git diff --cached --name-only
$changed += git ls-files --others --exclude-standard
$changed | Sort-Object -Unique
```

Reject any non-`AGENTS.md` path under generated data/cache/log/build/dist directories or with raw
source/archive/image/database extensions.

## Reviewer Checklist

An autonomous reviewer should approve only if:

- Valid movement reach results are single-model, circular-base, straight-corridor diagnostics and
  are `estimated`, not `trusted`.
- Invalid movement inputs are `blocked` with no overlays.
- Endpoint diagnostics avoid legal/safe/recommended language.
- Dense-feature, board-edge, non-finite input, zero/negative movement, and no-recommendation wording
  checks are covered by tests.
- Web and desktop surfaces call the shared service layer and do not duplicate movement logic.
- No downstream Phase 6-12 behavior is introduced.
