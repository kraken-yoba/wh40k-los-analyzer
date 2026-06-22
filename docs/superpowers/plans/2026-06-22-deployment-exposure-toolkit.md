# Phase 7 Deployment Exposure Toolkit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 7 manual deployment exposure diagnostic toolkit without adding placement
optimization, placement-compliance claims, or mission-aware recommendations.

**Architecture:** Add typed domain records for exposure diagnostics, an application-layer
`ToolkitResult` builder that composes existing LOS/threat/deployment geometry, then expose it through
the shared service, server-rendered web route, and PySide6 desktop screen. Rendering should reuse
existing SVG hooks unless a focused test proves a missing overlay contract.

**Tech Stack:** Python 3.12, Shapely, FastAPI/Jinja, PySide6, pytest, Ruff, mypy.

---

## File Map

- Create: `src/warhammer_companion/domain/exposure.py`
- Create: `src/warhammer_companion/los/exposure.py`
- Create: `src/warhammer_companion/application/deployment_exposure.py`
- Modify: `src/warhammer_companion/application/services.py`
- Modify: `src/warhammer_companion/application/view_models.py`
- Modify: `src/warhammer_companion/web/server.py`
- Create: `src/warhammer_companion/web/templates/deployment_exposure.html`
- Modify: `src/warhammer_companion/web/templates/base.html`
- Create: `src/warhammer_companion/desktop/screens/deployment_exposure.py`
- Modify: `src/warhammer_companion/desktop/main_window.py`
- Modify: `src/warhammer_companion/desktop/app.py`
- Modify: `README.md`
- Modify: `docs/qa-scenarios.md`
- Modify: `docs/work-log/player-toolkit-implementation.md`
- Create/modify tests listed below.

## Task 1: Domain And Geometry Builder

- [ ] Add failing tests in `tests/test_deployment_exposure_toolkit.py` for:
  - valid manual placement returns `estimated`;
  - invalid friendly base diameter blocks with no overlays;
  - a friendly base inside threat/LOS is marked exposed under selected assumptions;
  - a friendly base outside risk and inside the selected deployment zone is marked not exposed under
    selected assumptions;
  - output text fields avoid `legal`, `safe`, `recommended`, `optimal`, `likely`, and `guaranteed`.
- [ ] Add `domain/exposure.py` with:
  - `ExposureMode = Literal["threat-only", "los-only", "threat-or-los", "threat-and-los"]`;
  - `EXPOSURE_MODES`;
  - `ExposureDiagnosticReason`;
  - `ExposurePlacementDiagnostic`;
  - `DeploymentExposurePayload`.
- [ ] Add `los/exposure.py` with focused geometry helpers:
  - `allowed_deployment_center_region(...)`;
  - `exposure_risk_region(...)`;
  - `candidate_staging_center_region(...)`.
- [ ] Add `application/deployment_exposure.py` with
  `build_deployment_exposure_toolkit_result(...)`.
- [ ] Reuse:
  - `base_center_region(...)` and `dense_movement_collision_regions(...)` from
    `los.movement`;
  - `circular_base(...)` and `visibility_polygon_from_base(...)` from `los.geometry`;
  - `threat_projection_regions(...)`, `threat_projection(...)`, and
    `target_threat_probability(...)` from `los.threat`.
- [ ] Define risk region:
  - `threat-only`: max threat region;
  - `los-only`: enemy LOS region;
  - `threat-or-los`: union of threat and LOS;
  - `threat-and-los`: intersection of threat and LOS.
- [ ] Define candidate staging center region as selected deployment-zone candidate centers
  intersected with board-fit centers, minus dense collision centers, minus
  `risk_region.buffer(friendly_radius)`.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py -q
```

## Task 2: Service State And Rendering Integration

- [ ] Add failing tests in `tests/test_application_service.py` and `tests/test_rendering_svg.py`
  proving the service returns an SVG with:
  - one `safe-zone-outline` SVG class from the existing outline renderer, while visible copy uses
    "candidate staging" or "not exposed under selected assumptions";
  - one `coverage-image` when LOS is included;
  - one `threat-projection-image` when threat is included;
  - one `model-base`;
  - one `threat-source-base`.
- [ ] Add `DeploymentExposureState` to `application/view_models.py`.
- [ ] Import the builder and domain modes in `application/services.py`.
- [ ] Add `deployment_exposure_toolkit_result(...)`.
- [ ] Add `deployment_exposure_state(...)`, rendering:
  - no overlays when blocked;
  - `coverage_polygon=payload.enemy_los_region` when mode includes LOS;
  - `threat_regions=payload.enemy_threat_regions` when mode includes threat;
  - `safe_regions=payload.candidate_center_region`;
  - `base_center=payload.friendly_center`;
  - `base_diameter=payload.friendly_base_diameter`;
  - `threat_source_center=payload.enemy_source_center`;
  - `threat_base_diameter=payload.enemy_base_diameter`.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_rendering_svg.py -q
```

## Task 3: Web Route

- [ ] Add failing tests in `tests/test_web_server.py` for:
  - GET `/deployment-exposure` renders controls, warnings, map SVG, no `<script>`;
  - POST preserves manual values in the redirect query;
  - visible copy avoids `legal`, `safe`, `recommended`, `optimal`, `likely`, and `guaranteed`
    claims.
- [ ] Add GET and POST handlers in `web/server.py`.
- [ ] Add navigation link in `web/templates/base.html`.
- [ ] Create `web/templates/deployment_exposure.html` with a form matching the service state.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_web_server.py -q
```

## Task 4: Desktop Screen

- [ ] Add failing tests in `tests/test_desktop_app.py` for:
  - main window includes `Deployment Exposure`;
  - screen renders a non-null pixmap;
  - desktop smoke includes `deployment_exposure_svg: true`.
- [ ] Create `desktop/screens/deployment_exposure.py` following the existing Threat Range screen
  pattern.
- [ ] Add the screen to `desktop/main_window.py`.
- [ ] Add smoke state to `desktop/app.py`.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

## Task 5: Documentation, QA, And Commit

- [ ] Update `README.md` and `docs/qa-scenarios.md` with the new route/screen and QA expectation.
- [ ] Update `docs/work-log/player-toolkit-implementation.md` with Phase 7 decisions, TDD, review,
  validation, Browser QA, and blockers.
- [ ] Run full validation:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

- [ ] Run Browser QA:
  - `/deployment-exposure` default route;
  - one query path using `threat-and-los`;
  - page 9 regression route:
    `/deployment-exposure?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=6&enemy_threat=2&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`;
  - page 52 regression route:
    `/deployment-exposure?packet_id=official-event-companion-page-52&deployment_zone_id=defender&friendly_x=29.34&friendly_y=10.00&friendly_base=1.57&enemy_x=14.66&enemy_y=49.99&enemy_base=1.57&enemy_move=6&enemy_threat=2&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`;
  - confirm SVG, `safe-zone-outline`, expected raster classes, cautious warning text, no
    `<script>`, no forbidden claim wording, and no warning/error console logs.
- [ ] Protected-path scan excludes generated/raw/PDF/credential artifacts and keeps `AGENTS.md`
  unstaged.
- [ ] Commit:

```powershell
git commit -m "Add exposure deployment toolkit"
```
