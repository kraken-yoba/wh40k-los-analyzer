# Phase 7 Adversarial Review - Deployment Exposure

Date: 2026-06-22

## Initial Verdict

CHANGES_REQUESTED unless Phase 7 stays a diagnostic/exposure overlay slice rather than a placement
planner.

## Accepted Requirements

- Return a `ToolkitResult` payload before web/desktop rendering.
- Preserve readiness semantics: `estimated` for valid manual assumptions, `blocked` for invalid
  inputs, never `trusted` in this phase.
- Avoid visible/export wording such as `legal`, `safe`, `recommended`, `optimal`, `likely`, or
  `guaranteed`.
- Do not present the existing `safe-zone-outline` renderer class as product truth; visible copy must
  use "candidate staging" or "not exposed under selected assumptions".
- Keep web and desktop as adapters over the service.
- No JavaScript or new frontend architecture.
- No mission, objective, damage, survivability, pairing, or AI behavior.
- Include page 9 and page 52 regression checks when geometry/rendering behavior changes.
- Require Browser QA for the new route and desktop smoke for native surface coverage.

## Applied Spec Changes

- Renamed the slice to Deployment Exposure.
- Changed route and modules to `/deployment-exposure` and `deployment_exposure`.
- Replaced first-pass "estimated safe" acceptance wording with
  `not_exposed_under_assumptions`.
- Added explicit forbidden-word checks for visible copy and toolkit text fields.

## Re-Review Finding

CHANGES_REQUESTED because the first revised plan and QA path did not explicitly require page 9 and
page 52 Deployment Exposure regression checks.

## Applied Fix

- Added page 9 Browser QA route:
  `/deployment-exposure?packet_id=official-event-companion-page-9&deployment_zone_id=attacker&friendly_x=19.24&friendly_y=51.48&friendly_base=1.57&enemy_x=24.77&enemy_y=8.46&enemy_base=1.57&enemy_move=6&enemy_threat=2&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`.
- Added page 52 Browser QA route:
  `/deployment-exposure?packet_id=official-event-companion-page-52&deployment_zone_id=defender&friendly_x=29.34&friendly_y=10.00&friendly_base=1.57&enemy_x=14.66&enemy_y=49.99&enemy_base=1.57&enemy_move=6&enemy_threat=2&enemy_mode=fixed-move-plus-range&exposure_mode=threat-and-los`.

## Final Verdict

APPROVED.

## Final Notes

No concrete blockers remain after adding explicit page 9 and page 52 Browser regression routes.
The design preserves the `ToolkitResult` and service-boundary approach, requires Browser QA plus
desktop smoke, and keeps visible wording away from placement-compliance, safe, and recommendation
claims.

## Implementation Review

Initial implementation verdict: REQUIRED CHANGES.

Blockers found:

- Curved deployment-zone placement used raw deployment polygons while candidate staging used
  smoothed/eroded deployment-center geometry. This could report a placement as not exposed even
  when the center was outside the candidate staging region.
- `threat-and-los` could show "not exposed under selected assumptions" while also reporting an
  LOS-only component fact with selected-assumption wording.

Applied fixes:

- Added a curved deployment regression at friendly center `(12.2, 30.8)`.
- Changed placement diagnostics to use the smoothed/eroded allowed center region and to derive
  `not_exposed_under_assumptions` from `candidate_center_region.covers(point)`.
- Added all-four-mode exposure tests and split component reason ids from
  `exposed-under-selected-assumptions`.

Implementation re-review verdict: APPROVED.

No commit-blocking issues remained. The adversarial reviewer reran the focused
`tests/test_deployment_exposure_toolkit.py -q` suite and observed 6 passed. They accepted the local
full-suite and Browser QA rerun evidence reported in the work log.
