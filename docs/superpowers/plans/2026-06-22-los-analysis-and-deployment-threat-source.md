# LOS Analysis And Deployment Threat Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan
> task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one switchable Line of Sight surface and add deployment-zone source regions to the
Threat Range tool.

**Architecture:** The Line of Sight change is a facade over existing heatmap and checker services.
The Threat Range change adds source-region movement and threat geometry in `los/`, then threads the
new source mode through service, web, desktop, and rendering adapters.

**Tech Stack:** Python 3.12, FastAPI/Jinja, PySide6, Shapely, Pillow/numpy SVG raster rendering,
pytest, Ruff, mypy.

---

## Decisions

- Use `/los` as the canonical web route.
- Keep `/heatmap` and `/los-checker` as redirect compatibility routes.
- Do not compute heatmap and checker outputs together in `los_analysis_state(...)`.
- Add deployment-zone source mode only to Threat Range in this slice.
- Use `allowed_deployment_center_region(...)` and dense endpoint collision subtraction to build
  source center regions.
- Use multi-source route-distance fields for non-mobile deployment-zone source movement.
- Render deployment-zone threat source as `threat-source-region`, not `threat-source-base`.

## Task 1: Add Failing Tests For LOS Facade And Compatibility Routes

**Files:**

- Modify: `tests/test_application_service.py`
- Modify: `tests/test_web_server.py`
- Modify: `tests/test_desktop_app.py`

- [ ] **Step 1: Add service facade tests**

Add tests that call `service.los_analysis_state(mode="heatmap")` and
`service.los_analysis_state(mode="checker")` using a counting subclass. The heatmap case must call
`_render_heatmap_svg(...)` once and must not call `los_checker_toolkit_result(...)`. The checker
case must call `los_checker_toolkit_result(...)` once and must not call `_render_heatmap_svg(...)`.

- [ ] **Step 2: Add web route tests**

Add tests for:

- `GET /los?mode=heatmap` returns 200, heatmap controls, `heatmap-image`, and no `<script>`.
- `GET /los?mode=checker` returns 200, checker controls, `coverage-image`, and no `<script>`.
- primary web navigation contains one `Line of Sight` link to `/los` and does not contain separate
  `LOS Heatmap` or `LOS Checker` links.
- `GET /heatmap?...` returns 303 to `/los?mode=heatmap...`.
- `GET /los-checker?...` returns 303 to `/los?mode=checker...`.
- `POST /los` preserves both heatmap and checker values in redirects.
- old `POST /los-checker` redirects to `/los?mode=checker...`.

- [ ] **Step 3: Add desktop nav tests**

Update desktop tests to expect one `Line of Sight` nav item and no `LOS Heatmap` or `LOS Checker`
nav items. Add a test that switches the Line of Sight screen between checker and heatmap modes and
confirms both render non-null pixmaps.

- [ ] **Step 4: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py::test_los_analysis_state_delegates_to_heatmap_without_rendering_checker tests\test_application_service.py::test_los_analysis_state_delegates_to_checker_without_rendering_heatmap tests\test_web_server.py::test_los_analysis_route_renders_heatmap_mode tests\test_web_server.py::test_los_analysis_route_renders_checker_mode tests\test_desktop_app.py::test_desktop_line_of_sight_screen_renders_both_modes -q
```

Expected: fail because `los_analysis_state`, `/los`, and `LineOfSightScreen` do not exist.

## Task 2: Implement LOS Facade, Web Route, And Desktop Screen

**Files:**

- Modify: `src/warhammer_companion/application/view_models.py`
- Modify: `src/warhammer_companion/application/services.py`
- Modify: `src/warhammer_companion/web/server.py`
- Create: `src/warhammer_companion/web/templates/los_analysis.html`
- Modify: `src/warhammer_companion/web/templates/base.html`
- Create: `src/warhammer_companion/desktop/screens/los_analysis.py`
- Modify: `src/warhammer_companion/desktop/main_window.py`
- Modify: `src/warhammer_companion/desktop/app.py`

- [ ] **Step 1: Add `LosAnalysisState`**

Create a frozen dataclass with:

```python
@dataclass(frozen=True)
class LosAnalysisState:
    mode: str
    modes: list[str]
    heatmap: HeatmapState | None
    checker: LosCheckerState | None
    packet: MapPacket
    packet_groups: list[PacketSelectGroup]
    packet_selector: PacketSelectorState
    map_svg: str
