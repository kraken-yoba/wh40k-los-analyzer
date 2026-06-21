# Phase 4.5 Roster Snapshot Housekeeping QA Pathway

Date: 2026-06-21

## Scope

This pathway proves that Phase 4.5 only extracts pure roster snapshot builder behavior and does not
change roster admission, source-trust semantics, UI behavior, rendering behavior, or downstream
toolkit analysis.

## Automated Checks

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_builders.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_builders.py tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_builders.py tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py tests\test_toolkit_contracts.py tests\test_rules_sources.py tests\test_base_sizes.py tests\test_terrain_semantics.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- The new direct builder tests pass.
- Existing Phase 4A and 4B roster tests pass unchanged.
- Focused toolkit/source/base/terrain regressions pass.
- Ruff, mypy, full tests, packet validation, desktop smoke, and diff whitespace checks pass.

## TDD Red Step

Before implementation, run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_builders.py -q
```

Expected:

- The test fails because `warhammer_companion.application.roster_snapshots` does not exist.

## Browser Manual QA

Launch the local web app on an available loopback port.

Use built-in Browser to verify:

- `/viewer` renders a map SVG and terrain labels.
- `/heatmap` renders a map SVG and embedded PNG heatmap.
- `/los-checker` renders a map SVG, embedded PNG, and clear/blocked result text after form submit.
- `/hidden-coverage` renders a map SVG, embedded PNG, and terrain labels after form submit.
- `/settings` renders forms without console errors.
- `/map-data` renders packet-management forms without console errors.

If built-in Browser fails:

- Record the exact Browser error.
- Try Computer Use with Firefox as the fallback.
- If both fail, preserve shell HTTP, screenshot, and desktop smoke evidence and mark manual UI QA
  blocked rather than implying it passed.

## Protected-Data And Artifact Checks

Review changed files and verify:

- No official PDFs, roster archives, community catalog files, public spreadsheet exports, processed
  packs, SQLite/database files, generated caches, screenshots, logs, or Codex state files are
  staged.
- No copied rules, card, datasheet, profile, or roster text is added beyond tiny synthetic test
  strings.
- `AGENTS.md` remains unstaged unless the user explicitly asks to commit it.

Suggested scan:

```powershell
git diff --name-only
git diff --cached --name-only
rg -n "\.pdf|\.rosz|\.ros|\.catz|\.cat|\.gstz|\.gst|sqlite|\.db|data/raw|data/processed|data/cache|codex-home|screenshot|\.png|\.jpg|\.jpeg|\.webp" docs src tests
```

## Reviewer Checklist

An autonomous reviewer should approve only if:

- The extraction is behavior preserving.
- `application.roster_import` remains the only byte-admission entrypoint.
- The extracted builder API does not imply profile resolution, points authority, legality, or
  tactical recommendation.
- Direct builder tests cover deep source refs, index/candidate markers, and snapshot hash identity.
- Existing roster safety and snapshot profile tests still pass.
