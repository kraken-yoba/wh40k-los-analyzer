# LOS Analysis And Deployment Threat Source QA Pathway

Date: 2026-06-22

## Scope

This QA proves the app has one switchable Line of Sight surface and that Threat Range can use a
deployment zone as the source region without weakening movement-profile-aware routing or adding
unsafe claims.

## Automated Checks

Run focused checks during implementation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py::test_los_analysis_state_delegates_to_heatmap_without_rendering_checker tests\test_application_service.py::test_los_analysis_state_delegates_to_checker_without_rendering_heatmap -q
.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py tests\test_threat_range_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py -q -k "deployment_zone_source_page_9 or deployment_zone_source_page_52"
.\.venv\Scripts\python.exe -m pytest tests\test_web_server.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_rendering_svg.py -q
```

Run final validation:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- `/los` supports both modes with no scripts.
- primary web navigation contains one `Line of Sight` link and no separate `LOS Heatmap` or
  `LOS Checker` entries.
- old `/heatmap` and `/los-checker` routes redirect to canonical `/los`.
- Threat Range source mode values persist through GET and POST.
- Deployment-zone threat source uses selected deployment zone geometry, not point source
  coordinates.
- Deployment-zone threat source does not require point source fields and blocks empty source-center
  regions without overlays.
- Deployment-zone source mode renders a source-region indicator, not a single source-base marker.
- Movement profile behavior still affects move-plus-range deployment-zone projection.
- Page 9 and page 52 deployment-zone threat projections render within the automated smoke tests.

## Manual Browser QA

Launch the local app:

```powershell
.\.venv\Scripts\python.exe -m warhammer_companion.app
```

Use the built-in Browser at `http://127.0.0.1:8000`.

Verify Line of Sight:

- Open `/los`.
- Switch to `checker`, enter `x=30.5`, `y=24`, `base=1.57`, submit, and verify the URL contains
  `mode=checker`.
- Confirm the page shows checker controls, one SVG, a `coverage-image`, a model base marker, and no
  `<script>` tag.
- Switch to `heatmap`, choose defender deployment zone, full deployment zone source, submit, and
  verify the URL contains `mode=heatmap`.
- Confirm the page shows heatmap controls, one SVG, a `heatmap-image`, safe-zone outline, and no
  `<script>` tag.
- Open `/heatmap?zone_id=defender&source=interior&offset_inches=0` and verify it redirects to
  `/los?mode=heatmap...`.
- Open `/los-checker?x=30.5&y=24&base=1.57` and verify it redirects to `/los?mode=checker...`.

Verify Threat Range deployment-zone source:

- Open `/threat-range`.
- Select `Deployment zone` source, attacker zone, `fixed-move-plus-range`, `move=6`,
  `threat=2`, `base=1.57`, and `ground-non-mobile`; submit.
- Confirm the page shows source mode and deployment zone controls, one SVG, a
  `threat-projection-image`, a deployment source-region indicator, no `threat-source-base`, and no
  `<script>` tag.
- Change only the source deployment zone to defender and verify the hash or visible map changes.
- Change movement profile to `ground-mobile`, then `fly-take-to-skies`, then
  `fly-hover-take-to-skies`; verify selected values persist and effective movement changes for Fly.
- Switch back to point source and verify the single source-base marker returns.
- Open
  `/threat-range?packet_id=official-event-companion-page-9&source_mode=deployment-zone&source_deployment_zone_id=attacker&target_x=22.5&target_y=32.75&base=1.57&move=9&threat=0.5&mode=fixed-move-plus-range&movement_profile=ground-mobile`
  and verify one SVG plus `threat-projection-image`.
- Open
  `/threat-range?packet_id=official-event-companion-page-52&source_mode=deployment-zone&source_deployment_zone_id=defender&target_x=22.5&target_y=32.75&base=1.57&move=9&threat=0.5&mode=fixed-move-plus-range&movement_profile=ground-mobile`
  and verify one SVG plus `threat-projection-image`.

If Browser control fails:

- Try Computer Use with Firefox against the same local URL.
- If Computer Use is also unavailable, use FastAPI/TestClient route rendering checks and record the
  exact Browser/Computer blockers in the work log.

## Desktop QA

Run:

```powershell
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Use PySide test coverage to verify:

- nav labels contain `Line of Sight`;
- nav labels do not contain `LOS Heatmap` or `LOS Checker`;
- Line of Sight renders checker mode and heatmap mode pixmaps;
- Threat Range source-mode combo includes point and deployment-zone;
- deployment-zone source mode renders a threat map without a point source marker.

If Computer Use desktop inspection is unavailable, record the blocker and rely on PySide offscreen
tests plus the desktop smoke summary.

## Protected-Path Scan

Before staging:

```powershell
$changed = @()
$changed += git diff --name-only
$changed += git diff --cached --name-only
$changed += git ls-files --others --exclude-standard
$changed | Sort-Object -Unique
```

Reject generated data/cache/log/build/dist paths, raw PDFs, roster archives, image/database files,
credentials, Codex state, and unexpected official-source artifacts. Keep `AGENTS.md` untracked and
unstaged unless explicitly requested.

## Reviewer Checklist

- The LOS merge is one player surface, not two nav entries with renamed labels.
- The web implementation is server-rendered and script-free.
- Old URLs preserve player-entered values through redirects.
- Threat deployment-zone source uses source-region geometry and route-aware movement profiles.
- The deployment-zone source renderer does not show a misleading single source base.
- The slice does not silently alter Deployment Exposure or Deployment Scorecard source semantics.
