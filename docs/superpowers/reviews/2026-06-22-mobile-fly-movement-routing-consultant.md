# Mobile And Fly Movement Routing Consultant Review

Date: 2026-06-22

## Scope

Consultant review for the source-backed spec to rebuild movement and downstream threat tooling around
movement profiles, route-around behavior, and Fly/Take to the Skies.

## Rules And Architecture Inputs

The rules consultant recommended modelling these first profiles:

- ground units with INFANTRY, BEASTS, SWARM, or MOBILE horizontal dense-feature pass-through;
- ground units that must route around dense terrain features when no section-height metadata proves
  pass-through;
- FLY units that explicitly select Take to the Skies, including the 2-inch movement penalty;
- Super-heavy Walker temporary MOBILE as a later ability-driven profile unless roster/profile data
  requires it.

The architecture consultant identified the root cause as the current non-pathfinding movement model:
`movement_envelope(...)` subtracts dense collision regions from a Euclidean disk, and Threat Range
inherits that behavior through move-plus-range projections. The recommendation was to add reusable
movement profile and pathfinding records, keep route algorithms in `los/`, and thread profile inputs
through Movement Reach, Threat Range, Deployment Exposure, Deployment Scorecard, services, view
models, web, desktop, and input hashes.

## Written-Spec Review

The consultant written-spec review approved the spec as source-backed, focused, and clear enough for
the next plan loop. One planning note required Fly/Hover ordering to reflect the user's "second fix"
priority. The spec was patched so Phase C is now Fly and Hover immediately after the Phase B
non-mobile route-around endpoint slice, before route-connected envelopes and threat propagation.

Focused re-review approved the patched ordering.
