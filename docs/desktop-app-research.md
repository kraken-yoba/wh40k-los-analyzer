# True Desktop App Research Note

Date: 2026-06-18

## Question

Would it be difficult to move the Warhammer Tournament Companion away from the
current local web app/frontend-backend shape into a true Windows/macOS desktop
app, and what stack and migration route should be used?

## Current Codebase Fit

The current repo is in a good position for a desktop migration because the main
product engine is already Python-owned and mostly isolated:

- `domain/`: map packet models and persistence contracts.
- `los/`: visibility and heatmap geometry.
- `rendering/`: current SVG map/overlay rendering.
- `ingestion/`: official PDF download/extraction, packet generation, and review
  artifacts.
- `web/`: FastAPI routes, Jinja templates, static CSS, and forms.

The true desktop migration should keep the first four layers and replace only
the `web/` layer. That makes the work moderate rather than a full rewrite.

The current web MVP also avoids custom frontend JavaScript. This helps because
there is no React/Vite/browser state model to unwind. The main UI concepts are
server-rendered screens and forms, which map cleanly to native widgets.

## Complexity Verdict

Moving to a true desktop app is **moderate complexity for a usable native MVP**
and **high complexity for a polished cross-platform product**.

The reusable Python engine keeps the migration bounded. The difficult work is
not the LOS or ingestion logic; it is rebuilding interaction and presentation:

- Native navigation across Settings, Map Data, Viewer, Heatmap, and LOS Checker.
- Native map rendering and hit testing.
- Drag-to-place model base behavior.
- Background ingestion and heatmap jobs without freezing the UI.
- Native file dialogs and app-data paths.
- Windows/macOS packaging, signing, notarization, and QA.

## Recommended Stack

### Primary UI Stack: PySide6 / Qt for Python

Use **PySide6** as the true desktop UI framework.

Why it fits:

- Mature cross-platform desktop toolkit for Windows and macOS.
- Native windows, menus, dialogs, forms, split views, tabs, and background
  threading support.
- `QGraphicsView` / `QGraphicsScene` are a good match for map-table rendering,
  zooming, panning, selecting terrain, and dragging a model base. Qt documents
  `QGraphicsView` as a widget for displaying a `QGraphicsScene`, with scrollable
  viewport support and transforms for zooming.
- `QSvgWidget` / `QSvgRenderer` can provide a low-risk transition path by
  displaying current SVG output first, before replacing it with native graphics
  scene items.
- `QThreadPool` / `QRunnable` are suitable for ingestion, PDF extraction,
  heatmap generation, and other long-running jobs.

Preferred desktop modules:

- `PySide6.QtWidgets`: shell, navigation, forms, panels, tables.
- `PySide6.QtGui`: painting, colors, actions, icons.
- `PySide6.QtCore`: settings, signals/slots, background jobs.
- `PySide6.QtSvgWidgets` or `PySide6.QtSvg`: transitional SVG display.
- `QGraphicsView` / `QGraphicsScene`: long-term map canvas.

### Keep Existing Domain Stack

Keep these dependencies and modules:

- Shapely for geometry and LOS.
- PyMuPDF for PDF extraction.
- OpenCV/Pillow/NumPy for image/CV extraction.
- Pydantic models for map packet and ingestion contracts.
- Existing tests around `domain`, `los`, `ingestion`, and packet validation.

### Add Desktop Support Dependencies

Recommended additions:

- `PySide6`: native desktop UI.
- `platformdirs`: platform-correct user data/config/cache/log paths. Its docs
  cover Windows `AppData`, macOS `~/Library`, Linux XDG paths, and optional
  directory creation.
- `PyInstaller`: first packaging target. PyInstaller bundles a Python
  application and dependencies into a runnable package without requiring users
  to install Python. It supports Windows/macOS/Linux, but is not a
  cross-compiler, so build Windows packages on Windows and macOS packages on
  macOS.

Later packaging candidates:

- Briefcase: useful if MSI and macOS `.app` packaging becomes the priority. Its
  docs describe support for macOS standalone `.app` and Windows MSI installers.
- Platform signing/notarization tools: required for polished distribution,
  especially macOS.

## Alternatives Considered

### PyWebView

Good for a quick standalone wrapper, but not the target if the goal is to move
away from web architecture. PyWebView explicitly displays HTML content in a
native GUI window and hides the browser-based nature. That is useful as a
short-term packaging bridge, not a true desktop rewrite.

### Briefcase / Toga as Primary UI

Good packaging story, but less attractive for this app's map-heavy interaction
needs. The app needs a custom board canvas, dense overlays, LOS heatmaps, drag
handles, and possibly future annotation layers. Qt has stronger primitives for
that.

### Tkinter

Lowest dependency footprint, but too limited for the expected map/canvas,
styling, long-running jobs, and cross-platform polish.

### Electron / Tauri

Not aligned with the Python-only direction. They would reintroduce a web
frontend architecture and additional JavaScript/Rust tooling.

## Recommended Migration Route

### Phase 1: Extract an Application Service Layer

Create a thin Python service layer that both web and desktop can call:

