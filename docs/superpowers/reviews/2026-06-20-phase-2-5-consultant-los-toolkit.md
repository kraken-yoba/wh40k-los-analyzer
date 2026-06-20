# Phase 2.5 Consultant Review - LOS Toolkit Extraction

Date: 2026-06-20

## Scope

Review whether a behavior-preserving housekeeping extraction is warranted after Phase 2.

## Consultant Findings

Approved.

- `WarhammerCompanionService` mixed packet selection/view projection with LOS toolkit payload,
  hash, warning, assumption, and overlay construction.
- Moving only LOS toolkit construction into `application.los_toolkit` is low risk and keeps the
  service as the adapter-facing facade.
- The service should still own packet selection and `clamp_base_center()`.

## Triage

Accepted:

- Add `src/warhammer_companion/application/los_toolkit.py`.
- Add `tests/test_los_toolkit.py`.
- Keep the scope tight: no changes to toolkit/domain contracts, LOS geometry, SVG rendering,
  heatmap, hidden coverage, routes, desktop code, or UI.

## Final Status

Approved.
