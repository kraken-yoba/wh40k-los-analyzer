# Phase 3.5 Semantics Identity Hardening QA Pathway

Date: 2026-06-21

## Scope

This QA pathway proves that Phase 3.5 hardens existing Phase 3 contracts without adding roster
import, profile resolution, UI behavior, rendering behavior, or protected data.

## Automated Checks

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py tests\test_board_state.py tests\test_toolkit_contracts.py tests\test_los_toolkit.py tests\test_los_geometry.py tests\test_rendering_svg.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- Phase 3.5 targeted tests pass.
- Existing toolkit/LOS/rendering regressions pass.
- Ruff, mypy, full tests, packet validation, desktop smoke, and diff whitespace checks pass.

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
- No copied rules, card, datasheet, profile, or roster text is added.
- `AGENTS.md` remains unstaged unless the user explicitly asks to commit it.

## Reviewer Checklist

An autonomous reviewer should approve only if:

- Terrain semantics input hashes include provenance-sensitive source refs and freshness.
- Manual model-frame input hashes include all durable audit fields.
- Empty manual footprints cannot appear usable.
- Unsupported hull/custom base shapes cannot create exact-looking geometry records.
- Existing LOS, rendering, packet, web, and desktop behavior remains unchanged except for normal
  result identity changes in the hardened Phase 3 application builders.
