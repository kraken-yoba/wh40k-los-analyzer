# Phase 5 Consultant Review - Movement Reach Toolkit

Date: 2026-06-21

## Review Scope

Consultant reviewers evaluate whether the Phase 5 movement reach slice is right-sized and fits the
existing geometry, service, web, and desktop architecture.

## Geometry Consultant

Reviewer: `019eebbe-579b-7631-9786-69efc5050571`

Status: approved with naming and claim constraint.

- Proceed if the tool is called an estimated 2D movement reach tool, not endpoint legality.
- Keep the slice manual, single-model, round-base, geometry-only, and `estimated`.
- Put movement geometry in a new focused `los/movement.py` module rather than growing
  `los/geometry.py`.
- Keep transient request/payload types in application/domain records for this slice; do not mutate
  `BoardState`.
- Use Shapely board-valid center region, dense-feature buffered blockers, movement-distance disk,
  and straight swept corridor diagnostics.
- Surface limitations: 2D center/base geometry only, not rules-legal movement, no vertical movement,
  terrain traversal permissions, coherency, other models, engagement, charge/disembark/scout/reserve
  restrictions, or non-round base shapes.

## UI Consultant

Reviewer: `019eebbe-8fb8-7050-bb2c-5a6c1867063e`

Status: approved with sequencing condition.

- Add both web and desktop surfaces in Phase 5 only after the service/result layer lands.
- Keep adapters thin like the existing LOS Checker pattern.
- Web remains server-rendered with no custom JavaScript.
- Use wording such as estimated 2D reach, geometric reach estimate, blocked by board edge,
  assumptions, warnings, and not a rules-legal endpoint claim.
- Browser QA must verify `/movement-reach`, submitted value persistence, movement SVG overlay,
  readiness/assumption text, absence of forbidden legal/safe wording, and no console errors.

## Triage

- Accepted: use a focused `los/movement.py` module and application toolkit builder.
- Accepted: keep Phase 5 single-model, manual, round-base, and `estimated`.
- Accepted: web and desktop surfaces are included only as thin service adapters.
- Accepted: avoid legal/safe/recommended/optimal/likely wording.
- Accepted: defer coherency, other-model collision, non-round bases, objective/action markers,
  exposure summaries, pathfinding, dice, charge/disembark/scout/reserve mechanics, roster/profile
  integration, and threat-range behavior.

## Final Approval Gate

Final consultant approval requires:

- The scope is appropriate for Phase 5 and does not become threat range, mission logic, or full
  legal movement.
- Geometry lives under the existing reusable Python engine boundary.
- Web and desktop surfaces remain thin adapters over `WarhammerCompanionService`.
- The QA pathway can be executed autonomously.
