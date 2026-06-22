# Threat Range Toolkit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first manual estimated threat range toolkit slice with deterministic probability-band geometry and dice distribution summaries.

**Architecture:** Keep threat mechanics in typed domain/application modules and geometry in `los/`, mirroring Phase 5 movement reach. Web and desktop remain thin adapters over `WarhammerCompanionService`, and rendering extends the existing SVG/raster pipeline with a stable threat projection layer.

**Tech Stack:** Python 3.12, Shapely, NumPy/Pillow SVG raster helpers, FastAPI/Jinja, PySide6, pytest, Ruff, mypy.

---

## File Map

- Create: `src/warhammer_companion/domain/threat.py`
- Create: `src/warhammer_companion/los/threat.py`
- Create: `src/warhammer_companion/application/threat_range.py`
- Modify: `src/warhammer_companion/application/services.py`
- Modify: `src/warhammer_companion/application/view_models.py`
- Modify: `src/warhammer_companion/rendering/svg.py`
- Modify: `src/warhammer_companion/web/server.py`
- Modify: `src/warhammer_companion/web/templates/base.html`
- Create: `src/warhammer_companion/web/templates/threat_range.html`
- Modify: `src/warhammer_companion/web/static/style.css`
- Modify: `src/warhammer_companion/desktop/app.py`
- Modify: `src/warhammer_companion/desktop/main_window.py`
- Create: `src/warhammer_companion/desktop/screens/threat_range.py`
- Create: `tests/test_threat_range_geometry.py`
- Create: `tests/test_threat_range_toolkit.py`
- Modify: `tests/test_application_service.py`
- Modify: `tests/test_rendering_svg.py`
- Modify: `tests/test_web_server.py`
- Modify: `tests/test_desktop_app.py`
- Modify: `docs/work-log/player-toolkit-implementation.md`

## Task 1: Threat Domain And Geometry

- [ ] Write failing tests in `tests/test_threat_range_geometry.py` for raw range clipping,
  move-plus-range using dense movement blockers, D6/2D6 distributions, and invalid inputs.
- [ ] Run those tests and confirm missing modules fail.
- [ ] Add `domain/threat.py` records:
  - `ThreatMode`
  - `ThreatDiceOutcome`
  - `ThreatRangePayload`
  - `ThreatProjectionRegion`
  - `coerce_threat_mode(...)`
- [ ] Add `los/threat.py` helpers:
  - `threat_projection(...)`
  - `threat_projection_regions(...)`
  - `threat_distribution(...)`
  - `threat_reach_probability(...)`
  - `target_threat_probability(...)`
  - positive finite base validation and nonnegative finite movement/threat validation.
- [ ] Verify the new geometry tests pass.

## Task 2: Toolkit Result

- [ ] Write failing tests in `tests/test_threat_range_toolkit.py` for estimated readiness, blocked
  invalid input, warning language, input hash identity including measurement convention, and no
  recommendation language.
- [ ] Run tests and confirm missing application builder fails.
- [ ] Implement `application/threat_range.py` with `build_threat_range_toolkit_result(...)`.
- [ ] Verify toolkit tests pass.

## Task 3: Service And Rendering

- [ ] Write failing application/rendering tests:
  - `WarhammerCompanionService.threat_range_toolkit_result(...)`.
  - `WarhammerCompanionService.threat_range_state(...)`.
  - `render_map_svg(..., threat_regions=..., threat_source_center=..., threat_base_diameter=...)`
    emits `threat-projection-image`, `threat-source-base`, and `threat-target-point`.
- [ ] Run focused tests and confirm missing methods/parameters fail.
- [ ] Implement service state and rendering support.
- [ ] Verify application/rendering tests pass.

## Task 4: Web And Desktop Adapters

- [ ] Write failing web route tests for `/threat-range` controls, cautious copy, target-point
  measurement convention, target probability, value preservation, no scripts, and
  `threat-projection-image`.
- [ ] Write failing desktop tests for smoke summary `threat_range_svg`, target probability state, and
  screen pixmap rendering.
- [ ] Implement route/template/static CSS and desktop screen/nav/smoke summary.
- [ ] Verify web and desktop focused tests pass.

## Task 5: Review, QA, And Commit

- [ ] Update work log with design decisions, reviewer outcomes, TDD, validation, Browser QA, and
  remaining blocker status.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py tests\test_threat_range_toolkit.py tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

- [ ] Run built-in Browser QA for `/threat-range`, `/movement-reach`, `/los-checker`, `/viewer`,
  `/heatmap`, `/hidden-coverage`, `/settings`, and `/map-data`.
- [ ] Protected-path scan confirms no generated/raw/Codex/credential artifacts and `AGENTS.md`
  unstaged.
- [ ] Stage Phase 6 files and commit with `git commit -m "Add threat range toolkit"`.
