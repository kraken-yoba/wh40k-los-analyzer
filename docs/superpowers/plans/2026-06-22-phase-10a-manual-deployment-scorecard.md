# Phase 10A Manual Deployment Scorecard Plan

Date: 2026-06-22

Goal: add a manual deployment scorecard surface that reuses existing deployment exposure diagnostics
without claiming a placement is legal, safe, optimal, recommended, likely, guaranteed, preferred,
or useful for pairing decisions.

Forbidden-word checks scan user-visible text only. Existing implementation-only CSS/SVG tokens such
as `safe-zone-outline` are not treated as visible copy.

## Task 1: Toolkit Tests

- [ ] Add `tests/test_deployment_scorecard_toolkit.py` with failing tests for:
  - result readiness `estimated`, tool id `deployment_scorecard`, and no recommendation language;
  - explicit turn-order assumption values `going-first` and `going-second`;
  - invalid turn-order input returns `blocked`, block reason `invalid-turn-order`, user-facing block
    reasons, and no overlays;
  - component records with ids `deployment-fit`, `selected-exposure`, `mission-readiness`, and
    `turn-order-assumption`;
  - component assessments are only `checked`, `warning`, or `blocked`;
  - no aggregate score, rank, grade, best label, or placement recommendation is emitted;
  - mission-pack readiness is included as source-pending/estimated context;
  - invalid manual placement input returns a blocked scorecard with deployment exposure block
    reasons and no tactical overlays;
  - identity changes when turn order or manual footprint inputs change.

## Task 2: Domain And Builder

- [ ] Add `domain/deployment_scorecard.py` with typed payload/component records.
- [ ] Add `application/deployment_scorecard.py`:
  - call `build_deployment_exposure_toolkit_result(...)`;
  - call `build_mission_pack_toolkit_result(...)` for context;
  - validate turn order as `going-first` or `going-second` before producing estimated output;
  - derive component records and warnings;
  - return `estimated` only when turn order is valid and deployment exposure is not blocked;
  - return `blocked` when either turn-order validation or deployment exposure validation fails;
  - avoid legal/safe/optimal/recommended/likely/guaranteed/preferred/pairing wording.

## Task 3: Service And UI Adapters

- [ ] Add `DeploymentScorecardState` to `application/view_models.py`.
- [ ] Add `deployment_scorecard_toolkit_result(...)` and `deployment_scorecard_state(...)` to the
  shared service.
- [ ] Add GET/POST web route `/deployment-scorecard`, template, and navigation link.
- [ ] Add desktop `DeploymentScorecardScreen`, navigation entry, and smoke key
  `deployment_scorecard_estimate`.

## Task 4: Documentation And QA

- [ ] Update `README.md` route list.
- [ ] Update `docs/qa-scenarios.md` with a Deployment Scorecard scenario.
- [ ] Update `docs/work-log/player-toolkit-implementation.md` with Phase 10A purpose, decisions,
  verification, and review results.

## Task 5: Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_scorecard_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_scorecard_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Browser QA:

- Launch the local app.
- Open `/deployment-scorecard`.
- Open the valid going-first route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-only&turn_order=going-first`.
- Open the valid going-second route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=los-only&turn_order=going-second`.
- Open the invalid base route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=0&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-only&turn_order=going-first`.
- Open the invalid turn-order route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-only&turn_order=alpha-strike`.
- Submit the form with valid values and confirm the redirected URL preserves all values.
- Submit invalid base values and confirm the route renders `blocked` messages with no tactical
  overlays. Invalid turn-order is verified through the exact route because the select control only
  exposes supported values.
- Verify heading, one form, component scorecard, mission/turn-order warnings, zero `<script>` tags,
  no traceback/internal-error text, no forbidden visible-text claims, no console warning/error logs,
  and no tactical overlay on blocked output.
- Browser overlay assertion: for blocked output, the base terrain SVG may still be present, but
  `safe-zone-outline`, `coverage-image`, and `threat-projection-image` must be absent.
- Desktop manual verification: run the smoke test and instantiate the `Deployment Scorecard`
  screen through the desktop test harness to confirm heading, component text, turn-order warning,
  and invalid-turn-order blocked state without opening a native window.
- Page 9/page 52 regression: retain the existing deployment exposure/web/desktop tests in the
  focused batch. This slice reuses that geometry/rendering path and does not edit geometry,
  terrain, LOS, deployment-zone, or mission-zone rendering modules.

## Task 6: Protected Path And Commit

- [ ] Protected-path scan excludes generated/raw/cache/log/build/dist/PDF/database/archive/image
  paths, `.codex`, `.agents`, `data/codex-home*`, auth/session files, credentials, other
  Codex/OpenAI state, Google Sheet exports, screenshots, and card text.
- [ ] Keep `AGENTS.md` untracked and unstaged.
- [ ] Commit as one atomic Phase 10A commit.
