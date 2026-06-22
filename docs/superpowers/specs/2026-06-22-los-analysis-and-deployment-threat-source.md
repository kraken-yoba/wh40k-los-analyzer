# LOS Analysis And Deployment Threat Source Spec

Date: 2026-06-22

## Goal

Merge the LOS Checker and LOS Heatmap player surfaces into one switchable Line of Sight tool, and
extend Threat Range so the threat source can be either a point model position or an inferred
deployment-zone source area.

The result should make the app more useful as a player toolkit while preserving the Python-first
engine, server-rendered web MVP, and PySide6 desktop adapter boundaries.

## Source Context

Existing app surfaces:

- `/heatmap` renders deployment-zone visibility density through `WarhammerCompanionService`.
- `/los-checker` renders a point/base LOS check through `WarhammerCompanionService`.
- `/threat-range` renders point-source threat projection with movement-profile-aware routing.
- Desktop currently has separate `LOS Heatmap`, `LOS Checker`, and `Threat Range` nav entries.

Consultant review produced two recommendations:

- The LOS merge should be a thin application/UI facade. Keep existing heatmap and checker engines
  intact and add one switchable state and adapter surface.
- Deployment-zone threat should be a real source-region geometry primitive. Do not fake it by
  sampling a few source points or by pretending the selected deployment zone is one source base.

## Product Behavior

### Line Of Sight Surface

Add one canonical Line of Sight surface with two modes:

- `checker`: place one circular model base and render binary visible-area coverage plus sampled LOS
  rays.
- `heatmap`: render visibility density from sampled deployment positions, with the existing
  deployment edge/full deployment zone source controls and edge offset.

The active mode is selected by a server-rendered form field or desktop combo. The inactive mode's
stale query parameters are ignored deliberately.

Compatibility:

- `/los` is the canonical web route.
- The primary web navigation exposes one `Line of Sight` link to `/los`; old LOS links are
  compatibility routes only and are not shown as separate player surfaces.
- old `/heatmap` GET redirects to `/los?mode=heatmap` while preserving heatmap query parameters.
- old `/los-checker` GET redirects to `/los?mode=checker` while preserving checker query
  parameters.
- old `POST /los-checker` redirects to `/los?mode=checker` while preserving submitted values.

Desktop:

- Replace separate `LOS Heatmap` and `LOS Checker` nav entries with one `Line of Sight` screen.
- The screen uses one packet selector, one mode selector, mode-specific controls, and one SVG map.
- The old screen classes may remain as compatibility internals only if they are no longer exposed
  as separate windows/nav entries.

Hidden Coverage remains separate in this slice.

### Deployment-Zone Threat Source

Threat Range gets a source mode:

- `point`: current behavior using `source_x` and `source_y`.
- `deployment-zone`: source centers are inferred from the selected deployment zone for the selected
  circular source base.

For deployment-zone source mode:

- The source center region is the selected deployment zone eroded by the source base radius,
  intersected with board-fit center space, and cleared of dense endpoint occupancy collision.
- A selected deployment zone that becomes empty after base erosion, board-fit intersection, or dense
  endpoint collision subtraction returns `blocked` with no tactical overlays.
- Point source coordinates are ignored and are not required in deployment-zone source mode.
- `raw-range` buffers that source center region by `base_radius + threat_range`.
- move-plus-range modes use the existing movement profile semantics from the movement engine:
  - ground non-mobile routes around dense traversal blockers;
  - ground mobile ignores dense traversal blockers;
  - Fly Take to the Skies applies the existing 2 inch effective-move penalty;
  - Hover/no-cost Fly keeps the unpenalized effective move.
- The output remains estimated. It must not claim exact legal movement, exact deployment legality,
  safety, recommendations, or matchup advantage.

Rendering:

- Point source mode keeps the existing source-base marker.
- Deployment-zone source mode renders a source-area outline/overlay instead of a misleading
  single source-base marker.
- Threat probability raster semantics stay unchanged: each dice outcome contributes by probability.

### Scope Boundary For Downstream Exposure

This slice does not extend Deployment Exposure or Deployment Scorecard to deployment-zone enemy
source mode. Those tools combine enemy threat with enemy LOS from a point. Reusing a point LOS source
while showing deployment-zone threat would mislead the player. A later slice can add explicit
separate source semantics for threat and LOS, or a deployment-area LOS estimator.

## Architecture

### Application Layer

Add a facade state in `src/warhammer_companion/application/view_models.py`:

- `LosAnalysisState`
- active mode id and mode options;
- optional `HeatmapState`;
- optional `LosCheckerState`;
- shared packet selector state from the active mode.

Add `WarhammerCompanionService.los_analysis_state(...)` in
`src/warhammer_companion/application/services.py`. It normalizes `mode` and delegates to
`heatmap_state(...)` or `los_checker_state(...)`. It must not compute both modes per request.

Threat Range service and payload additions:

