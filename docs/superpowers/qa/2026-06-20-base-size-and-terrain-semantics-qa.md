# Base Size And Terrain Semantics QA

Date: 2026-06-20

## Autonomous QA Path

Run from repository root:

```powershell
Resolve-Path .
git status --short --branch
.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py tests\test_board_state.py tests\test_toolkit_contracts.py tests\test_los_toolkit.py tests\test_los_geometry.py tests\test_rendering_svg.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
git diff --name-only
```

## Built-In Browser Manual QA

Run the local web app:

```powershell
.\.venv\Scripts\python.exe -m warhammer_companion.app
```

Then use the built-in browser to inspect `http://127.0.0.1:8000` and verify:

- The app loads without server errors.
- Main navigation links render and route correctly.
- Map Viewer renders an official packet SVG.
- LOS Checker renders a coverage SVG after submitting a base position.
- Hidden Coverage renders a hidden-coverage SVG/raster on page 9.
- Page 52 can be selected and rendered in the viewer as a complex packet smoke case.
- No Phase 3 base-size or terrain-semantics internals leak into existing user-facing UI because no
  UI surface is intended for them yet.

## Required Manual Checks

- Confirm `AGENTS.md` remains unstaged unless the user explicitly asks to stage it.
- Confirm no official PDFs, mission-card images, roster exports, community catalog data, raw public
  sheet exports, or copied rules passages were added.
- Confirm changed production code is confined to Phase 3 contract/adapter modules:
  `src/warhammer_companion/domain/semantics.py`,
  `src/warhammer_companion/domain/base_sizes.py`,
  `src/warhammer_companion/domain/terrain_semantics.py`,
  `src/warhammer_companion/application/base_sizes.py`, and
  `src/warhammer_companion/application/terrain_semantics.py`.
- Confirm existing LOS toolkit, rendering, web, and desktop behavior were not changed.
- Confirm manual base data is `estimated`, unknown base data is `blocked`, and neither can allow
  legal/safe trusted claim wording.
- Confirm terrain semantics are adapted from `MapPacket` without mutating it.

## Protected Content Scan

Run:

```powershell
rg -n --glob '!docs/superpowers/qa/2026-06-20-base-size-and-terrain-semantics-qa.md' --glob '!docs/work-log/player-toolkit-implementation.md' "mission card|datasheet|verbatim|Warhammer 40,000 Core Rules|Munitorum Field Manual" src tests docs\superpowers
```

Expected: no new protected content matches outside documentation that names source families without
copying protected text.

## Browser And Computer Use

Required for Phase 3 closeout because the user requested built-in-browser manual QA. Computer Use is
not required unless the built-in browser cannot inspect the local app or a desktop-only issue is
found.
