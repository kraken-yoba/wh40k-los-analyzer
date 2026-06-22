# Phase 6.5 Threat Housekeeping Spec

Date: 2026-06-22

## Purpose

Phase 6 added the manual threat range toolkit. Phase 6.5 is a behavior-preserving cleanup slice
before Phase 7. It reduces duplicated circular-base board-fit geometry exposed by Phase 6 without
changing threat projection, movement reach, web routes, desktop navigation, source authority,
readiness semantics, or UI copy.

## Scope

This slice may touch only:

- `src/warhammer_companion/los/movement.py`
- `src/warhammer_companion/application/threat_range.py`
- focused tests that lock the shared geometry helper
- Phase 6.5 documentation, review records, and the player-toolkit work log

## Design

Phase 5 movement geometry already computes the region where a circular model base center can remain
fully inside the board. Phase 6 duplicated equivalent logic in the threat toolkit validation. This
slice exposes that geometry as `base_center_region(packet, base_radius)` in `los/movement.py` and
uses it in both:

- `movement_envelope(...)`
- `movement_endpoint_diagnostic(...)`
- threat-range source-base board validation

The helper remains a Shapely geometry helper under `los/`; it does not become a domain model and it
does not add new gameplay rules. It accepts a nonnegative base radius and preserves the existing
large-base behavior for unusually small boards.

## Explicit Non-Goals

- No new movement, threat, roster, damage, mission, analytics, or AI behavior.
- No changed dice distributions, threat probabilities, movement envelopes, endpoint diagnostics, or
  target probability semantics.
- No web template, CSS, route, desktop navigation, or desktop control changes.
- No official-source extraction or generated data changes.
- No custom frontend JavaScript.
- No change to board coordinate convention, board size, terrain semantics, or source/readiness
  wording.

## Acceptance Criteria

- A direct test locks `base_center_region(...)` board-edge semantics for normal and oversized base
  cases.
- Existing movement envelope tests still pass unchanged.
- Existing threat-range overhanging source-base validation still blocks with no overlays.
- Static checks pass.
- Full tests pass or a narrower final run is justified by behavior-preserving scope.
- Browser QA confirms relevant map pages still render if any runtime surface changes are made.
- Consultant and adversarial reviewers approve the cleanup as behavior-preserving and scoped.
