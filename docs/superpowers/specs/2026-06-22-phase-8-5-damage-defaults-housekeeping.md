# Phase 8.5 Damage Profile Defaults Housekeeping Spec

Date: 2026-06-22

## Roadmap Anchor

Phase 8A added the first manual estimated Damage Profile tool. Phase 8.5 is a
behavior-preserving housekeeping slice before any further roster-aware damage work.

## Goal

Centralize the default manual damage profile and target profile values so the service, web route,
desktop screen, smoke tests, and future Phase 8 work share one source of truth.

This reduces drift risk without changing:

- Damage math.
- Readiness semantics.
- Warning copy.
- Route names or query parameter names.
- Desktop screen labels or controls.
- Any roster/profile/rules authority.

## Current Drift Risk

The default sample values are duplicated in multiple adapters:

- 2 attacks.
- 4+ hit target.
- 4+ wound target.
- 4+ effective save target.
- Damage 2.
- 2 wounds/model.
- 3 target models.

These are product defaults for the manual estimate. They are not rules/profile data.

## Required Change

- Add canonical default constants for the manual damage profile input and target profile input.
- Use those constants in:
  - `WarhammerCompanionService.damage_profile_state(...)`.
  - `WarhammerCompanionService.damage_profile_toolkit_result(...)`.
  - GET `/damage-profile` route defaults.
  - Desktop `DamageProfileScreen` initial controls.
  - Desktop smoke and guardrail tests where defaults are asserted.
- Keep explicit form/query field names unchanged.
- Keep all values unchanged.

## Acceptance Criteria

- Existing default `/damage-profile` behavior remains the same.
- Existing desktop `Damage Profile` behavior remains the same.
- Service default `damage_profile_state()` returns the same summary as before.
- New guardrail tests prove service and desktop defaults come from the canonical constants.
- No result becomes `trusted`.
- No official, roster, profile, AP/cover, reroll, ability, or survivability behavior is added.
- Standard validation and default-route Browser QA pass.
