# Phase 2.5 Housekeeping - LOS Toolkit Extraction

Date: 2026-06-20

## Status

Draft housekeeping spec after Phase 2.

Parent roadmap: `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`

## Goal

Keep the Phase 2 toolkit foundation behavior-preserving while reducing `WarhammerCompanionService`
growth before Phase 3.

This housekeeping slice extracts LOS checker toolkit-result construction from
`src/warhammer_companion/application/services.py` into a focused application module.

## Scope

Add:

- `src/warhammer_companion/application/los_toolkit.py`
- `tests/test_los_toolkit.py`

Modify:

- `src/warhammer_companion/application/services.py`
- `docs/work-log/player-toolkit-implementation.md`

## Non-Goals

This slice must not:

- Change LOS geometry semantics, SVG output, route behavior, desktop behavior, or user-facing UI.
- Add movement, base-size, terrain-semantics, roster, mission, damage, or AI logic.
- Change `ToolkitResult`, `BoardState`, or `MapOverlayLayer` public behavior.
- Add custom JavaScript, TypeScript, or new frontend architecture.

## Architecture

`application.services` should remain the workflow facade for web and desktop adapters. It should
select packets and project toolkit payloads to view models, but LOS toolkit-specific hashing,
payload construction, assumptions, warnings, and overlay creation should live in a smaller module.

`application.los_toolkit` owns:

- `LOS_CHECKER_TOOLKIT_SCHEMA_VERSION`
- `LosCheckerToolkitPayload`
- `build_los_checker_toolkit_result(packet, center, base_diameter)`

The service remains responsible for:

- packet selection
- coordinate clamping
- calling `build_los_checker_toolkit_result()`
- rendering `LosCheckerState` from the returned payload

## Acceptance Criteria

- New module-level tests prove `build_los_checker_toolkit_result()` returns the same toolkit
  identity, readiness, payload, overlay, warning, and input-hash behavior as Phase 2.
- Existing service tests still prove `los_checker_toolkit_result()` wraps analysis before SVG
  projection and does not mutate `MapPacket`.
- Existing service tests still prove `los_checker_state()` matches the direct legacy rendering
  path.
- Ruff, mypy, focused tests, and full pytest pass.
- Browser and Computer Use checks remain not required because no UI/runtime surface changes.

## Design Decisions

### Decision 1: Extract only the LOS builder

Heatmap and hidden coverage wrappers are not implemented yet. Extracting only LOS keeps this
housekeeping slice behavior-preserving and avoids inventing abstractions before other toolkit
builders exist.

### Decision 2: Service keeps clamping

The service currently owns user-input normalization for `los_checker_state()`. Keeping clamping in
the service preserves that boundary and lets future toolkit builders receive canonicalized inputs.
