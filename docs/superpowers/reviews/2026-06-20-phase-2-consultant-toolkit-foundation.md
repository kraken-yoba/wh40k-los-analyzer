# Phase 2 Consultant Review - Toolkit Foundation

Date: 2026-06-20

## Scope

Review the Phase 2 plan for `ToolkitResult`, `MapOverlayLayer`, and minimal `BoardState`
primitives before committing the implementation.

## Consultant Inputs

Architecture consultant:

- Recommended splitting durable contracts by ownership:
  - `BoardState` in `src/warhammer_companion/domain/board_state.py`.
  - `MapOverlayLayer` in `src/warhammer_companion/domain/overlays.py`.
  - `ToolkitResult` in `src/warhammer_companion/application/toolkit.py`.
- Confirmed `ToolkitReadiness` should not reuse Phase 1 `SourceReadiness`.
- Recommended Shapely `BaseGeometry` for Phase 2 overlays and deferring GeoJSON/export
  serialization.
- Recommended adding a service wrapper that produces `ToolkitResult` before SVG projection.

QA consultant:

- Required contract tests for readiness semantics, invalid readiness, blocked-result behavior,
  source/readiness metadata, overlay neutrality, and no recommendation language for non-trusted
  outputs.
- Required board-state tests for no `MapPacket` mutation, missing model positions, missing base
  sizes, and packet JSON round-trip stability.
- Required existing LOS/rendering regression checks.

## Triage

Accepted:

- Split Phase 2 implementation across domain board-state, domain overlays, and application toolkit
  result modules.
- Add `ToolkitResult` validation for invalid readiness, blocked results without block reasons,
  blocked results with overlays, overlay readiness exceeding parent result readiness, and trusted
  results without source refs or passed validation.
- Add `MapOverlayLayer` invalid-readiness validation.
- Add `BoardState.packet_digest` and `map_packet_digest()` so same-id packet content changes are
  detectable.
- Document `BoardState` as a shallow wrapper over the live `MapPacket` plus a content digest.
- Add `los_checker_toolkit_result()` and have `los_checker_state()` project from that payload.
- Add service-level regression tests proving LOS SVG output matches the previous direct-rendering
  path.

Deferred:

- Heatmap and hidden-coverage toolkit wrappers are deferred to later slices. Phase 2 proves the
  pattern with LOS only.
- GeoJSON/export serialization is deferred until export workflows exist.

## Final Status

Approved.
