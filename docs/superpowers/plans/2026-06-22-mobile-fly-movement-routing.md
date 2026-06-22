# Mobile And Fly Movement Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this
> plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make movement and move-plus-threat calculations visibly movement-profile aware in the web
and desktop app, including non-mobile route-around behavior, horizontal dense-feature pass-through
profiles, and FLY Take to the Skies profiles.

**Primary spec:** `docs/superpowers/specs/2026-06-22-mobile-fly-movement-routing-spec.md`

**Architecture:** Movement profiles and payload metadata live in `domain/movement.py`. Pathfinding
and movement geometry stay in `los/`. Movement Reach, Threat Range, Deployment Exposure, and
Deployment Scorecard continue to flow through application services before web/desktop adapters.
The first solver is an estimated 2D route-distance field; it is not a legal movement oracle.

---

## Decisions

- Use a deterministic grid route-distance field for the first route-connected implementation.
  This gives one bounded algorithm for endpoint diagnostics and movement envelopes.
- Use 1.0 inch default routing resolution in product flows, with the resolution and algorithm
  version recorded in payload metadata and input hashes.
- Snap route-grid nodes to the board-fit center-space grid, accept route-distance error up to one
  grid diagonal plus 0.01 inch, and report endpoint diagnostics as estimated when the snapped
  endpoint is used.
- Inflate traversal blockers by the base radius plus a fixed 0.01 inch routing tolerance. Endpoint
  occupancy blockers use the base radius without the routing tolerance.
- Reject route fields above 8,000 candidate grid nodes in product flows with a blocked diagnostic
  and a user-facing performance warning instead of hanging.
- Treat dense terrain feature polygons as traversal blockers only for `ground-non-mobile`.
- Treat dense terrain feature polygons as endpoint occupancy blockers for all initial profiles.
- Apply the Take to the Skies 2 inch penalty to the movement component only. Hover/no-cost Take to
  the Skies applies no penalty.
- Keep `raw-range` threat unchanged by movement profile.

## Phase 1: Baseline Red Tests And Profile Plumbing

- [ ] Add movement profile tests in `tests/test_movement_reach_geometry.py`:
  - non-mobile route around a dense blocker succeeds when the detour is within budget;
  - non-mobile route around the same blocker fails when the detour is over budget;
  - `ground-mobile` ignores dense traversal blockers but still rejects endpoints whose base overlaps
    dense terrain;
  - `fly-take-to-skies` ignores dense traversal blockers and applies the 2 inch movement penalty;
  - `fly-hover-take-to-skies` ignores dense traversal blockers without the penalty.
  - dense terrain feature polygons, not broad terrain area polygons, control traversal.
- [ ] Add threat tests in `tests/test_threat_range_geometry.py`:
  - `raw-range` is unchanged by movement profile;
  - point-in-threat probability is lower or zero for `ground-non-mobile` when route distance is over
    budget;
  - point-in-threat probability increases for `ground-mobile` when dense traversal is the only
    blocker;
  - `fly-take-to-skies` reduces the effective movement component by exactly 2 inches and can fail
    where `fly-hover-take-to-skies` succeeds;
  - threat distribution total reach records the effective movement distance after profile penalty.
- [ ] Add service and adapter tests:
  - Movement Reach and Threat Range states expose profile options and selected values;
  - web GET and POST routes preserve `movement_profile`;
  - Deployment Exposure and Deployment Scorecard states include enemy movement profile;
  - desktop Movement Reach and Threat Range screens populate profile combos.
- [ ] Verify the tests fail for missing profile controls/arguments before implementation.
- [ ] Add profile controls and state only, then run an adversarial review gate before route
  algorithm work. The reviewer must verify the visible app cannot be mistaken for completed routing
  behavior yet and all unimplemented route behavior is still tested RED.
- [ ] Add tests that every affected input hash includes movement profile id, effective movement
  distance, routing algorithm version, route resolution/tolerance, endpoint occupancy policy, and
  traversal policy. This applies to Movement Reach, Threat Range move-plus-range modes, Deployment
  Exposure, and Deployment Scorecard.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_threat_range_geometry.py tests\test_movement_reach_toolkit.py tests\test_threat_range_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