```

- [ ] **Step 2: Add `WarhammerCompanionService.los_analysis_state(...)`**

Normalize mode to `heatmap` unless it is exactly `checker`. Delegate only the active mode and return
the active mode's packet selector and SVG.

- [ ] **Step 3: Add canonical `/los` and redirects**

Implement `GET /los`, `POST /los`, compatibility `GET /heatmap`, compatibility `GET /los-checker`,
and update old `POST /los-checker`.

- [ ] **Step 4: Add `los_analysis.html`**

Use a mode select and Jinja conditionals to render only active mode controls. No custom JavaScript.

- [ ] **Step 5: Add desktop `LineOfSightScreen`**

Use one packet selector, one mode combo, heatmap controls, checker controls, and one map widget.
Hide/show controls by mode with Qt widget visibility.

- [ ] **Step 6: Update nav and smoke summary**

Replace desktop nav entries with `Line of Sight`. Keep smoke summary keys `heatmap_svg` and
`los_svg` by calling the service states directly so packaging smoke remains compatible.

- [ ] **Step 7: Verify GREEN**

Run the Task 1 command again. Expected: pass.

## Task 3: Add Failing Tests For Deployment-Zone Threat Source

**Files:**

- Modify: `tests/test_threat_range_geometry.py`
- Modify: `tests/test_threat_range_toolkit.py`
- Modify: `tests/test_rendering_svg.py`
- Modify: `tests/test_application_service.py`
- Modify: `tests/test_web_server.py`
- Modify: `tests/test_desktop_app.py`

- [ ] **Step 1: Add geometry tests**

Add tests that prove:

- `threat_projection_regions_from_source_region(...)` exists;
- raw deployment-zone source equals a base-center source region buffered by base radius plus threat
  range;
- deployment-zone source ignores point coordinates;
- zero-move source-region movement returns the endpoint-clear source region;
- dense-ignoring profiles buffer the source region by effective movement and subtract endpoint
  blockers;
- non-mobile profiles can route from a source region around dense blockers through a multi-source
  route field;
- ground-mobile or Hover can threaten a point through dense traversal where non-mobile cannot;
- penalized Fly differs from Hover under the same source region and target point.

- [ ] **Step 2: Add toolkit tests**

Add tests that prove:

- point source mode stays estimated;
- deployment-zone source mode stores `source_mode="deployment-zone"`;
- invalid source mode blocks;
- invalid source deployment zone blocks;
- source zone id changes the input hash;
- source coordinates do not change the deployment-zone hash;
- deployment-zone mode stays estimated when `source_x/source_y` are omitted or invalid;
- point source mode still blocks invalid or out-of-board source coordinates;
- valid deployment zones that become empty after base erosion or dense endpoint collision return
  blocked with no overlays;
- raw deployment-zone output is movement-profile invariant.

- [ ] **Step 3: Add rendering, web, and desktop tests**

Add tests for `threat-source-region`, source-mode form fields, GET/POST preservation, and desktop
combo population.

- [ ] **Step 4: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py tests\test_threat_range_toolkit.py tests\test_rendering_svg.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
```

Expected: fail because deployment-zone source primitives and fields do not exist.

## Task 4: Implement Source-Region Movement And Threat Geometry

**Files:**

