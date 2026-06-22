# Mobile And Fly Movement Routing Adversarial Review

Date: 2026-06-22

## Scope

Adversarial review for the mobile-aware and Fly-aware movement routing spec before committing the
spec loop.

## Initial Guardrails

The adversarial gap-analysis pass required the spec to avoid these traps:

- upgrading estimated routing into legal-movement or charge-legality claims;
- treating all dense terrain as universally impassable;
- confusing terrain areas with terrain features;
- modelling FLY as a permanent ignore-terrain toggle instead of an explicit Take to the Skies
  option;
- ignoring the 2-inch Take to the Skies cost or Hover exception;
- using Shapely boolean envelopes as proof of shortest paths;
- omitting downstream propagation into Threat Range, Deployment Exposure, and Deployment Scorecard;
- leaving vertical movement, model collisions, non-round/FRAME rotation, and exact charge legality
  ambiguous;
- skipping page 9/page 52 performance checks and deterministic synthetic blocker QA.

## Resolution

The written spec incorporates those guardrails:

- valid output remains `estimated`;
- dense feature traversal and endpoint occupancy are separated;
- `ground-non-mobile`, `ground-mobile`, `fly-take-to-skies`, and
  `fly-hover-take-to-skies` profiles are explicit;
- route-aware movement requires deterministic bounded pathfinding with algorithm and tolerance
  metadata;
- Threat Range, Deployment Exposure, and Deployment Scorecard must receive profile inputs and hash
  changes;
- non-round/FRAME movement, vertical movement, model collision, and exact charge legality remain
  non-goals;
- QA requires synthetic route-around, mobile pass-through, Fly/Hover, page 9/page 52 performance,
  web/desktop, manual Browser/Computer or documented fallback, and protected-source scans.

Final written-spec adversarial verdict: approved. The commit-blocker check found no issues with
movement/Fly/MOBILE semantics, estimated-only framing, downstream Threat Range and deployment
propagation, no-JavaScript web/desktop QA, protected-source handling, or the AGENTS.md architecture
boundaries.
