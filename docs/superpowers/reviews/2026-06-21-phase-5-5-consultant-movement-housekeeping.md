# Phase 5.5 Consultant Review - Movement Housekeeping

Date: 2026-06-21

Reviewer: consultant subagent `019eebe6-ce37-7130-9723-f8389d72930a`

## Review Prompt

Review whether Phase 5.5 should be a narrow behavior-preserving cleanup after Movement Reach and
before Phase 6 Threat Range. Candidate scope: shared desktop numeric spin-box helper and SVG raster
helper consolidation. No new player-facing behavior.

## Outcome

Approved. The consultant recommended the narrow slice:

- Add one shared `QDoubleSpinBox` helper in `desktop/screens/common.py`.
- Use it from `los_checker.py` and `movement_reach.py`.
- Make `_render_coverage_raster(...)` delegate to the existing binary `_render_geometry_raster(...)`
  path with the same color and CSS class.

Accepted scope cuts:

- Do not redesign `render_map_svg(...)` movement parameters.
- Do not introduce a generic overlay registry or threat-range renderer.
- Do not touch service/view model shape.
- Do not change SVG class names, colors, raster dimensions, ordering, labels, or movement geometry.
- Do not add web/desktop behavior.