```

## Phase 2: Domain And Routing Core

- [ ] Add typed movement profile records in `domain/movement.py`:
  - `MovementProfileId`
  - `MovementProfile`
  - `MovementRoutingMetadata`
  - profile registry and coercion helpers.
- [ ] Extend movement payloads and endpoint diagnostics with:
  - selected movement profile id and label;
  - effective move distance;
  - route distance and route points;
  - routing algorithm version and resolution;
  - traversal and endpoint occupancy policy notes.
- [ ] Implement route-distance field helpers in `los/movement.py` or `los/pathfinding.py`:
  - board-fit center space;
  - inflated traversal blockers for non-mobile profiles;
  - endpoint occupancy blockers for all profiles;
  - deterministic 8-neighbor Dijkstra over a bounded inch grid;
  - start and target validation against board-fit center space and endpoint occupancy blockers;
  - endpoint snapping that records the snapped target point and tolerance in diagnostics;
  - route reconstruction for the selected endpoint.
- [ ] Update `movement_envelope(...)` and `movement_endpoint_diagnostic(...)` to accept
  `movement_profile_id` and return profile-aware estimated routing metadata.
- [ ] Add page 9/page 52 performance smoke tests for Movement Reach routing and Threat Range
  move-plus-range projections on the official seed packets when present. Record elapsed time, node
  count, resolution, mode/profile, and skip reason if the packet is unavailable in the local seed
  set. Budget: each movement routing call under 750 ms and each threat projection under 2 seconds on
  the local development machine at 1.0 inch routing resolution.
- [ ] Run a consultant and adversarial review gate focused on route-distance correctness,
  dense-feature-vs-area handling, tolerance semantics, and performance guardrails. Fix and rerun
  targeted tests before moving to UI integration.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py -q
```

## Phase 3: Movement Reach Product Surface

- [ ] Thread `movement_profile_id` through `application/movement_reach.py`,
  `WarhammerCompanionService`, `MovementReachState`, web routes, web template, and desktop screen.
- [ ] Include movement profile, effective move distance, algorithm version, and resolution in input
  identity and assumptions. Include traversal policy and endpoint occupancy policy in the identity.
- [ ] Render selected endpoint route geometry when available.
- [ ] Use cautious copy: "estimated route" and "selected movement assumptions"; avoid legal/safe
  claims. Also avoid `optimal`, `recommended`, `guaranteed`, `can charge`, and unqualified
  `reachable`; endpoint diagnostics must say "route-connected under selected assumptions".
- [ ] Browser fixture for Movement Reach:
  - use a deterministic seeded packet or add a test-only seed route with a dense feature between
    start `(12, 12)` and target `(24, 12)`;
  - submit `ground-non-mobile` with a movement distance that routes around successfully and verify a
    route line appears;
  - submit `ground-non-mobile` with an over-budget movement distance and verify the endpoint
    diagnostic changes;
  - submit `ground-mobile` and verify the route/hash/status differs from non-mobile;
  - submit `fly-take-to-skies` and verify effective movement text shows a 2 inch reduction.
  - submit `fly-hover-take-to-skies` and verify effective movement text shows no 2 inch reduction
    and the rendered result differs from the penalized Fly profile.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
```

## Phase 4: Threat Range Propagation

- [ ] Thread `movement_profile_id` through `los/threat.py` and `application/threat_range.py`.
- [ ] Update threat distribution payloads to expose effective movement distance for move-plus-range
  modes.
- [ ] Include movement profile id, effective movement distance, algorithm version, route
  resolution/tolerance, traversal policy, and endpoint occupancy policy in threat input hashes for
  move-plus-range modes. For `raw-range`, record profile-invariant movement metadata as not
  applicable and preserve raw geometry behavior.
- [ ] Thread the selected profile through Threat Range service state, web routes/template, and
  desktop screen.
- [ ] Keep `raw-range` outputs profile-invariant in tests and code.
- [ ] Browser fixture for Threat Range:
  - use the same dense-feature-between-source-and-target scenario;
  - assert selected profile changes result hash and visible probability/effective reach for
    move-plus-range;
  - assert a target point outside non-mobile route budget becomes threatened for `ground-mobile`;
  - assert Take to the Skies 2 inch penalty can reduce the same point below the threatened
    threshold;
  - assert Hover/no-cost Take to the Skies restores the same point above the threatened threshold;
  - assert `raw-range` does not change rendered probability when profile changes.
- [ ] Run a consultant and adversarial review gate after Threat Range propagation. Required focus:
  movement profile reaches actual geometry, not just state/hash/UI, and `raw-range` stays invariant.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py tests\test_threat_range_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
```