- Modify: `src/warhammer_companion/domain/threat.py`
- Modify: `src/warhammer_companion/los/movement.py`
- Modify: `src/warhammer_companion/los/threat.py`
- Modify: `src/warhammer_companion/application/threat_range.py`
- Modify: `src/warhammer_companion/application/services.py`

- [ ] **Step 1: Add threat source domain fields**

Add `ThreatSourceMode = Literal["point", "deployment-zone"]`, `THREAT_SOURCE_MODES`, and payload
fields for source mode, selected source deployment zone id, source center region, and source label.

- [ ] **Step 2: Add `movement_envelope_from_region(...)`**

Implement continuous-region movement for profiles that ignore dense traversal and multi-source
Dijkstra for non-mobile routing. Reuse endpoint blocker policy and routing budget exceptions.
Include a stable source-region digest in cache keys so different deployment zones cannot collide.

- [ ] **Step 3: Add `threat_projection_regions_from_source_region(...)`**

Use source-region buffering for raw range and source-region movement envelope for move-plus-range
modes.

- [ ] **Step 4: Thread source mode through toolkit builder**

Update `build_threat_range_toolkit_result(...)` to accept `source_mode` and
`source_deployment_zone_id`. Use deployment-zone source geometry only when the source mode is valid
and the zone exists. Keep point mode behavior stable.

- [ ] **Step 5: Verify geometry and toolkit GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py tests\test_threat_range_toolkit.py -q
```

Expected: pass.

## Task 5: Thread Source Mode Through Rendering, Web, And Desktop

**Files:**

- Modify: `src/warhammer_companion/rendering/svg.py`
- Modify: `src/warhammer_companion/application/view_models.py`
- Modify: `src/warhammer_companion/application/services.py`
- Modify: `src/warhammer_companion/web/server.py`
- Modify: `src/warhammer_companion/web/templates/threat_range.html`
- Modify: `src/warhammer_companion/desktop/screens/threat_range.py`

- [ ] **Step 1: Render `threat-source-region`**

Add optional `threat_source_region` to `render_map_svg(...)` and render it before terrain labels.

- [ ] **Step 2: Extend `ThreatRangeState`**

Expose source mode options, deployment-zone options, selected source deployment zone id, and source
label.

- [ ] **Step 3: Update web route/template**

Add `source_mode` and `source_deployment_zone_id` to GET/POST and template controls. Preserve point
source fields for point mode.
Add web tests for `/threat-range?source_mode=deployment-zone...` and point mode that assert no
`<script>` tag.

- [ ] **Step 4: Update desktop screen**

Add source-mode and deployment-zone combos. Populate zone options from state. Pass selected values
to the service.

- [ ] **Step 5: Verify adapter GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rendering_svg.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
```

Expected: pass.

## Task 6: Documentation, Manual QA, Review, And Commit

**Files:**

- Modify: `README.md`
- Modify: `docs/qa-scenarios.md`
- Modify: `docs/work-log/player-toolkit-implementation.md`

- [ ] **Step 1: Update docs**

Document `/los`, old route redirects, the desktop `Line of Sight` screen, and Threat Range
deployment-zone source mode.

- [ ] **Step 2: Run manual QA**

Execute the QA pathway in
`docs/superpowers/qa/2026-06-22-los-analysis-and-deployment-threat-source-qa.md`. Attempt built-in
Browser first, then Computer Use plus Firefox if Browser fails, then rendered-route fallback.

- [ ] **Step 3: Run adversarial implementation review**

Reviewer must return `APPROVED` or `CHANGES_REQUIRED`. Fix all required issues before final
validation.

- [ ] **Step 4: Run full validation**

Run the final validation commands from the QA document.
Include targeted page smoke tests for deployment-zone threat projection on
`official-event-companion-page-9` and `official-event-companion-page-52`.

- [ ] **Step 5: Protected-artifact scan and commit**

Stage only intended source/docs/tests. Do not stage `AGENTS.md` or generated artifacts. Commit with:

```text
Add unified LOS surface and deployment threat source
```
