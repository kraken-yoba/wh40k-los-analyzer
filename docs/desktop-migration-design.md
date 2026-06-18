# Desktop Migration Design

Date: 2026-06-18

## Goal

Move the Warhammer Tournament Companion from a local server-rendered web MVP toward a true standalone Windows desktop app while preserving the Python LOS, ingestion, rendering, and domain engine.

## Design Brief

- Preserve the existing MVP workflows: Settings, Map Data, Map Viewer, LOS Heatmap, and LOS Checker.
- Keep the app Python-focused. Avoid JavaScript/TypeScript in the desktop migration.
- Keep the web MVP as a verified baseline during migration.
- Use the current Python engine as the shared implementation of map packets, official ingestion, LOS, heatmaps, and SVG rendering.
- Build a Windows desktop v1 that can be packaged and launched without requiring the user to install Python.
- Treat cross-platform support as an architecture constraint, but build and verify Windows first.

## Recommended Approach

Use a true PySide6 desktop app with a shared Python application service layer.

The desktop app should not import FastAPI routes. Instead, both web routes and desktop widgets should call `warhammer_companion.application` services. The service layer owns repository access, ingestion orchestration, packet selection, map rendering, heatmap rendering, LOS rendering, cache invalidation, and sanitized backend status retrieval.

Desktop v1 should display current SVG output through Qt as a transitional rendering path. This keeps parity work bounded and avoids rewriting map rendering, heatmap rasters, drag semantics, and LOS overlays at the same time. Native `QGraphicsScene` rendering should be a later milestone after desktop workflow parity is proven.

## UX And Workflow Scope

### Settings

Show Python backend state and Codex account/runtime state. Desktop should expose login/logout controls only through service methods that preserve the existing credential boundary: the app must not read, render, copy, or bundle user auth files or tokens.

### Map Data

Show official source status, packet list, latest ingestion report, delete controls for generated packets, and an ingestion action. In desktop, ingestion must run through a background worker and report started/progress/success/error state without freezing the UI.

### Map Viewer

Show packet selector, selected packet summary, terrain/dense/light/deployment counts, and map preview. Desktop v1 can use the existing SVG map output.

### LOS Heatmap

Show packet selector, deployment zone selector, source mode, offset control, and rendered heatmap. Desktop must use the same service call and cache invalidation semantics as web.

### LOS Checker

Show packet selector, base coordinates, base diameter, rendered coverage, and base marker. Desktop v1 can use form-driven coordinate updates; native drag can follow once the map display moves from SVG bridge to `QGraphicsScene`.

## Application Service Layer

Create `src/warhammer_companion/application/` with:

- `paths.py`: application data path resolution using development defaults and installed-app user-data paths.
- `services.py`: `WarhammerCompanionService` with methods for settings status, packet listing, packet deletion, ingestion, viewer rendering, heatmap rendering, and LOS rendering.
- `view_models.py`: small dataclasses for screen-neutral responses such as packet groups, viewer state, heatmap state, LOS checker state, and operation results.

The service should accept injected `IngestionPaths`, repository, and Codex backend instances. This removes current web module-global ownership and gives desktop tests a clean seam.

## Desktop Architecture

Create `src/warhammer_companion/desktop/` with:

- `app.py`: desktop launcher, `--smoke-test`, and `--version`.
- `main_window.py`: top-level window, navigation, and screen container.
- `workers.py`: Qt background job wrapper for ingestion and other long-running tasks.
- `screens/`: one module per workflow.
- `widgets/svg_map.py`: transitional SVG map widget.

Use PySide6:

- `QtWidgets` for shell, forms, panels, tables, splitters, and buttons.
- `QtSvgWidgets` or `QtSvg` for SVG display in v1.
- `QtCore` signals/slots and `QThreadPool` for background jobs.

## Windows Packaging

Use PyInstaller one-folder builds first.

Reasons:

- It is easier to debug missing DLLs, Qt plugins, package data, and Codex runtime binaries.
- One-file builds have slower startup and more extraction edge cases.
- Windows and macOS must be built on their respective operating systems; GitHub Actions should build Windows artifacts on `windows-latest`.

Package artifacts:

- Portable `WarhammerTournamentCompanion` one-folder zip.
- Inno Setup installer wrapping the one-folder build.

Installer defaults:

- Per-user install under `%LOCALAPPDATA%\Programs\WarhammerTournamentCompanion`.
- Start Menu shortcut by default.
- Optional desktop shortcut.
- No admin rights required for MVP.
- Do not bundle user credentials.
- Do not bundle official PDFs until distribution/licensing is explicitly reviewed.

## Data Paths

Installed builds should use platform-correct user data directories via `platformdirs`.

Development mode can keep repo-relative `data/` defaults when running from source. Portable builds can support a local writable `data/` directory next to the executable if it exists and is writable.

The service layer should ensure generated data, logs, raw PDFs, processed packets, and Codex state are not written into the read-only installed app directory.

## CI Build Path

Add a GitHub Actions workflow named `Build windows app`.

The Windows job should:

1. Check out the repo.
2. Set up Python 3.12.
3. Install `.[dev,desktop,package]`.
4. Run `ruff format --check src tests`.
5. Run `ruff check .`.
6. Run `mypy src`.
7. Run `pytest`.
8. Build with a committed PyInstaller spec.
9. Run `WarhammerTournamentCompanion.exe --smoke-test`.
10. Zip the one-folder dist.
11. Compile the Inno Setup installer.
12. Upload the portable zip and installer as artifacts.

## Key Risks And Mitigations

- **Web owns workflow globals today.** Mitigate by extracting `application` services before desktop screens.
- **SVG bridge may not render exactly like the browser.** Mitigate with page 9/page 52 visual smoke checks and keep native `QGraphicsScene` as the planned long-term renderer.
- **Long-running ingestion can freeze UI.** Mitigate by requiring Qt workers before wiring ingestion controls.
- **Repo-relative `data/` breaks installed apps.** Mitigate by adding app-path service and installed-user-data paths before packaging.
- **PyInstaller may miss Qt/Codex/OpenCV/Shapely/PyMuPDF assets.** Mitigate with a committed `.spec`, smoke tests, and one-folder builds first.
- **Codex state and runtime are sensitive.** Mitigate by packaging dependencies, not user credentials, and retaining sanitized status display.
- **Unsigned Windows installer may trigger SmartScreen.** Accept for internal MVP; track signing as a release hardening item.

## Decisions

- Keep the web app during migration.
- Add a shared application service layer before desktop screens.
- Use PySide6 for the true desktop app.
- Use existing SVG rendering for desktop v1.
- Use PyInstaller `onedir` before one-file builds.
- Use Inno Setup for the first friendly Windows installer.
- Build Windows artifacts in GitHub Actions on Windows.
- Defer macOS packaging, code signing, notarization, and native map-canvas rewrite until the Windows desktop MVP path is proven.

## Verification Strategy

The QA scenarios in `docs/qa-scenarios.md` are the contract. The current web MVP must be verified first and treated as the baseline. Desktop implementation must then pass the same scenarios, with explicit notes where desktop-specific rendering differs but underlying packet/LOS/heatmap semantics match.