- source mode id and options;
- selected deployment-zone id and deployment-zone options;
- source center region and source label in the payload;
- source region geometry in rendering for deployment-zone mode;
- input identity includes source mode, selected source zone id, source-region policy, movement
  profile, effective move, routing metadata, and packet digest.

### LOS Geometry Layer

Add reusable geometry under `src/warhammer_companion/los/`:

- `movement_envelope_from_region(...)` in `los/movement.py` for route-connected envelopes from a
  source center region.
- `threat_projection_regions_from_source_region(...)` in `los/threat.py` for deployment-zone source
  projection.

The region movement implementation should share the same deterministic routing constraints as the
point movement implementation. For non-mobile routing, use a multi-source route-distance field whose
initial nodes are the valid route nodes inside the source region.

Required source-region movement behavior:

- zero movement returns the source center region after endpoint-occupancy subtraction;
- dense-ignoring profiles buffer the source center region by effective move distance and then apply
  endpoint-occupancy subtraction;
- non-mobile profiles build one multi-source Dijkstra field seeded by all visible route nodes inside
  the source region and threshold that field by effective move distance;
- routing budget overflow returns a blocked toolkit result instead of raising to the UI;
- route-field cache keys include packet geometry, base radius, profile id, routing resolution, and a
  stable source-region digest.

### Rendering Layer

Extend `render_map_svg(...)` with an optional threat source region geometry. Render it as an outline
or light fill using stable CSS class names. Do not render `threat-source-base` in deployment-zone
source mode unless a point source is also selected.

### Web Adapter

Add `src/warhammer_companion/web/templates/los_analysis.html`.

Update `src/warhammer_companion/web/server.py`:

- canonical `GET /los`;
- compatibility redirects for `/heatmap` and `/los-checker`;
- `POST /los` for both modes;
- keep `POST /los-checker` as a compatibility redirect to canonical checker mode;
- add `source_mode` and `source_deployment_zone_id` to Threat Range GET/POST.

No custom JavaScript is allowed.

### Desktop Adapter

Add `src/warhammer_companion/desktop/screens/los_analysis.py`.

Update `src/warhammer_companion/desktop/main_window.py`:

- import the new screen;
- expose one `Line of Sight` nav item;
- remove separate `LOS Heatmap` and `LOS Checker` nav items.

Update Threat Range desktop screen:

- add a source-mode combo;
- add a deployment-zone combo;
- retain point source controls for point mode;
- render a deployment-zone source region when selected.

## Acceptance Criteria

### LOS Surface

- `/los?mode=heatmap` renders the heatmap controls, one SVG map, one heatmap raster, and no custom
  script tags.
- `/los?mode=checker` renders checker controls, one SVG map, coverage raster/rays/base marker, and
  no custom script tags.
- The primary web nav contains one `Line of Sight` link to `/los` and does not contain separate
  `LOS Heatmap` or `LOS Checker` entries.
- `/heatmap` and `/los-checker` redirect to `/los` with the correct mode and preserved values.
- Desktop nav contains `Line of Sight` and no separate `LOS Heatmap` or `LOS Checker` items.
- Desktop Line of Sight screen renders both active modes to non-null pixmaps.

### Deployment-Zone Threat Source

- Threat Range point mode remains compatible with existing point-source results except for the
  expanded source-mode identity fields.
- Deployment-zone source mode returns `estimated` for valid deployment zones and base sizes.
- Invalid source mode or invalid deployment-zone id returns `blocked` without tactical overlays.
- Valid deployment-zone source mode returns `blocked` without tactical overlays when source center
  geometry is empty after erosion/board/dense endpoint constraints.
- Deployment-zone source mode does not require or trust point source coordinates for source geometry.
- Deployment-zone source mode succeeds when point source coordinates are omitted or invalid, while
  point source mode continues to validate point source coordinates.
- The source-zone id changes the input hash and geometry.
- `raw-range` remains movement-profile invariant.
- move-plus-range deployment-zone projections use the selected movement profile, including mobile
  traversal and Fly effective-move penalties.
- Deployment-zone source mode renders a source-region indicator and does not render a single
  `threat-source-base` marker.

### QA And Safety

- Focused service, geometry, web, desktop, and renderer tests cover both features.
- Page 9 and page 52 official seed packets are smoke-tested for deployment-zone threat projection.
- Manual browser QA is attempted through the built-in Browser. If it fails, Computer Use plus
  Firefox is attempted. If both fail, FastAPI route-level rendered checks are recorded as fallback.
- Ruff format check, Ruff lint, mypy, full pytest, packet validation, desktop smoke, and
  `git diff --check` pass before commit.
- Protected-source scan confirms no raw PDFs, generated caches/logs/databases, credentials, Codex
  state, or generated app data are staged.

## Explicit Non-Goals

- No custom frontend JavaScript.
- No exact legal movement/deployment oracle.
- No multi-model unit placement or coherency solver.
- No roster-derived source mode selection.
- No deployment-zone LOS estimator.
- No Deployment Exposure or Deployment Scorecard source-mode changes in this slice.
- No official PDF bundling or protected source asset commits.
