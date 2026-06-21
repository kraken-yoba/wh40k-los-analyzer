# Movement Reach Toolkit Spec

Date: 2026-06-21

Parent roadmap:

- `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`
- `docs/superpowers/specs/2026-06-20-toolkit-result-and-board-state-spec.md`
- `docs/superpowers/specs/2026-06-20-base-size-and-terrain-semantics-spec.md`

## Goal

Add Phase 5, the first deterministic player tool beyond LOS: a manual movement reach checker.

This slice gives players a single-model, manual, circular-base 2D movement diagnostic that works
before roster/profile import is complete. It takes manual start and target points, base diameter,
movement distance, and a move mode label. It returns a shared `ToolkitResult` with a movement
envelope overlay, straight-corridor endpoint diagnostics, assumptions, warnings, and a rendered SVG
projection for web and desktop screens.

## Scope

- Add reusable single-model round-base movement geometry under `src/warhammer_companion/los/`.
- Add domain records for manual movement requests, endpoint diagnostics, and movement payloads.
- Add an application builder that returns `ToolkitResult[MovementReachPayload]`.
- Add `WarhammerCompanionService.movement_reach_toolkit_result(...)`.
- Add `WarhammerCompanionService.movement_reach_state(...)` for web and desktop rendering.
- Add a server-rendered no-JavaScript `/movement-reach` page with GET and POST handling.
- Add a PySide6 Movement Reach desktop screen using the same service state.
- Add SVG rendering for movement envelope regions, selected start/target bases, and target path.
- Add smoke tests so web, desktop, and service paths prove the tool is available.

## Non-Goals

- No exact rules-legal movement verdicts.
- No advance/charge dice probability, rerolls, modifiers, CP, stratagem, or distribution modeling.
- No roster/profile/base-size-pack integration.
- No coherency solver or multi-model movement.
- No friendly/enemy model collision from full `BoardState` unit placement.
- No mission/action reach logic.
- No objective/action reach markers.
- No exposure or safe-position summary.
- No pathfinding around blockers.
- No oval, rectangle, hull, or custom base orientation policy.
- No threat range, safe deployment, damage, survivability, team-pairing analytics, or AI companion
  behavior.
- No source fetching, public-sheet ingestion, official/community data bundles, or protected rules
  text.
- No custom frontend JavaScript.

## Design Decisions

- Movement geometry lives in `los/movement.py` because AGENTS.md keeps reusable geometry algorithms
  under the `los` package.
- The first implementation is single-base/manual-input only. Multi-model coherency and formation
  movement will be a later slice after the base deterministic surface is stable.
- Dense features are treated as 2D movement blockers in this estimate based on current map packet
  hints, not source-backed movement rules. The result remains `estimated` and cannot be a terrain
  authority claim.
- The movement envelope overlay is an endpoint estimate:
  - base centers must stay inside the board after accounting for base radius;
  - endpoints inside dense-feature buffered collision zones are excluded;
  - the overlay does not prove that every path inside the region is route-connected around terrain.
- The selected endpoint check uses a swept circular base corridor along the straight segment from
  start to target. This catches common direct-collision cases and explains why a target point is
  outside the estimate.
- Move modes are labels for the operator-entered distance in Phase 5. Normal, Advance, Charge,
  Scout, Ingress, and Disembark can be selected, but dice, rerolls, reserves, transports, vertical
  movement, and source-backed mode legality are not calculated.
- Results are `estimated` when the manual inputs are valid. They are `blocked` only for invalid
  geometry inputs that prevent producing a meaningful diagnostic, such as non-positive base or move
  distance.
- The UI may say "reachable estimate" and "endpoint diagnostic". It must not say legal, safe,
  recommended, optimal, or likely.
- Any future non-round base support must be a separate slice. This phase accepts only a circular
  base diameter input and blocks non-finite or non-positive values.

## Data Contracts

`MovementMode`

- `normal`
- `advance`
- `charge`
- `scout`
- `ingress`
- `disembark`

`MovementReachPayload`

- `packet`
- `mode`
- `start_center`
- `target_center`
- `base_diameter`
- `move_distance`
- `movement_envelope`
- `swept_path`
- `endpoint`
- `dense_collision_regions`

`MovementEndpointDiagnostic`

- `within_distance`
- `within_board`
- `clear_of_dense_features`
- `estimated_reachable`
- `distance`
- `reasons`

## Acceptance Criteria

- Movement geometry excludes endpoints that would place the circular base outside the board.
- Movement geometry excludes endpoints whose circular base would overlap dense movement blockers.
- Endpoint diagnostics report distance, board-edge, and dense-feature swept-corridor blockers.
- Invalid base diameter or move distance returns a blocked toolkit result with no tactical overlay.
- Valid manual inputs return an `estimated` toolkit result with:
  - one movement envelope overlay;
  - movement assumptions and warnings;
  - no recommendation language.
- Input hashes change when packet content, start, target, base, distance, or mode changes.
- The web `/movement-reach` page renders without custom JavaScript and preserves submitted values.
- The page copy contains "Estimated 2D geometry" and does not contain legal, safe, recommended,
  optimal, likely, or guaranteed wording for estimated results.
- The desktop Movement Reach screen renders a non-null map pixmap and desktop smoke includes a
  movement SVG.
- Browser QA verifies `/movement-reach` and a Layout B/query smoke path in addition to existing
  map routes.

## QA Expectations

- Unit tests for movement geometry.
- Toolkit-result tests for readiness, overlay contract, blocked invalid input, and identity.
- Service tests proving state renders through the same SVG projection as direct rendering.
- Web route tests proving GET/POST controls, no custom JavaScript, and query preservation.
- Desktop tests proving nav/smoke exposure.
- Full project validation plus Browser route sweep before commit.
