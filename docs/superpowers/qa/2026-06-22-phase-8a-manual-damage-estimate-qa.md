# Phase 8A Manual Damage Estimate QA Pathway

Date: 2026-06-22

## Scope

This QA proves Phase 8A adds a manual estimated damage math toolkit without claiming roster/profile
authority or source-backed rules resolution.

## Automated Checks

Focused implementation checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py tests\test_application_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_web_server.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_desktop_app.py -q
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

- Exact D6/binomial math matches hand-calculated fixtures.
- Invalid manual inputs are blocked with no overlays. Builder fixtures cover zero attacks,
  negative attacks, non-integer attacks, non-finite attacks, thresholds outside 2+ to 6+,
  target wounds/model less than or equal to zero, non-integer target wounds/model,
  non-finite target wounds/model, target model count less than or equal to zero,
  non-integer target model count, non-finite target model count, negative damage, and
  non-finite damage.
- No result returns `trusted`.
- Warning text says manual estimate, not roster-derived, not official/profile-resolved, effective
  save supplied by user, and unsupported effects omitted.
- Visible/result copy avoids `legal`, `optimal`, `recommended`, `likely`, `target priority`,
  `bad target`, and positive `official`/`profile-resolved` claim wording. Explicit negative wording
  such as `not official/profile-resolved` is expected.

## Browser QA

Launch the local app and inspect with the built-in Browser:

- `/damage-profile`
- `/damage-profile?attacks=2&hit=4&wound=4&save=4&damage=2&wounds=2&models=3`
- `/damage-profile?attacks=0&hit=4&wound=4&save=4&damage=2&wounds=2&models=3`

For each route, verify:

- Page heading is `Damage Profile`.
- One form exists and zero `<script>` tags exist.
- Valid routes show expected hits, wounds, unsaved wounds, damage, models destroyed, and
  distribution rows.
- Invalid route shows blocked reason text and no traceback/internal-error text.
- Warning copy includes manual-estimate trust boundaries.
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

- Slice is named and framed as manual estimated damage math, not roster-aware Phase 8 completion.
- No roster snapshot profile data is read as mechanics authority.
- Save is treated as a manual effective save target, not source-modeled AP/cover/invulnerable
  selection.
- Target wounds/model and target model count are finite positive integers.
- Unsupported effects are omitted and clearly warned.
- Web and desktop are thin adapters over the service.
