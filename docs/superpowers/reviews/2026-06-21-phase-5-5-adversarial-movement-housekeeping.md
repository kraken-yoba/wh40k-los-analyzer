# Phase 5.5 Adversarial Review - Movement Housekeeping

Date: 2026-06-21

Reviewer: adversarial subagent `019eebe6-f9c7-7e33-8da3-fe5a5bc4133e`

## Review Prompt

Critique the proposed Phase 5.5 cleanup for accidental behavior changes, insufficient scope,
unnecessary abstractions, UI/rendering drift, or Phase 6 scope creep.

## Outcome

Approved with constraints.

Accepted constraints:

- Keep `rendering/svg.py` as the owner of SVG/raster map rendering.
- Treat raster work as shared plumbing extraction, not semantic unification.
- Preserve layer order and CSS classes: `heatmap-image`, `coverage-image`,
  `hidden-coverage-image`, and `movement-envelope-image`.
- Do not collapse heatmap, LOS coverage, hidden coverage, and movement envelope semantics.
- Do not touch movement rules, threat/exposure rules, BoardState, MapPacket schema, route
  parameters, templates, official PDF/data handling, or desktop/web UI behavior.
- Do not merge `desktop/svg_raster.py` into this cleanup.
- Keep legacy cell render fallbacks.

Accepted required tests:

- Add decoded-PNG tests for representative heatmap, LOS coverage, hidden coverage, and movement
  envelope raster behavior.
- Add desktop tests for extracted spin-box defaults.
- Run targeted regression, full static/test gates, desktop smoke, and Browser QA for affected
  rendered surfaces.