- `list_packets()`
- `get_packet(packet_id)`
- `delete_packet(packet_id)`
- `run_ingestion()`
- `build_viewer_scene(packet_id)`
- `build_heatmap_scene(packet_id, zone_id, source, offset)`
- `build_los_scene(packet_id, base_center, base_diameter)`

This layer should return domain objects or render-neutral view models, not HTML.

Goal: make FastAPI routes become adapters, not owners of behavior.

### Phase 2: Add a Minimal PySide6 Shell

Add a new desktop entrypoint alongside the web app, for example:

- `src/warhammer_companion/desktop/app.py`
- `src/warhammer_companion/desktop/main_window.py`
- `src/warhammer_companion/desktop/screens/`

First screen should be Map Viewer, because it is read-only and proves packet
loading plus rendering without ingestion or drag complexity.

Use `QSvgWidget` initially to display the existing SVG output. This avoids
rewriting rendering and UI interaction at the same time.

### Phase 3: Native Navigation and Forms

Rebuild the existing screens as native widgets:

- Settings: backend/account state, data path, source status.
- Map Data: packet list, delete, trigger ingestion.
- Viewer: packet selector and map preview.
- Heatmap: packet selector, deployment selector, source mode, offset control.
- LOS Checker: packet selector, base diameter, coordinate controls.

At this stage, map rendering can still be SVG-based.

### Phase 4: Background Jobs

Move ingestion and expensive heatmap generation into Qt background workers.

Use signals to report:

- started
- progress message
- success payload
- validation warnings
- error with traceback/log path

This is critical because PDF/CV ingestion and dense heatmaps should not block
the UI thread.

### Phase 5: Replace SVG With Native Graphics Scene

Once parity exists, migrate map rendering from SVG strings to a native
`QGraphicsScene`.

Suggested scene items:

- Board rectangle.
- Deployment polygons.
- Terrain footprint polygons.
- Dense feature polygons.
- Light/review feature polygons.
- Heatmap raster or polygon layer.
- LOS coverage polygon.
- LOS ray lines.
- Draggable model base item.

This is where the desktop app becomes genuinely better than the current web
MVP: native drag, zoom, pan, hover, selection, and later annotation/editing.

### Phase 6: Desktop Data Paths and Packaging

Use `platformdirs` for:

- raw official PDFs
- processed packets
- review overlays
- logs
- settings/config

Do not depend on repo-relative `data/` in packaged builds.

Package first with PyInstaller:

- one-folder build first for debuggability
- one-file only after startup and binary dependencies are stable
- separate Windows and macOS build jobs

Then evaluate Briefcase/MSI/DMG packaging and signing.

## Suggested File Layout

```text
src/warhammer_companion/
  application/
    services.py
    view_models.py
    paths.py
  desktop/
    app.py
    main_window.py
    workers.py
    canvas/
      board_scene.py
      items.py
      svg_view.py
    screens/
      settings.py
      map_data.py
      viewer.py
      heatmap.py
      los_checker.py
  web/
    server.py
    templates/
```

The `application/` layer is the key migration step. It prevents desktop code
from importing FastAPI routes and prevents web routes from remaining the only
place where workflows are assembled.

## Risk Register

### Packaging Binary Dependencies

OpenCV, NumPy, Shapely, PyMuPDF, Qt, and SSL/cert handling can all create
packaging issues. Start with PyInstaller one-folder builds and automated smoke
tests before attempting polished installers.

### Map Canvas Scope Creep

Rewriting SVG to `QGraphicsScene` too early would slow the migration. Display
current SVG first; only move to native scene once screen parity is real.

### UI Thread Blocking

Ingestion and heatmaps must run off the UI thread. This should be designed
before wiring ingestion buttons into the desktop UI.

### Platform Distribution

macOS notarization and Windows signing are separate from "does the app run".
Treat them as release engineering tasks after a functional packaged prototype.

### Licensing

PySide6/Qt licensing should be reviewed before public distribution. The likely
open-source route is workable, but it should be checked explicitly before
commercial release decisions.

## Decision

The best true-desktop route is:

1. Keep the current Python engine.
2. Introduce an `application/` service layer.
3. Build a PySide6 desktop shell.
4. Use existing SVG rendering as a transitional display path.
5. Migrate map rendering to `QGraphicsScene` after UI parity.
6. Package with PyInstaller first, then evaluate Briefcase/signing for release.

This avoids a full rewrite while still moving decisively away from a web
frontend/backend architecture.

## Sources

- PyInstaller manual: https://pyinstaller.org/en/stable/
- Qt for Python deployment docs: https://doc.qt.io/qtforpython-6/deployment/index.html
- Qt for Python `QGraphicsView`: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsView.html
- Qt for Python `QSvgWidget`: https://doc.qt.io/qtforpython-6/PySide6/QtSvgWidgets/QSvgWidget.html
- Qt for Python `QThreadPool`: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThreadPool.html
- platformdirs docs: https://platformdirs.readthedocs.io/en/latest/
- Briefcase docs: https://briefcase.beeware.org/en/stable/
- pywebview docs: https://pywebview.flowrl.com/
