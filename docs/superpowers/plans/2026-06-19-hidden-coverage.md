# Hidden Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Hidden Coverage screen that shows where enemy models threaten hidden models inside a selected terrain footprint, colored by the fraction of sampled footprint points exposed.

**Architecture:** Reuse the existing Python LOS geometry and SVG rendering path. The geometry layer samples the selected terrain footprint, removes dense blocker interiors from the hidden-model sample area, intersects normal LOS with the hidden detection range, and emits exposure cells. The service, web UI, and desktop UI consume one shared `HiddenCoverageState`.

**Tech Stack:** Python, Shapely, Pillow/numpy SVG raster overlays, FastAPI/Jinja templates, PySide6 desktop shell, pytest.

---

### Task 1: Geometry Contract

**Files:**
- Modify: `tests/test_los_geometry.py`
- Modify: `src/warhammer_companion/los/geometry.py`

- [ ] **Step 1: Write the failing tests**

Add tests that import `hidden_coverage_from_terrain_area`, then assert:
- a point at the selected footprint edge has higher exposure than a point at the detection-range edge;
- dense blockers inside the selected footprint reduce exposure behind the blocker;
- range 18 produces more threat cells than range 12.

- [ ] **Step 2: Run RED**

Run: `pytest tests/test_los_geometry.py -k hidden_coverage -q`

Expected: FAIL because `hidden_coverage_from_terrain_area` does not exist.

- [ ] **Step 3: Implement minimal geometry**

Add `HiddenCoverageCell`, `HiddenCoverageResult`, `hidden_coverage_from_terrain_area`, and small private helpers for selected terrain lookup, hidden sample area, and point-grid accumulation.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/test_los_geometry.py -k hidden_coverage -q`

Expected: PASS.

### Task 2: SVG Rendering

**Files:**
- Modify: `tests/test_rendering_svg.py`
- Modify: `src/warhammer_companion/rendering/svg.py`
- Modify: `src/warhammer_companion/web/static/style.css`

- [ ] **Step 1: Write the failing test**

Add a renderer test that passes a `HiddenCoverageResult` to `render_map_svg` and asserts the output contains `class="hidden-coverage-image"`, `class="selected-terrain-area"`, and embedded PNG data.

- [ ] **Step 2: Run RED**

Run: `pytest tests/test_rendering_svg.py -k hidden_coverage -q`

Expected: FAIL because `render_map_svg` has no hidden coverage argument.

- [ ] **Step 3: Implement rendering**

Add a hidden-coverage raster overlay using a green-yellow-red scale where low nonzero exposure is green and high exposure is red. Add selected footprint outline and sample-point markers.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/test_rendering_svg.py -k hidden_coverage -q`

Expected: PASS.

### Task 3: Shared Application State

**Files:**
- Modify: `tests/test_application_service.py`
- Modify: `src/warhammer_companion/application/view_models.py`
- Modify: `src/warhammer_companion/application/services.py`

- [ ] **Step 1: Write the failing test**

Add a test for `hidden_coverage_state` asserting default range 15, range options `[12, 15, 18]`, selected terrain option, and hidden coverage SVG output.

- [ ] **Step 2: Run RED**

Run: `pytest tests/test_application_service.py -k hidden_coverage -q`

Expected: FAIL because `hidden_coverage_state` does not exist.

- [ ] **Step 3: Implement service state**

Add `TerrainSelectOption` and `HiddenCoverageState`. Implement `hidden_coverage_state` with selector support, range clamping to 12/15/18, default first terrain area, and render-map integration.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/test_application_service.py -k hidden_coverage -q`

Expected: PASS.

### Task 4: Web and Desktop UI

**Files:**
- Modify: `tests/test_web_server.py`
- Modify: `tests/test_desktop_app.py`
- Modify: `src/warhammer_companion/web/server.py`
- Create: `src/warhammer_companion/web/templates/hidden_coverage.html`
- Modify: `src/warhammer_companion/web/templates/base.html`
- Modify: `src/warhammer_companion/desktop/main_window.py`
- Create: `src/warhammer_companion/desktop/screens/hidden_coverage.py`
- Modify: `src/warhammer_companion/desktop/app.py`

- [ ] **Step 1: Write failing tests**

Add route tests for `/hidden-coverage` and desktop smoke assertions for hidden coverage SVG output.

- [ ] **Step 2: Run RED**

Run: `pytest tests/test_web_server.py tests/test_desktop_app.py -k hidden_coverage -q`

Expected: FAIL because the route and desktop state do not exist.

- [ ] **Step 3: Implement UI**

Add the web route/template and desktop screen with player disposition selector, terrain footprint selector, range slider/options, and shared rendered SVG map.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/test_web_server.py tests/test_desktop_app.py -k hidden_coverage -q`

Expected: PASS.

### Task 5: Verification and Checkpoint

**Files:**
- Modify as needed from previous tasks.

- [ ] **Step 1: Run focused tests**

Run: `pytest tests/test_los_geometry.py tests/test_rendering_svg.py tests/test_application_service.py tests/test_web_server.py tests/test_desktop_app.py -q`

- [ ] **Step 2: Run full tests**

Run: `pytest -q`

- [ ] **Step 3: Browser check**

Launch or reuse the local app and open `/hidden-coverage` in the built-in browser. Verify selector controls, range controls, terrain selector, and rendered heatmap are present.

- [ ] **Step 4: Commit and push**

Run: `git status --short`, `git add ...`, `git commit -m "Add hidden coverage heatmap"`, and `git push`.
