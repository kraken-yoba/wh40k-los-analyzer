# Mobile And Fly Movement Routing Spec

Date: 2026-06-22

## Goal

Rebuild the movement engine used by Movement Reach, Threat Range, Deployment Exposure, and
Deployment Scorecard so it distinguishes unit traversal profiles:

- ground units that can move horizontally through dense terrain features;
- ground units that must route around dense terrain features under the current map data;
- FLY units that explicitly use Take to the Skies.

This is a rules-aware estimated routing slice, not an exact legal-move solver. It should correct the
current false model where every unit inherits one dense-blocker subtraction and endpoint diagnostics
only consider Euclidean distance plus a straight swept corridor.

## Source Review

Official source reviewed:

- Warhammer 40,000 Core Rules PDF from Warhammer Community:
  `https://assets.warhammer-community.com/eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf`
- The PDF was downloaded to a local temporary path for extraction only. It must not be committed,
  copied into app data, or packaged.

Relevant rule anchors:

- Pages 12-13: basic movement, ending a move, movement as multiple straight segments, and rotation.
- Page 37: charge example where a target is within rolled distance but terrain routing prevents the
  charge from ending engaged.
- Pages 46-49: terrain categories, terrain areas, dense terrain features, horizontal and vertical
  movement through dense terrain, and dense-feature examples.
- Page 71: FLY and Take to the Skies.
- Page 85: Super-heavy Walker and temporary MOBILE keyword.

Key source-backed interpretations for this design:

- Movement permissions are about terrain features, not broad terrain areas. A model can cross a
  terrain area without impediment when it is not moving through a terrain feature.
- INFANTRY, BEASTS, SWARM, and MOBILE models can move horizontally through dense terrain features.
- Other models can only move horizontally through dense feature sections that are 2 inches or less
  high; without section-height data, this app must conservatively route them around dense feature
  polygons.
- A FLY unit does not automatically ignore terrain. It can choose Take to the Skies for normal,
  advance, fall-back, or charge moves. When it does, the move distance is reduced by 2 inches unless
  a rule such as Hover removes that cost, and the moving FLY model can move through all terrain
  categories.
- The first implementation cannot model vertical movement, stable elevated placement, ceilings,
  floors, enclosed solid areas, or exact charge legality from current map packets.

## Current Root Cause

Current movement geometry in `src/warhammer_companion/los/movement.py`:

- builds `Point(start).buffer(move_distance)`;
- clips it to board-fit center space;
- subtracts dense collision regions for every unit;
- checks the selected endpoint using Euclidean distance and one straight swept circular-base
  corridor.

Current threat geometry in `src/warhammer_companion/los/threat.py` calls that same movement envelope
for move-plus-range modes. Deployment Exposure and Deployment Scorecard consume threat projection
outputs, so the same simplification propagates downstream.

This misses two important cases:

- non-mobile ground units may be able to move around dense terrain by a non-straight path even when
  a direct swept corridor crosses a blocker;
- mobile and Take-to-the-Skies units should not treat dense terrain as a traversal blocker.

## Product Behavior

### Movement Profile

Add a manual movement profile selector used by Movement Reach, Threat Range, Deployment Exposure, and
Deployment Scorecard. Initial profile options:

- `ground-non-mobile`: default profile for models without INFANTRY, BEASTS, SWARM, MOBILE, or an
  active Take-to-the-Skies move. Dense feature footprints block traversal and endpoint occupancy.
- `ground-mobile`: profile for INFANTRY, BEASTS, SWARM, and MOBILE horizontal movement. Dense
  feature footprints do not block traversal, but endpoint/base occupancy still cannot overlap a
  dense feature in this 2D implementation.
- `fly-take-to-skies`: profile for a FLY unit whose player selects Take to the Skies. The effective
  move distance is reduced by 2 inches, traversal ignores dense terrain blockers, and endpoint/base
  occupancy still cannot overlap a dense feature in this 2D implementation.
- `fly-hover-take-to-skies`: same traversal policy as `fly-take-to-skies`, but without the 2-inch
  movement penalty for units with Hover or equivalent no-cost source-backed behavior.

The UI should describe these as estimated movement assumptions, not unit legality. A FLY unit that
does not use Take to the Skies should use the appropriate ground profile instead.

### Traversal Versus Endpoint Occupancy

The movement engine must split two concepts:

- traversal blockers: geometry that a path cannot pass through for the selected profile;
- occupancy blockers: geometry that the final circular base cannot overlap.

