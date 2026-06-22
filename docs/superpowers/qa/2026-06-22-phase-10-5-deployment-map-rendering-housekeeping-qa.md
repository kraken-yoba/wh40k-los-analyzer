# Phase 10.5 Deployment Map Rendering Housekeeping QA Pathway

Date: 2026-06-22

## Scope

This QA proves Phase 10.5 is a behavior-preserving service-layer refactor for deployment exposure
map SVG projection.

## Automated Checks

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Expected:

- Deployment Exposure and Deployment Scorecard valid state maps match for identical manual
  deployment inputs.
- Page 9 and page 52 valid map SVGs match pre-refactor SHA-256 characterization values.
- Characterized valid SVGs include board/base structure plus `safe-zone-outline`, `coverage-image`,
  `threat-projection-image`, `model-base`, and `threat-source-base`.
- Blocked deployment outputs omit `safe-zone-outline`, `coverage-image`, and
  `threat-projection-image`.
- No scorecard toolkit result identity, warning, block reason, or payload behavior changes.
- Web and desktop tests pass.

## Browser QA

Open with the built-in Browser:

- valid page 9 deployment exposure route:
  `/deployment-exposure?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`
- valid page 9 deployment scorecard route:
  `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los&turn_order=going-first`
- valid page 52 deployment scorecard route:
  `/deployment-scorecard?packet_id=official-event-companion-page-52&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los&turn_order=going-first`
- `/deployment-scorecard?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=0&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=8&enemy_threat=12&enemy_mode=fixed-move-plus-range&exposure_mode=threat-only&turn_order=going-first`

Verify:

- expected headings render;
- zero `<script>` tags;
- no traceback/internal-error text;
- no console warning/error logs;
- valid outputs include `safe-zone-outline`, `coverage-image`, and `threat-projection-image`;
- blocked scorecard output has no `safe-zone-outline`, `coverage-image`, or
  `threat-projection-image`.

## Desktop QA

- `tests\test_desktop_app.py` must assert Deployment Exposure renders a non-null map pixmap.
- `tests\test_desktop_app.py` must assert Deployment Scorecard renders a non-null map pixmap for
  the valid state and that the invalid-turn-order state carries blocker text while omitting
  tactical overlay classes from the state SVG.

## Protected-Path Scan

Reject generated data/cache/log/build/dist paths, raw PDFs, images, screenshots, Google Sheet
exports, database/archive files, `.codex`, `.agents`, `data/codex-home*`, auth/session files,
credentials, other Codex/OpenAI state, and copied mission-card/rules text. Keep `AGENTS.md`
untracked and unstaged unless explicitly requested.
