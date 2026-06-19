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

## 2026-06-19 - Native Desktop Shell

Branch: `codex/standalone-windows-desktop-app`

Purpose:

- Add a true Python desktop entrypoint and native PySide6 shell without introducing JavaScript.
- Keep a non-GUI `--smoke-test` path for CI and packaging verification.

Changes:

- Added optional `desktop` and `package` dependencies plus the `warhammer-companion-desktop` console script.
- Added desktop data path helpers that use user-writable packaged app data when frozen and repo-local data during source runs.
- Added a PySide6 main window with Settings, Map Data, Map Viewer, LOS Heatmap, and LOS Checker screens.
- Added a reusable Qt SVG map widget as the transitional desktop rendering path.
- Added a background worker wrapper for long-running desktop actions such as ingestion.
- Added desktop smoke tests for the non-GUI entrypoint.

Verification:

- `python -m warhammer_companion.desktop.app --smoke-test` returned JSON with `status: ok`, 45 packets, and rendered viewer/heatmap/LOS SVG.
- Headless Qt construction with `QT_QPA_PLATFORM=offscreen` created `Warhammer Tournament Companion` with 5 screens.

## 2026-06-19 - Windows Packaging Path

Branch: `codex/standalone-windows-desktop-app`

Purpose:

- Add the Windows standalone build path for a one-folder app, portable zip, and user-friendly installer.
- Make the packaged executable smoke-testable in GitHub Actions.

Changes:

- Added `packaging/pyinstaller/WarhammerTournamentCompanion.spec`.
- Added `packaging/windows/WarhammerTournamentCompanion.iss` for a per-user Inno Setup installer.
- Added `.github/workflows/build-windows-app.yml` with formatting, lint, type, tests, packet validation, PyInstaller build, packaged smoke test, portable zip, Inno Setup build, and artifact uploads.
- Added packaging artifact tests to lock workflow/spec/installer paths.
- Added 45 official packet JSON files as package seed data so standalone builds start with the official layouts instead of the synthetic sample fallback.
- Hardened CI validation to check the packaged seed packet directory directly on clean runners.
- Added an official-data smoke-test gate so packaged builds fail if they fall back to synthetic sample data.
- Desktop source and packaged builds merge bundled seed packets with local user packets, allowing user-generated overrides without hiding missing official layouts.
- Desktop Map Data now keeps bundled seed packets non-deletable and disables ingestion when source PDFs are not available locally.
- Added seed-data provenance notes and a public-release redistribution check.

Verification:

- `ruff format --check src tests` - passed, 69 files already formatted.
- `ruff check .` - passed.
- `mypy src` - passed for 49 source files.
- `python -m warhammer_companion.cli validate-packets --packet-dir src/warhammer_companion/seed_data/map-packets` - passed for all 45 bundled official packets.
- `python -m warhammer_companion.cli validate-packets` - passed for the current processed packet directory.
- `python -m pytest` - passed, 170 tests; one existing Starlette/httpx deprecation warning.
- `pyinstaller --clean --noconfirm packaging/pyinstaller/WarhammerTournamentCompanion.spec` completed and produced `dist/WarhammerTournamentCompanion/WarhammerTournamentCompanion.exe`.
- Packaged smoke test with `--smoke-test --require-official-data --smoke-output` returned exit code 0 and reported 45 bundled seed packets, 45 official packets, and rendered viewer/heatmap/LOS SVG.
- Source desktop smoke test with `--smoke-test --require-official-data` returned exit code 0 and reported the same 45 official packets.
- Headless Qt construction with `QT_QPA_PLATFORM=offscreen` created `Warhammer Tournament Companion` with 5 screens.
- Portable zip creation using `.NET ZipFile.CreateFromDirectory` produced a readable archive with `WarhammerTournamentCompanion.exe` and 45 official seed packet JSON entries.
- Browser route sweep on `http://127.0.0.1:8052`:
  - Viewer page 52 renders an SVG, 16 terrain labels, and no horizontal overflow.
  - Heatmap page 9 with edge offset 12 renders a raster overlay, 23 safe-zone outlines, and no horizontal overflow.
  - Settings renders Codex account status rows without row or page overflow.
  - Map Data reports 45 packets and the pipeline/status content without horizontal overflow.
- Local Inno Setup is not installed; installer compilation is covered by the CI workflow after `choco install innosetup`.

## 2026-06-19 - Player Disposition Layout Selector

Branch: `codex/standalone-windows-desktop-app`

Purpose:

- Replace the long single packet selector with the user-facing tournament workflow: Player A disposition, Player B disposition, then terrain layout A/B/C.
- Keep the implementation Python-first and avoid custom browser JavaScript.

Changes:

- Added shared selector state and packet resolution to `WarhammerCompanionService`.
- Updated the web Viewer, LOS Heatmap, and LOS Checker forms to submit `player_a`, `player_b`, and `layout_variant`.
- Added a reusable PySide6 `PacketSelectorWidget` with live cascading combos for the desktop Viewer, LOS Heatmap, and LOS Checker screens.
- Updated QA docs to make the three-part selector part of the regression contract.

Verification:

- `python -m pytest` - passed, 179 tests; one existing Starlette/httpx deprecation warning.
- `ruff check .` - passed.
- `mypy` - passed for 56 source files.
- `python -m warhammer_companion.cli validate-packets` - passed for all 45 current packets.
- Source desktop smoke test with `--smoke-test --require-official-data` returned exit code 0 and reported 45 official packets.
- `pyinstaller --clean --noconfirm packaging/pyinstaller/WarhammerTournamentCompanion.spec` rebuilt `dist/WarhammerTournamentCompanion/WarhammerTournamentCompanion.exe`.
- Packaged smoke test with `--smoke-test --require-official-data --smoke-output` returned exit code 0 and reported 45 bundled seed packets, 45 official packets, and rendered viewer/heatmap/LOS SVG.
- Refreshed `dist/WarhammerTournamentCompanion-portable.zip`; archive sanity check found `WarhammerTournamentCompanion.exe` and 45 official seed packet JSON entries.
- Browser verification on `http://127.0.0.1:8055`:
  - Viewer resolved Take and Hold / Reconnaissance / Layout C to Event Companion page 20 with no horizontal overflow.
  - Heatmap resolved Priority Assets / Priority Assets / Layout B to Event Companion page 52, rendered one heatmap raster, 23 safe-zone outlines, and retained the 12-inch offset state.
  - LOS Checker resolved the same page-52 selector, rendered one coverage raster and one model base, and had no horizontal overflow.
  - Browser console warning/error log was empty.
