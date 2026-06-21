# Phase 5.5 Movement Housekeeping Spec

Date: 2026-06-21

## Purpose

Phase 5 added the movement reach toolkit. Phase 5.5 is a behavior-preserving cleanup slice before
Phase 6 threat range work. It reduces small duplication introduced or exposed by the movement slice
without changing player-facing behavior, movement geometry, web routes, desktop navigation, source
authority, or toolkit readiness semantics.

## Scope

This slice may touch only:

- `src/warhammer_companion/desktop/screens/common.py`
- `src/warhammer_companion/desktop/screens/los_checker.py`
- `src/warhammer_companion/desktop/screens/movement_reach.py`
- `src/warhammer_companion/rendering/svg.py`
- focused tests and Phase 5.5 documentation/work-log files

## Design Decisions

### Decision 1: Extract one shared desktop numeric-control helper

`LosCheckerScreen` and `MovementReachScreen` both construct `QDoubleSpinBox` controls with the same
range, decimal, step, and initial-value pattern. Phase 5.5 extracts this into a shared helper in
`desktop/screens/common.py` so future deterministic tools can reuse the same offscreen-tested
control contract.

The helper will not introduce styling, validators, signals, or unit labels. It only centralizes the
existing construction behavior.

### Decision 2: Extract shared binary raster plumbing, not overlay semantics

Phase 5 added `_render_geometry_raster(...)` for movement reach while `_render_coverage_raster(...)`
still carries a near-identical mask/color/image implementation. Phase 5.5 makes coverage rastering
delegate to the shared helper with the existing coverage color and CSS class.

This is intentionally smaller than introducing a full overlay renderer or moving SVG rendering into
new modules. Phase 6 will need more overlay types, but this slice should not change public
`render_map_svg(...)` parameters or overlay ordering.

Heatmap, LOS coverage, hidden coverage, and movement envelope keep separate semantics, class names,
colors, alpha rules, denominators, and render order. The cleanup shares only the binary mask to PNG
plumbing used by coverage and movement envelope rendering.

## Explicit Non-Goals

- No movement, threat, mission, roster, damage, analytics, or AI behavior.
- No new web routes, templates, CSS classes, navigation items, or desktop screens.
- No custom frontend JavaScript.
- No changed SVG class names, colors, raster dimensions, map ordering, or semantic labels.
- No `render_map_svg(...)` API redesign and no generic overlay registry.
- No merge with `desktop/svg_raster.py`, which rasterizes final SVG output for Qt and is a
  different runtime surface.
- No removal of legacy cell-render fallbacks.
- No generated data, raw official sources, screenshots, logs, caches, or credentials.

## Acceptance Criteria

- Desktop LOS and Movement Reach screens use the shared numeric spin-box helper.
- Coverage and movement raster SVG output still contain their existing stable image classes and
  embedded PNG data URIs.
- Decoded PNG tests lock representative alpha/color behavior for heatmap, LOS coverage, hidden
  coverage, and movement envelope raster outputs.
- Existing LOS, movement reach, rendering, web, and desktop tests pass.
- Static checks pass.
- Browser QA confirms the affected rendered surfaces still display maps and overlays with no console
  warnings or errors.
- Consultant and adversarial reviewers approve the slice as behavior-preserving and scoped.