## Phase 5: Downstream Propagation

- [ ] Add `enemy_movement_profile_id` to Deployment Exposure service inputs, state, input identity,
  web routes/template, and desktop coverage where present.
- [ ] Add `enemy_movement_profile_id` to Deployment Scorecard service inputs, state, input identity,
  web routes/template, and desktop coverage where present.
- [ ] Add the full movement metadata contract to downstream hashes: enemy movement profile id,
  effective movement distance, routing algorithm version, route resolution/tolerance, traversal
  policy, and endpoint occupancy policy.
- [ ] Update warnings/assumptions to say enemy threat projections use selected movement assumptions.
- [ ] Explicitly inspect desktop surfaces. If Deployment Exposure or Deployment Scorecard has a
  desktop screen, add profile controls and tests. If no desktop surface exists, document that fact in
  the work log and keep service/web coverage complete.
- [ ] Add tests and Browser checks proving enemy movement profile changes visible downstream
  exposure/scorecard output, probability, blocked/estimated status, or score component. Hash-only
  proof is not sufficient.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
```

## Phase 6: Documentation And Manual Browser QA

- [ ] Update `docs/qa-scenarios.md` with the movement-profile Browser scenario, page 9/page 52
  performance smoke expectations, and fallback procedure.
- [ ] Update `docs/work-log/player-toolkit-implementation.md` with design decisions, test evidence,
  reviewer outcomes, and remaining non-goals.
- [ ] Restart the local app after code changes.
- [ ] Use the built-in Browser against `http://127.0.0.1:8000/movement-reach`:
  - verify the Movement Profile selector is visible;
  - submit `ground-non-mobile`, `ground-mobile`, `fly-take-to-skies`, and
    `fly-hover-take-to-skies`;
  - verify selected values persist and result status remains user-facing;
  - verify route geometry, endpoint diagnostic, result hash, and effective movement text change
    under the deterministic dense-blocker scenario;
  - verify Hover/no-cost Take to the Skies visibly differs from penalized Take to the Skies;
  - verify the page text avoids legal/safe claims.
- [ ] Use the built-in Browser against `http://127.0.0.1:8000/threat-range`:
  - verify the Movement Profile selector is visible;
  - submit `fixed-move-plus-range` with each profile;
  - verify Take to the Skies shows a reduced effective movement/reach summary;
  - verify Hover/no-cost Take to the Skies shows the unreduced effective movement/reach summary;
  - verify `raw-range` remains profile-invariant in page state.
- [ ] Use the built-in Browser against Deployment Exposure and Deployment Scorecard:
  - verify enemy movement profile controls are visible and preserve values;
  - verify selected profile changes visible result output, probability, blocked/estimated status, or
    score component under the deterministic dense-blocker scenario. Hash-only proof is not
    sufficient.
- [ ] Use desktop QA or smoke-test assertions to prove Movement Reach and Threat Range visibly
  represent profile behavior:
  - profile combo population and selected value;
  - non-mobile route-around diagnostic or route output;
  - mobile pass-through output;
  - penalized Fly versus no-cost Hover effective movement text.
  If Computer Use is unavailable, assert the same screen state through PySide smoke tests and record
  the blocker.
- [ ] If Browser control fails, try Computer Use with Firefox and record exact blocker/fallback
  evidence.

## Phase 7: Review, Full Validation, And Commit

- [ ] Run adversarial implementation review. Required reviewer verdict format:
  `APPROVED` or `CHANGES_REQUIRED`, with concrete file/line risks.
- [ ] Fix all `CHANGES_REQUIRED` issues and rerun targeted tests plus Browser QA.
- [ ] Run full validation:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_threat_range_geometry.py -q -k "page_9 or page_52"
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

- [ ] Run a protected-artifact scan before staging. Do not stage `AGENTS.md`, generated logs, raw
  PDFs, processed packets, caches, databases, build outputs, packaged artifacts, screenshots,
  credentials, Codex state, `data/raw/`, `data/processed/`, `data/cache/`, `build/`, `dist/`, or
  `.venv/`.
- [ ] Commit atomically with:

```text
Implement movement profile aware routing
```
