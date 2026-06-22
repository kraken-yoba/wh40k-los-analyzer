# Phase 10.5 Deployment Map Rendering Housekeeping Plan

Date: 2026-06-22

Goal: centralize deployment exposure map SVG projection while preserving current behavior.

## Task 1: Characterization Tests

- [ ] Add or extend service tests proving:
  - Deployment Exposure and Deployment Scorecard render identical map SVG for identical valid
    deployment inputs and exposure mode.
  - Page 9 and page 52 valid map SVGs match pre-refactor SHA-256 characterization values.
  - Characterized SVGs still include board/base map structure plus `safe-zone-outline`,
    `coverage-image`, `threat-projection-image`, `model-base`, and `threat-source-base`.
  - Blocked scorecard/deployment exposure states omit `safe-zone-outline`, `coverage-image`, and
    `threat-projection-image`.
  - Scorecard toolkit result ids/input hashes are not affected by service rendering refactors.

## Task 2: Refactor

- [ ] Add a private service-layer helper, for example
  `_deployment_exposure_map_svg(payload: DeploymentExposurePayload, *, include_overlays: bool)`.
- [ ] Use the helper from `deployment_exposure_state(...)`.
- [ ] Use the helper from `deployment_scorecard_state(...)`.
- [ ] Do not move geometry into web or desktop adapters.
- [ ] Do not change route/template/desktop copy.

## Task 3: Documentation

- [ ] Update `docs/work-log/player-toolkit-implementation.md` with Phase 10.5 purpose, design
  decision, verification, and review results.

## Task 4: Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Browser QA:

- Launch the local app.
- Open the valid page 9 deployment exposure route:
  `/deployment-exposure?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`.
- Open the valid page 9 deployment scorecard route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los&turn_order=going-first`.
- Open the valid page 52 deployment scorecard route:
  `/deployment-scorecard?packet_id=official-event-companion-page-52&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los&turn_order=going-first`.
- Open the invalid scorecard base route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=0&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-only&turn_order=going-first`.
- Verify each page has the expected heading, zero `<script>` tags, no traceback/internal-error text,
  no console warning/error logs, valid outputs include `safe-zone-outline`, `coverage-image`, and
  `threat-projection-image`, and blocked scorecard output has none of those classes.
- Desktop QA must include a widget harness assertion that Deployment Scorecard renders a non-null
  map pixmap for the valid state and omits tactical overlay classes in the invalid-turn-order state.

## Task 5: Protected Path And Commit

- [ ] Protected-path scan excludes generated/raw/cache/log/build/dist/PDF/database/archive/image
  paths, `.codex`, `.agents`, `data/codex-home*`, auth/session files, credentials, Google Sheet
  exports, screenshots, and copied rules/card text.
- [ ] Keep `AGENTS.md` untracked and unstaged.
- [ ] Commit as one atomic Phase 10.5 housekeeping commit.
