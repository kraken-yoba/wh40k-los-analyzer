# Threat Range Toolkit QA Pathway

Date: 2026-06-21

## Scope

This QA proves Phase 6 adds only the first manual, estimated threat range toolkit slice. It does not
prove rules-legal threat selection, damage, roster-aware profiles, transport/reserve/action logic,
or matchup analytics.

## Automated Checks

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py tests\test_threat_range_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py tests\test_threat_range_toolkit.py tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- Threat geometry/toolkit tests pass.
- Existing movement/LOS/rendering/web/desktop behavior stays green.
- Static checks, full tests, packet validation, desktop smoke, and diff whitespace pass.

## Browser Manual QA

Launch:

```powershell
.\.venv\Scripts\python.exe -m warhammer_companion.app
```

Use built-in Browser to verify:

- `/threat-range` renders a `Threat Range` page, one SVG map, a `threat-projection-image`, a
  source-base marker, no `<script>` tags, and no console warnings/errors.
- `/threat-range?layout_variant=B&source_x=16&source_y=10&target_x=24&target_y=10&base=1.57&move=6&threat=2&mode=2d6-move-plus-range`
  preserves submitted values, selects Layout B, renders one SVG map, and shows exact dice
  distribution rows for 2D6 totals.
- Visible text includes "Estimated 2D threat projection" and the
  `source-base-edge-to-target-point` measurement convention, and avoids legal, safe, recommended,
  optimal, likely, and guaranteed wording.
- Existing `/viewer`, `/heatmap`, `/los-checker`, `/movement-reach`, `/hidden-coverage`,
  `/settings`, and `/map-data` smoke routes still render without console warnings or errors.

If Browser fails, try Computer Use with Firefox. If both fail, record the exact blocker and do not
claim manual Browser QA passed.

## Protected-Path Scan

Before staging, inspect changed paths:

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

- Valid manual threat results are `estimated`, not `trusted`.
- Invalid manual inputs are `blocked` with no overlays.
- Distribution rows state exactly which dice are modeled.
- Target point probability is deterministic and source-limited by the same distribution shown in the
  table.
- Reach probability helpers cover impossible thresholds, guaranteed thresholds, and monotonic
  threshold probability.
- Unsupported modifiers are visible/disabled by warning language and absent from calculations.
- No recommendation language appears for estimated results.
- Web and desktop adapters call the shared service layer and do not own threat logic.
- No Phase 7-12 behavior is introduced.
