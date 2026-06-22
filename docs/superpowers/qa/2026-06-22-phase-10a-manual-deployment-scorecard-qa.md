# Phase 10A Manual Deployment Scorecard QA Pathway

Date: 2026-06-22

## Scope

This QA proves Phase 10A adds a manual deployment scorecard that reuses existing deployment exposure
diagnostics and mission-pack context without adding legal placement, optimization, or mission
scoring claims.

Forbidden visible-text claims for this slice: `legal`, `safe`, `optimal`, `recommended`, `likely`,
`guaranteed`, `preferred`, and `pairing`. Checks scan user-visible text, not CSS class names or SVG
ids inherited from shared renderers.

All coordinates, base diameters, move distances, and threat ranges are battlefield inches. A 40 mm
base is represented as `1.57`, not `40`.

## Automated Checks

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

Expected:

- Valid manual scorecards are `estimated`, not `trusted`.
- Invalid manual inputs are `blocked`.
- Invalid turn-order input is `blocked`, includes `invalid-turn-order`, and produces no overlays.
- Component records include deployment fit, exposure, mission readiness, and turn-order limitation.
- Component records use ids `deployment-fit`, `selected-exposure`, `mission-readiness`, and
  `turn-order-assumption`; assessments are only `checked`, `warning`, or `blocked`.
- No aggregate score, rank, grade, best label, or placement recommendation is emitted.
- The builder reuses deployment exposure and mission-pack context.
- Web and desktop tests pass.
- Desktop smoke reports `deployment_scorecard_estimate: true`.
- Existing page 9/page 52 deployment exposure regression coverage remains in the focused app batch;
  this slice does not edit geometry, terrain, LOS, deployment-zone rendering, or mission-zone
  rendering code.

## Browser QA

Open with the built-in Browser:

- `/deployment-scorecard`
- valid going-first route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-only&turn_order=going-first`
- valid going-second route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=los-only&turn_order=going-second`
- invalid base route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=0&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-only&turn_order=going-first`
- invalid turn-order route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-only&turn_order=alpha-strike`

Verify:

- heading `Deployment Scorecard`;
- one form on interactive routes;
- component scorecard is visible;
- mission-readiness and turn-order assumption warnings are visible;
- zero `<script>` tags;
- no traceback/internal-error text;
- no forbidden visible-text claims;
- no console warning/error logs.
- valid form submission redirects and preserves values;
- invalid base submission renders blocked messages;
- invalid turn-order route renders blocked messages;
- blocked output has no tactical overlays: the base terrain SVG may still be present, but
  `safe-zone-outline`, `coverage-image`, and `threat-projection-image` must be absent.

## Desktop QA

- Run `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test`.
- Run the desktop test harness for `DeploymentScorecardScreen`.
- Verify the user-visible screen state contains the heading, component scorecard,
  mission-readiness warning, turn-order warning, and invalid-turn-order blocked message without
  opening a native window.

## Protected-Path Scan

Reject generated data/cache/log/build/dist paths, raw PDFs, images, screenshots, Google Sheet
exports, database/archive files, `.codex`, `.agents`, `data/codex-home*`, auth/session files,
credentials, other Codex/OpenAI state, and copied mission-card/rules text. Keep `AGENTS.md`
untracked and unstaged unless explicitly requested.
