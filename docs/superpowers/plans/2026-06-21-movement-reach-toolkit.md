# Movement Reach Toolkit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a manual single-model circular-base 2D Movement Reach toolkit with service, SVG, web,
and desktop surfaces while avoiding rules-legal claims.

**Architecture:** Put pure movement geometry under `los/movement.py`, durable movement records under
`domain/movement.py`, toolkit assembly under `application/movement_reach.py`, and UI state through
`WarhammerCompanionService`. Web and desktop code remain thin adapters.

**Tech Stack:** Python 3.12, Shapely, FastAPI/Jinja, PySide6, pytest, Ruff, mypy.

---

## File Structure

- Create: `src/warhammer_companion/los/movement.py`
  - Single-model circular-base movement-envelope and endpoint diagnostic geometry.
- Create: `src/warhammer_companion/domain/movement.py`
  - Movement mode, endpoint diagnostic, and payload records.
- Create: `src/warhammer_companion/application/movement_reach.py`
  - `ToolkitResult` builder and movement input hashing.
- Modify: `src/warhammer_companion/application/services.py`
  - Add movement reach toolkit/state methods.
- Modify: `src/warhammer_companion/application/view_models.py`
  - Add `MovementReachState`.
- Modify: `src/warhammer_companion/rendering/svg.py`
  - Add movement overlay rendering.
- Modify: `src/warhammer_companion/web/server.py`
  - Add `/movement-reach` GET and POST routes.
- Modify: `src/warhammer_companion/web/templates/base.html`
  - Add Movement Reach nav item.
- Create: `src/warhammer_companion/web/templates/movement_reach.html`
  - Server-rendered form and map view.
- Modify: `src/warhammer_companion/web/static/style.css`
  - Add movement overlay styles.
- Create: `src/warhammer_companion/desktop/screens/movement_reach.py`
  - PySide6 Movement Reach screen.
- Modify: `src/warhammer_companion/desktop/main_window.py`
  - Add Movement Reach nav item.
- Modify: `src/warhammer_companion/desktop/app.py`
  - Include movement SVG in smoke summary.
- Create: `tests/test_movement_reach_geometry.py`
  - Geometry tests.
- Create: `tests/test_movement_reach_toolkit.py`
  - Toolkit result tests.
- Modify: `tests/test_application_service.py`
  - Service/rendering integration tests.
- Modify: `tests/test_rendering_svg.py`
  - Movement overlay rendering tests.
- Modify: `tests/test_web_server.py`
  - Web route and no-JS tests.
- Modify: `tests/test_desktop_app.py`
  - Desktop smoke/screen tests.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Phase 5 work-log entry.

## Task 1: Write Failing Tests

- [ ] **Step 1: Add geometry tests**

Create `tests/test_movement_reach_geometry.py` proving:

- movement envelopes respect board-edge base radius;
- movement envelopes exclude dense-feature buffered collision regions;
- endpoint diagnostics block target points beyond movement distance;
- endpoint diagnostics block dense-feature swept-corridor collisions;
- endpoint diagnostics allow an in-range clear target.

- [ ] **Step 2: Add toolkit tests**

Create `tests/test_movement_reach_toolkit.py` proving:

- valid manual inputs return an `estimated` result with a movement overlay and no recommendation
  language;
- invalid base diameter or movement distance returns a `blocked` result with no overlays;
- input identity changes for packet content, start, target, base, move distance, and mode.

- [ ] **Step 3: Add adapter test expectations**

Extend service/web/desktop/rendering tests for the new movement state, route, SVG classes, nav item,
and desktop smoke key.

- [ ] **Step 4: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_movement_reach_toolkit.py -q
```

Expected: FAIL because movement modules do not exist.

## Task 2: Implement Movement Engine And Toolkit Result

- [ ] **Step 1: Add domain records**

Add movement mode, endpoint diagnostic, and payload dataclasses in `domain/movement.py`. Keep the
records single-model and circular-base only.

- [ ] **Step 2: Add movement geometry**

Implement `movement_envelope(...)` and `movement_endpoint_diagnostic(...)` in
`los/movement.py` with Shapely board, base-radius, dense-feature, and swept-corridor checks.
Do not add pathfinding, coherency, or non-round base logic.

- [ ] **Step 3: Add toolkit builder**

Implement `build_movement_reach_toolkit_result(...)` in `application/movement_reach.py` with
estimated/block readiness, assumptions, warnings, overlay layer, and stable input hash.

- [ ] **Step 4: Verify targeted tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_movement_reach_toolkit.py -q
```

Expected: PASS.

## Task 3: Add Service, Rendering, Web, And Desktop Surfaces

- [ ] **Step 1: Add service state**

Add `MovementReachState`, `movement_reach_toolkit_result(...)`, and `movement_reach_state(...)`.

- [ ] **Step 2: Add SVG projection**

Render reachable region, start base, target base, and path line using movement-specific classes.

- [ ] **Step 3: Add web adapter**

Add `/movement-reach` GET/POST, nav link, and Jinja template. Use forms only; no custom JS.

- [ ] **Step 4: Add desktop adapter**

Add Movement Reach PySide screen and include movement SVG in smoke summary.

- [ ] **Step 5: Verify adapter tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q
```

Expected: PASS.

## Task 4: Review, Full QA, And Commit

- [ ] **Step 1: Run focused regression**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_movement_reach_toolkit.py tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q
```

Expected: PASS.

- [ ] **Step 2: Run static checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
```

Expected: all pass.

- [ ] **Step 3: Run implementation reviews**

Reviewers must check false-precision wording, source/readiness boundaries, single-model circular-base
scope, geometry limits, web and desktop thinness, and absence of later-phase scope.

- [ ] **Step 4: Run full validation and Browser QA**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Then run Browser QA for `/movement-reach` and existing route smokes. If Browser fails, try Computer
Use with Firefox and record the blocker.

- [ ] **Step 5: Protected-artifact scan and commit**

Confirm no raw official/community/roster/mission data, generated artifacts, logs, screenshots,
databases, Codex state, or `AGENTS.md` are staged.

Commit message:

```text
Add phase 5 movement reach toolkit
```