Dense features are traversal blockers only for `ground-non-mobile` in the first implementation.
Dense features remain occupancy blockers for all initial profiles because the app does not yet know
which dense feature surfaces are open floor, vertical walls, enclosed solids, or valid elevated
ending surfaces.

### Route-Aware Movement

For `ground-non-mobile`, movement distance is the shortest route through navigable base-center space,
not the straight-line distance through obstacles. The path may be a sequence of straight segments
around dense blockers.

The first implementation should use deterministic bounded 2D routing:

- inflate traversal blockers by the circular base radius;
- compute navigable center space as board-fit space minus inflated traversal blockers;
- use a deterministic pathfinding algorithm versioned in hashes and payload metadata;
- return selected endpoint route distance, route geometry, and route diagnostics;
- generate the movement envelope as an estimated route-connected region using a deterministic
  resolution/tolerance recorded in payload metadata.

The exact algorithm can be chosen in the implementation plan, but acceptable options are:

- a visibility-graph shortest-path endpoint solver plus a sampled route-distance field for the
  envelope; or
- a bounded grid/navmesh route-distance field for both endpoint and envelope.

The implementation must not rely on `Point(start).buffer(distance).difference(blockers)` as proof of
route-connected reach.

### Threat And Downstream Propagation

Threat Range must pass the movement profile into movement routing for every move-plus-range outcome.
The `raw-range` mode remains unchanged because it has no movement component.

Deployment Exposure and Deployment Scorecard must expose the selected enemy movement profile because
their threat and exposure calculations inherit the Threat Range projection.

Every affected input hash must include:

- movement profile id;
- effective movement distance after profile modifiers;
- pathing algorithm version;
- route resolution/tolerance when used;
- endpoint occupancy policy;
- traversal policy.

## UI Surface

Web remains server-rendered FastAPI/Jinja with no custom JavaScript. Desktop remains PySide6 over
the shared service layer.

Required controls:

- Movement Reach: movement profile selector next to movement mode.
- Threat Range: movement profile selector next to threat mode; visible effective move distance when
  Take to the Skies applies a penalty.
- Deployment Exposure and Deployment Scorecard: enemy movement profile selector wherever enemy
  movement/threat inputs are shown.
- Desktop screens must mirror the same option labels and service state.

Required wording:

- Use "estimated route" and "selected movement assumptions".
- Avoid "legal", "safe", "optimal", "recommended", "guaranteed", "can charge", and unqualified
  "reachable".
- When showing route diagnostics, use "route-connected under selected assumptions" rather than a
  rules-legal claim.

## Data And Architecture

Domain layer:

- Extend `domain/movement.py` with typed profile records such as:
  - `MovementProfile`
  - `MovementProfileId`
  - `MovementTraversalPolicy`
  - `MovementPathResult`
  - `MovementRoutingMetadata`
- Extend `MovementEndpointDiagnostic` with route distance/path information while preserving blocker
  reason details.
- Extend `MovementReachPayload` with selected profile, effective move distance, routing metadata,
  route geometry, traversal blocker geometry, and occupancy blocker geometry.

LOS/geometry layer:

- Keep route algorithms under `src/warhammer_companion/los/`.
- `los/movement.py` can host the public movement API, but non-trivial path helpers may live in
  `los/pathfinding.py` if that keeps the file bounded.
- `los/threat.py` must accept a movement profile for move-plus-range projections.

Application layer:

- `application/movement_reach.py`, `application/threat_range.py`,
  `application/deployment_exposure.py`, and `application/deployment_scorecard.py` must include
  movement profile inputs in validation, result identity, assumptions, warnings, and state.
- `WarhammerCompanionService` remains the shared entrypoint for web and desktop adapters.

Rendering:

- Preserve current SVG/raster rendering patterns.
- Render route geometry when a selected endpoint route is available.
- Render route-connected envelopes as estimated overlays with stable CSS/SVG ids.
- If a sampled/raster reach envelope is used, include algorithm version and resolution in payload
  metadata and tests.

## Phased Goal Loops

The implementation should proceed as separate goal loops after this spec is approved:

1. **Plan loop:** write a detailed task-by-task implementation plan with QA paths and subagent
   review. No production code.
2. **Phase A - Profile plumbing:** add movement profile domain types, service state, web/desktop
   controls, hash identity, and warning/assumption copy without changing routing behavior.
