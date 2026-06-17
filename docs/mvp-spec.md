# MVP Spec

## Product Goal

Build a Python-first Warhammer 40,000 tournament companion whose first useful feature is terrain/map line-of-sight analysis.

The MVP is a web app only because it is the fastest local GUI shell. The product engine must remain reusable for a later standalone Python app.

## Hard Constraints

- Python-focused implementation.
- No frontend JavaScript in the MVP.
- Official Games Workshop PDFs are source inputs, not committed assets.
- Map, LOS, and ingestion logic must be isolated from web routes.
- Every visual artifact used by the MVP should be renderable server-side.

## MVP Screens

- Settings: backend and future ChatGPT/Codex integration status.
- Map Data Management: list known map packets, delete placeholder, trigger ingestion placeholder.
- Map Data Viewer: select and inspect current map packet.
- LOS Heatmap: choose source deployment zone and render aggregate visibility.
- LOS Checker: place a model base and render visibility from the base-aware footprint.

## Extraction Pipeline Target

The eventual extraction pipeline has six stages:

1. Download official terrain footprint PDF.
2. Extract exact footprint shapes, identify corners, simplify to snapped polygons, and infer dimensions.
3. Download official event companion layouts PDF.
4. Detect footprint instances on each layout, match against known shapes, and extract stated positional labels.
5. Generate a normalized internal map packet.
6. Run visual sanity review with a capable model.

The initial scaffold includes the source registry and pipeline boundaries, but ships the UI on a hand-authored sample map packet so LOS work can start before CV extraction is robust.

## Internal Map Model

- Coordinates are battlefield inches.
- Origin is the lower-left battlefield corner.
- Standard battlefield is 44" wide by 60" tall.
- Terrain areas are polygons with identifiers and kind labels.
- Dense terrain features are polygons nested on terrain areas.
- Deployment zones are polygons labelled by role.

## LOS Assumption For MVP

The first LOS model treats dense terrain polygons as opaque 2D blockers. A line segment is blocked when it crosses blocker interior outside the viewer base footprint.

This is intentionally narrower than the full Warhammer 40,000 rules. Terrain rules from the core rules PDF should inform later feature flags and rule profiles.

