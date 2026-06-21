# Phase 5 Adversarial Review - Movement Reach Toolkit

Date: 2026-06-21

## Review Scope

Adversarial reviewers evaluate whether Phase 5 creates false precision, hidden rules claims, source
trust regressions, or scope creep into later roadmap phases.

## Initial Findings

Reviewer: `019eebbe-bd44-7e60-b0a0-aa6a30cedc19`

Status: conditional approval, not full approval.

- Phase 5 is directionally right only if narrowed to a diagnostic single-model, manual,
  circular-base, 2D straight-corridor reach estimate.
- False legality is the primary risk. Phase 5 inputs are not source-backed for movement, terrain,
  vertical, coherency, or model-collision mechanics.
- Existing terrain semantics are source-pending. Dense/solid geometry can support diagnostics, not
  movement-rule authority.
- A straight swept corridor is not a route/pathfinding proof because models can route around
  corners.
- Oval, rectangle, hull, and custom base support must be cut until an orientation/footprint policy
  exists.
- UI scope is acceptable only if web and desktop remain thin adapters after the service/result layer.

## Triage

- Accepted: Phase 5 is narrowed to single-model, manual, circular-base diagnostics.
- Accepted: no coherency, multi-model collision, enemy/friendly collision, oval/rectangle/hull/custom
  base support, objective/action markers, exposure summary, or pathfinding around obstacles.
- Accepted: valid manual round-base results are `estimated`; invalid base/movement inputs are
  `blocked` with no overlays.
- Accepted: UI wording must include estimated 2D geometry and avoid legal, safe, recommended,
  optimal, likely, and guaranteed wording.

## Final Approval Gate

Final adversarial approval requires:

- Movement output is explicitly estimated unless source-backed rules make a later trusted result
  possible.
- Invalid inputs block instead of creating misleading overlays.
- Endpoint diagnostics do not use legal, safe, recommended, optimal, likely, or expected-points
  language.
- No roster/profile, mission, threat, damage, analytics, or AI behavior is introduced.
- Browser and desktop QA are recorded before commit.