3. **Phase B - Non-mobile route-around endpoint:** implement route-aware endpoint diagnostics for
   `ground-non-mobile`; keep route geometry deterministic and tested.
4. **Phase C - Fly and Hover:** implement Take to the Skies profiles, effective movement penalties,
   and no-cost Hover option after route-around endpoint behavior is tested.
5. **Phase D - Route-connected movement envelope:** replace the dense-subtracted Euclidean disk with
   a route-connected estimated envelope and performance guardrails for all initial profiles.
6. **Phase E - Threat propagation:** thread movement profiles and route-connected envelopes through
   Threat Range.
7. **Phase F - Downstream exposure/scorecard propagation:** expose enemy movement profiles in
   Deployment Exposure and Deployment Scorecard and update their identities.
8. **Housekeeping loops:** after major behavioral phases, run behavior-preserving cleanup loops as
   needed.

## Acceptance Criteria

### Rules And Scope

- The result remains `estimated` for valid manual inputs and `blocked` for invalid geometry inputs.
- No output claims exact legal movement, exact charge legality, safety, or recommendations.
- Dense movement decisions use dense terrain feature polygons, not terrain area polygons.
- Official PDF text and the downloaded PDF remain uncommitted.

### Geometry

- Synthetic tests prove a straight swept corridor can be blocked while a non-mobile route around the
  blocker is within movement budget.
- Synthetic tests prove a non-mobile route around a blocker is over budget when the detour exceeds
  the selected movement distance.
- Synthetic tests prove `ground-mobile` can route through dense traversal blockers while still
  blocking endpoint occupancy inside dense feature footprints.
- Synthetic tests prove Take to the Skies ignores dense traversal blockers and applies the 2-inch
  movement penalty.
- Synthetic tests prove Hover/no-cost Take to the Skies does not apply the 2-inch penalty.
- Page 9 and page 52 official seed packets complete movement and threat projections within a bounded
  performance budget recorded in the plan.

### Threat And Downstream

- `raw-range` threat projection is unchanged by movement profile.
- Move-plus-range threat projections differ for `ground-non-mobile`, `ground-mobile`, and
  Take-to-the-Skies profiles when dense blockers are between source and target.
- Deployment Exposure and Deployment Scorecard include enemy movement profile in state, input hash,
  and warnings.

### UI And Adapters

- Web route tests cover profile controls, value preservation, cautious copy, no custom scripts, and
  route output rendering.
- Desktop tests cover combo population, state propagation, screen rendering, and smoke-test keys.
- Browser or Computer manual QA verifies Movement Reach, Threat Range, Deployment Exposure, and
  Deployment Scorecard profile controls. If Browser/Computer tooling is unavailable, a documented
  TestClient/manual fallback must cover the same route contracts.

### Verification

- Focused movement/threat/deployment tests pass.
- Ruff format/check, Ruff lint, mypy, full pytest, packet validation, desktop smoke, and
  `git diff --check` pass before each implementation commit.
- Protected-source scan proves no raw official PDFs, generated caches, logs, Codex state, or
  credentials are staged.

## Explicit Non-Goals

- No exact legal movement oracle.
- No exact charge-target legality solver.
- No vertical movement, climbing, floors, ceilings, enclosed solid terrain resolution, stable
  elevated placement, or terrain-section height solver.
- No non-round base, hull, FRAME, rotation-cost, or oriented-footprint solver in the first
  implementation. Non-round/FRAME movement must remain out of scope or blocked explicitly.
- No multi-model coherency, friendly/enemy model collision, aircraft-specific combat rules,
  transports, reserves, stratagems, CP, rerolls, modifiers, or roster-derived profile ingestion.
- No official PDF bundling, protected rules text packaging, or custom frontend JavaScript.

## Reviewer Findings Incorporated

- Rules consultant: split profiles into pass-through ground, non-pass-through ground, and explicit
  Take to the Skies; distinguish MOBILE keyword from generic mobile wording; distinguish terrain
  areas from terrain features.
- Architecture consultant: route around blockers in reusable movement/pathfinding code, thread
  profile inputs through Movement Reach, Threat Range, Deployment Exposure, Deployment Scorecard,
  services, view models, web, desktop, and hashes.
- Adversarial reviewer: keep the result an estimated routing diagnostic, add pathfinding guardrails,
  avoid exact charge legality claims, require performance tests on page 9/page 52, and keep vertical,
  frame, model-collision, and exact legal movement out of scope.
