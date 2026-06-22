# Phase 8A Adversarial Review - Manual Damage Estimate

Date: 2026-06-22

## Initial Verdict

REQUIRED CHANGES.

## Findings

- The initial proposal overclaimed Phase 8 by implying roster-aware damage and survivability profiles
  before source/profile resolution exists.
- The first slice must be named `Manual Damage Estimate` or similar, not full Damage And
  Survivability Profiles.
- Save input must be a manual effective save target after unmodeled AP/cover/invulnerable decisions.
- Exact math subset, invalid-input blockers, no-spillover semantics, and warning language must be
  explicit before implementation.

## Applied Spec Changes

- Renamed the slice to Phase 8A Manual Damage Estimate.
- Scoped the tool to one manual weapon profile into one homogeneous target profile.
- Explicitly supported fixed attacks, flat damage, manual hit/wound/effective save thresholds,
  target wounds/model, target model count, exact binomial unsaved-wound PMF, and no-spillover
  models-destroyed distribution.
- Explicitly blocked or deferred random attacks/damage, AP/cover resolution, invulnerable selection,
  rerolls, modifiers, abilities, Feel No Pain, damage reduction, mission warnings, target priority,
  unit-vs-unit matrices, and roster-derived mechanics.
- Added QA for invalid blockers, trust wording, web route, desktop smoke, Browser QA, and protected
  data guardrails.

## Re-Review

The adversarial reviewer required finite positive integer target wounds/model and target model count
semantics, plus explicit builder fixtures for every declared invalid-input blocker class. The spec,
plan, and QA pathway were patched before implementation.

Final spec re-review verdict: APPROVED.

## Implementation Review

Initial implementation review required one correctness fix: remove the kill-threshold tolerance from
`models_destroyed_for_unsaved_wounds(...)` because fractional flat damage is supported and
near-threshold fractional sums must not overkill.

Accepted fix:

- Removed the tolerance and compared accumulated damage directly with target wounds/model.
- Added a regression for 3 unsaved wounds at 0.333333333 damage into a 1-wound target returning 0
  destroyed models.
- Re-ran focused toolkit tests, static checks, mypy, and full pytest.

Final implementation review verdict: APPROVED.
