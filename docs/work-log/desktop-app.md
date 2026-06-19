# Desktop App Work Log

## 2026-06-19 - Verified Web MVP Baseline

Branch: `codex/verified-web-app-mvp`

Purpose:

- Define QA workflows for web, desktop development, and packaged Windows builds.
- Preserve a browser-verified web MVP checkpoint before starting the standalone desktop migration.
- Capture design decisions for the Python-first desktop path.

Artifacts added:

- `docs/qa-scenarios.md`
- `docs/desktop-app-research.md`
- `docs/desktop-migration-design.md`

Verification:

- `python -m ruff format --check src tests` - passed, 49 files already formatted.
- `python -m ruff check .` - passed.
- `mypy src` - passed for 32 source files.
- `python -m pytest` - passed, 156 tests.
- `python -m warhammer_companion.cli validate-packets` - passed for all 45 official packets.
- Browser route sweep on `http://127.0.0.1:8047`:
  - Settings renders Codex backend status with no horizontal overflow.
  - Map Data reports 45 packets from 45 layouts and 687/687 visual categorizer results.
  - Viewer page 9 renders `Take and Hold vs Take and Hold - Layout A` with 15 dense and 15 light/review features.
  - Viewer page 20 renders `Take and Hold vs Reconnaissance - Layout C` with 15 dense and 14 light/review features.
  - Viewer page 52 renders `Priority Assets vs Priority Assets - Layout B` with 18 dense and 15 light/review features.
  - Heatmap page 9 renders a raster overlay and 23 safe-zone outlines.
  - LOS Checker page 9 renders a raster overlay and model-base marker.

Polish fixes made during baseline verification:

- Packet selector labels now include both force-disposition matchups and primary-mission source names, so the collapsed select remains understandable.
- Responsive CSS now constrains toolbar controls and grid items to avoid horizontal document overflow in the Codex browser.
- The stylesheet cache key was bumped to ensure browser-visible verification uses the current CSS.

Launch note:

- On this Windows environment, `Start-Process` may fail if both `Path` and `PATH` are present in the process environment. The successful launch normalized the shell-local environment first and then started uvicorn on port `8047`.

## 2026-06-19 - Shared Application Service Layer

Branch: `codex/standalone-windows-desktop-app`

Purpose:

- Move workflow assembly out of the FastAPI route module and into a Python service layer usable by both web and desktop adapters.
- Keep the web UI behavior-preserving while exposing desktop-ready state objects.

Changes:

- Added `warhammer_companion.application.view_models` for screen-neutral state objects.
- Added `WarhammerCompanionService` for settings, map data, viewer, heatmap, LOS checker, ingestion, deletion, packet grouping, and Codex account actions.
- Replaced the web module-owned heatmap LRU with an explicit bounded service-owned cache to avoid instance-method cache retention.
- Refactored `web.server` routes to call the service and keep redirects/templates as web-only concerns.
- Updated web tests to inject services rather than monkeypatching route globals.
- Added direct service tests for packet grouping and heatmap cache behavior.
