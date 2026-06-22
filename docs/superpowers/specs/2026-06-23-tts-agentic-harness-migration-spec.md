# TTS And Agentic Harness Migration Spec

Date: 2026-06-23

## Status

Drafted from:

- `docs/tts-pivot-research.md`
- `docs/agentic-self-play-harness-research.md`
- repository `AGENTS.md`

This is a product and architecture specification for a phased migration. It does not implement code
and does not authorize bundling official Games Workshop PDFs, raw TTS saves, raw rosters, generated
logs, or user credentials.

## Decision

Move the project toward a TTS-first companion and agentic supervised self-play harness while keeping
the durable product engine in Python.

The migration has two linked tracks:

- **TTS bridge track:** prove that Tabletop Simulator can provide live board state, selected-object
  LOS probes, controlled object mutations, Hutber dice events, and companion-service round trips.
- **Agentic harness track:** build information, belief, event, protocol, and execution contracts so
  two private LLM-powered agents can play supervised self-play scenarios through typed actions.

Lua should own in-game TTS interaction. Python should own domain models, source trust, probability
records, orchestration, validation, replay, reporting, and fallback analysis.

## Goals

- Preserve the current Python-first architecture and existing LOS/rendering work.
- Use TTS as the source of live table state where possible.
- Avoid a full Lua rewrite unless the product goal changes to Workshop-only limited tooling.
- Build a controlled TTS feasibility harness before deeper migration.
- Create typed data contracts for TTS board snapshots, action execution, event intake, belief
  updates, supervised self-play, and replay.
- Keep the MVP scoped to prepared development rosters, movement, scoring, shooting, Hutber dice,
  and supervisor approval.
- Leave a clean path from pragmatic probability records to formal Bayesian updates.

## Non-Goals

- No custom frontend JavaScript or web framework migration.
- No direct LLM manipulation of TTS objects.
- No live human-opponent product surface in the MVP.
- No arbitrary roster import in the self-play MVP.
- No full mission-pack support in the first self-play MVP.
- No melee, battleshock, transports, reserves, deep strike, broad stratagem coverage, or complex
  mortal-wound timing in the first self-play MVP.
- No C or Rust LOS side engine until proxy geometry and transform gates prove it is needed.
- No committed official PDFs, raw TTS saves, raw rosters, screenshots, replay logs, caches, or
  credentials.

## Architecture Boundaries

The existing repository boundaries still apply:

- Domain records live under `src/warhammer_companion/domain/`.
- Reusable orchestration lives under `src/warhammer_companion/application/`.
- LOS and geometry algorithms live under `src/warhammer_companion/los/`.
- SVG/raster rendering lives under `src/warhammer_companion/rendering/`.
- Official-source registries and ingestion artifacts live under `src/warhammer_companion/ingestion/`.
- Web and desktop remain thin adapters.

New Python contracts should follow the same split:

- `domain`: immutable data records for TTS snapshots, event envelopes, actions, belief variables,
  protocol states, and self-play sessions.
- `application`: services that normalize TTS snapshots, validate actions, run protocol reducers,
  update belief state, and coordinate supervised execution.
- `los`: reusable geometry and fallback LOS algorithms, not TTS-specific orchestration.
- `rendering`: companion-side visualizations and fallback raster/overlay rendering.
- `web` and `desktop`: optional supervisor and diagnostics adapters, not owners of product logic.

Lua artifacts should start as harness assets for controlled TTS saves. Generated or real TTS saves
are local artifacts, not repository data.

## System Overview

```text
TTS Global Lua Harness
  -> object discovery
  -> selected-object probes
  -> Hutber dice integration
  -> whitelisted action executor
  -> chat/action declarations
  -> local companion HTTP calls

Python Companion Engine
  -> TtsBoardSnapshot normalization
  -> TtsBoardTransform validation
  -> TTS event intake
  -> ToolkitResult and overlay reuse
  -> belief and probability records
  -> typed action validation
  -> supervised self-play protocol reducers
  -> replay and correction log

Supervisor Surface
  -> approvals
  -> corrections
  -> diagnostics
  -> replay inspection
```

## Core Contracts

### TtsBoardSnapshot

`TtsBoardSnapshot` is the normalized board observation from TTS.

Required fields:

- snapshot id;
- source save/session id;
- host/local companion marker;
- capture timestamp;
- `TtsBoardTransform`;
- observed objects;
- selected objects, if any;
- source warnings;
- schema version.

Every field derived from TTS should carry one of:

- `observed`: direct TTS value;
- `inferred`: derived by companion logic;
- `manual`: operator correction or manual tag;
- `unsupported`: known missing field.

The MVP snapshot may be incomplete. It must not claim exact gameplay footprints, true meshes, or
terrain semantics unless a later phase proves those fields.

### TtsBoardTransform

`TtsBoardTransform` maps TTS world coordinates to battlefield inches.

Required fields:

- TTS origin;
- battlefield origin;
- board rotation;
- scale to 44 x 60 inches;
- board bounds;
- transform version;
- calibration points;
- round-trip tolerance;
- validation result.

Acceptance requires known TTS placements to round-trip to battlefield inches within an explicitly
recorded tolerance.

### TtsObjectRef

`TtsObjectRef` represents a live TTS object.

Required fields:

- GUID;
- name;
- tags;
- object kind candidate;
- owning side candidate;
- position;
- rotation;
- scale;
- bounds;
- visual bounds when available;
- source classification: observed, inferred, or manual;
- warnings.

MVP object kinds:

- model;
- terrain;
- objective;
- marker;
- dice or dice-result source;
- unknown.

### TtsLosProbe

`TtsLosProbe` records a native TTS physics LOS check.

Required fields:

- probe id;
- attacker object GUID;
- target object GUID;
- origin point;
- target point;
- cast kind: ray, sphere, or box;
- ignored GUIDs;
- hit records;
- visible beam marker id when drawn;
- readiness: diagnostic until calibrated;
- warnings;
- latency/cast-count metadata.

TTS physics casts are collider based. They are diagnostic until the LOS calibration gate passes on
representative tables.

### EventEnvelope

All state changes flow through append-only events.

Required fields:

- event id;
- event type;
- status: provisional, confirmed, rejected, or corrected;
- actor side;
- source;
- visibility: public, side_private, or supervisor;
- protocol instance id;
- protocol step;
- input state version;
- output state version;
- correlation id;
- payload;
- verifier result;
- correction or rollback link;
- timestamp;
- schema version.

State should be reconstructed by deterministic reducers from the event stream. Direct mutation of
state without an event is out of scope.

Event status rules:

- `provisional`: observed but not yet verifier/supervisor accepted.
- `confirmed`: accepted and safe for deterministic reducers.
- `rejected`: preserved for audit but ignored by reducers and belief updates unless explicitly cited
  as counterevidence.
- `corrected`: superseded by a later `StateCorrection` or `ManualRuling`.

Reducers apply only confirmed events by default. Provisional events can affect belief state only when
the dependent `BeliefVariable` records the provisional evidence explicitly. Event status transitions
are append-only events; the original event is not edited in place.

### AgentView

Each planner receives an `AgentView`, not the raw supervisor state.

```text
AgentView = shared_public_state + own_private_state + own_belief_store
```

Rules:

- Agents can read public state.
- Agents can read their own private state.
- Agents cannot read opponent private plans, opponent utility estimates, or side-private belief
  records.
- The supervisor can inspect all views.

### AgentPrivateState

`AgentPrivateState` is the durable side-private planning record. It is referenced by `AgentView`,
but never copied into the public event stream.

Required fields:

- session id;
- side;
- owner agent id;
- private plan refs;
- candidate action refs;
- utility records;
- risk posture;
- private belief refs;
- visibility: side_private;
- schema version.

Acceptance requires view tests proving each `AgentView` excludes the opponent's `AgentPrivateState`,
private belief records, utility estimates, and unsubmitted candidate actions.

### BeliefVariable

`BeliefVariable` keeps the probability layer inspectable and migratable to formal Bayesian updates.

Required fields:

- id;
- subject;
- value space;
- current distribution;
- evidence refs;
- update history;
- confidence;
- visibility;
- calibration notes.

Each update history entry includes:

- prior distribution;
- evidence event ids;
- update method: heuristic, simulation, or bayesian;
- method version;
- posterior distribution;
- calibration notes.

MVP updates may be heuristic, but they must use the same structure as later formal Bayesian updates.

### ActionProposal

The LLM chooses typed action proposals, not direct TTS operations.

Required fields:

- proposal id;
- side;
- protocol instance id;
- step name;
- typed parameters;
- target GUIDs;
- preconditions;
- expected public effects;
- belief refs used;
- validator result;
- readiness;
- warnings.

### ApprovedAction

`ApprovedAction` is the execution-ready form of an action.

Required fields:

- approved action id;
- proposal id;
- dry-run id;
- input state version;
- input snapshot hash;
- target GUID hash;
- supervisor approval token;
- approval expiry;
- executor target;
- dry-run result;
- execute result;
- event correlation id;
- binding validation result;
- verifier result.

The bridge executes only `ApprovedAction` records. Before mutating TTS, execution must revalidate
that the approval token is bound to the proposal id, dry-run id, input state version or snapshot
hash, target GUID hash, and expiry. Stale, replayed, or mismatched approvals fail closed and emit a
rejected event.

## TTS Bridge Contract

The first TTS bridge is intentionally narrow:

- one controlled test save;
- one Global Lua harness script;
- whitelisted JSON action payloads;
- GUID-targeted operations only;
- `dry_run -> supervisor_approve -> execute`;
- structured success/error response;
- explicit timeouts;
- `WebRequest.custom` POST with `Content-Type: application/json` for JSON payloads;
- chat declarations with `action_id`, side, phase, action type, target GUIDs where applicable, and
  human-readable text.

The host must run the local companion for companion-backed features. In hosted multiplayer,
`127.0.0.1` refers to the host machine.

Do not implement JSON bridge calls with TTS `WebRequest.post`; that helper sends form-encoded
payloads. JSON bridge calls must use `WebRequest.custom` so the harness can set headers, body,
response handling, status-code handling, timeout behavior, and structured errors consistently.
Implementation reference: TTS API WebRequest Manager,
`https://api.tabletopsimulator.com/webrequest/manager/`.

## Hutber Dice Contract

Hutber dice integration is the primary gameplay dice path for shooting. Phase 3 is a branch gate:

- if the Hutber round trip passes, Phase 5 shooting must use Hutber dice;
- if the Hutber round trip is blocked, Phase 5 may use supervisor-entered dice only with
  `source=fallback_supervisor_entry`, explicit warning labels, and no claim that Hutber integration
  is working.

Before shooting uses Hutber dice in the harness, prove one round trip on a representative save:

- requested action id;
- side/player;
- phase/protocol step;
- raw source payload;
- parsed dice values;
- duplicate-protection marker;
- `DiceRolled` event;
- verifier result.

If direct Hutber integration is blocked, the MVP may use supervisor-entered dice only as a
documented fallback. It should not silently switch to an internal dice service for gameplay.

## Execution And Rollback

MVP TTS-mutating actions require supervisor approval.

Required verifier checks:

- expected GUIDs moved or changed;
- expected dice result captured;
- expected models moved to casualty zone or removed;
- phase/score state changed as expected;
- replay event appended.

Direct deletion is disabled until rollback is tested. Prefer moving casualties to a casualty zone
for MVP recovery.

Rollback options:

- snapshot-backed inverse operations;
- controlled-save reload;
- supervisor `StateCorrection`;
- supervisor `ManualRuling`.

Rollback itself must emit events.

## Data Guardrails

Local/generated data stays out of source control.

Never commit:

- raw TTS saves;
- raw rosters;
- official PDFs;
- screenshots;
- generated replay logs;
- generated snapshots;
- caches;
- SQLite/database files;
- Codex/OpenAI auth files;
- local secrets.

Committed fixtures must be sanitized minimal JSON with protected source text removed.

## MVP Rules Profile

The self-play MVP uses one pinned `RulesSourceTuple`. This tuple is a Phase 0/1 deliverable before
gameplay implementation acceptance. No phase may depend on "current rules" without resolving the
tuple first.

Each `RulesSourceTuple` entry records:

- edition id;
- source name;
- publisher or domain;
- URL or local source kind;
- release date, update date, or version id;
- retrieval timestamp for remote sources;
- content hash if locally cached;
- local artifact id or fixture id;
- source-trust label.

Required tuple entries for the MVP:

- core rules source;
- one fixed event companion mission/terrain layout source;
- prepared development roster fixture source;
- weapons, profiles, base sizes, and named effects source for those prepared rosters;
- points/profile source for those prepared rosters;
- one scripted non-tournament scoring rule fixture.

The first scoring proof is deliberately narrow: at end of active player turn, score a fixed VP value
if the side controls a designated terrain objective. Full mission scoring is deferred.

Official source PDFs remain user/local inputs and are not committed.

## Protocols

### Movement MVP

Only `NormalMove` is in scope for the first playable loop.

Events:

- `UnitSelectedForPhaseAction`;
- `MovementDeclared(mode=NormalMove)`;
- `MovementResolved`;
- `StateCorrection` if observed board state does not match expected board state.

Out of scope:

- Advance;
- Fall Back;
- charge;
- pile-in/consolidate;
- transports;
- reserves;
- disembark;
- vertical/3D legality beyond prepared-scenario assumptions.

### Shooting MVP

Shooting is a protocol, not one atomic action. The first shooting proof is constrained to one named
simple attack group:

- identical attacking model and weapon profiles;
- one target unit;
- no mixed saves;
- no multi-damage allocation;
- no multi-wound allocation;
- no Precision or special allocation rules;
- no FnP or similar post-save rolls;
- no reactive stratagems or abilities unless a later prepared-roster proof explicitly adds them.

```text
ShootingActivation
  -> UnitSelectedToShoot
  -> AttackerAllocatesWeaponsAndTargets
  -> ValidateShootingEligibility
  -> AttackerDeclaresNamedPreparedRosterEffects
  -> DefenderDeclaresNamedPreparedRosterEffects
  -> AttackerRollsHits
  -> AttackerRollsWounds
  -> DefenderRollsSaves
  -> DefenderSelectsCasualties
  -> DefenderRemovesModels
  -> PostAttackStateVerified
```

Only effects named in the prepared rosters are available. FnP-like abilities, multi-damage
allocation, mixed saves, and special allocation rules are later prepared-roster extensions, not part
of the first shooting proof.

Out of scope:

- general stratagem coverage;
- battleshock;
- melee;
- mortal/devastating wound edge cases;
- FnP-like post-save rolls in the first proof;
- transports/reserves interactions;
- arbitrary weapon/profile parsing.

### Scoring MVP

Scoring is one scripted proof protocol:

- select active player;
- compute designated terrain objective control;
- emit `ObjectiveScored`;
- update generic VP/win-proxy belief variables;
- verify score event and state version.

Full primary/secondary mission packs are final-product work.

## Bayesian And Planning Model

The architecture is Bayesian in direction but pragmatic in the MVP.

MVP planner inputs:

- public board state;
- side-private belief variables;
- deterministic toolkit outputs;
- probability distributions for shooting and scoring;
- action proposals generated from active protocol state.

MVP objective:

- maximize expected VP/win proxy;
- preserve useful units;
- remove enemy units;
- improve future scoring position;
- avoid illegal or unverified actions.

Later phases can replace heuristic belief updates with formal Bayesian updates without replacing
the event, belief, and replay contracts.

## Phased Migration Roadmap

### Phase 0 - Spec, Fixtures, And Safety Baseline

Goal: prepare the repository for TTS and self-play work without changing runtime behavior.

Scope:

- this spec;
- sanitized fixture policy;
- ignored local data paths for TTS harness artifacts;
- `RulesSourceTuple` schema and initial source ledger;
- representative fixture schema drafts;
- development roster fixture outline.

Acceptance:

- spec reviewed and accepted;
- fixture paths do not encourage committing raw TTS saves or raw rosters;
- rules-source requirements are explicit and no gameplay phase relies on unpinned "current" rules;
- no runtime behavior changes.

### Phase 1 - TTS Feasibility Harness

Goal: prove the TTS bridge can observe and act in one controlled save.

Scope:

- minimal Global Lua harness script;
- `TtsBoardSnapshot v0`;
- `TtsBoardTransform`;
- three tagged objects: attacker, target, terrain;
- one diagnostic `Physics.cast` LOS probe;
- one visible beam and hit marker;
- local companion JSON round trip through `WebRequest.custom`;
- sanitized snapshot fixture.

Acceptance:

- schema-valid snapshot reaches companion;
- board transform round-trips known placements within recorded tolerance;
- visible beam matches reported cast path;
- host-only companion behavior is documented;
- JSON requests use `WebRequest.custom` with explicit headers, response-code handling, and
  structured error handling;
- LOS result is labeled diagnostic.

### Phase 2 - TTS Action Bridge And Replay Core

Goal: introduce typed execution without self-play planning.

Scope:

- `EventEnvelope`;
- `ActionProposal`;
- `ApprovedAction`;
- dry-run/approve/execute bridge;
- append-only replay log;
- reducer-driven state update;
- rollback proof for movement and casualty-zone transfer.

Acceptance:

- approved `NormalMove` mutates the controlled save;
- replay records before/after state refs;
- rollback restores or corrects bad movement;
- direct deletion remains disabled until restore proof exists.

### Phase 3 - Hutber Dice And Shooting Protocol Proof

Goal: prove dice and shooting events can be captured and replayed.

Scope:

- Hutber dice round-trip fixture gate;
- documented fallback branch if Hutber is blocked;
- `DiceRolled` event;
- duplicate protection;
- shooting protocol reducer;
- simple attack-group weapon/target allocation for prepared rosters;
- defender save and casualty-selection handoff.

Acceptance:

- one shooting interaction executes through the protocol;
- either Hutber dice output is parsed into structured events, or the fallback branch is explicitly
  selected with `source=fallback_supervisor_entry` and warning labels;
- defender controls saves and casualty choice;
- casualty movement is verified;
- replay can reconstruct the interaction.

### Phase 4 - Information And Belief Harness

Goal: connect toolkit outputs, event state, and probability records.

Scope:

- `AgentView`;
- `AgentPrivateState`;
- `BeliefVariable`;
- belief update history;
- public/private visibility labels;
- movement/scoring/shooting probability records;
- generic VP/win-proxy objective.

Acceptance:

- each side receives only its allowed view;
- view tests prove opponent private state is excluded;
- belief updates cite event evidence;
- heuristic updates leave migration path to formal Bayesian updates;
- planner can compare 2-4 candidate actions in a controlled state.

### Phase 5 - Supervised Two-Agent Self-Play MVP

Goal: run the first supervised self-play loop.

Scope:

- two private agents;
- prepared mini-forces;
- `NormalMove`;
- scripted non-tournament scoring proof;
- one simple attack-group shooting interaction with Hutber dice, or documented supervisor-entered
  dice fallback if the Phase 3 Hutber gate was blocked;
- supervisor approval before every TTS mutation;
- approval-token revalidation before every TTS mutation;
- post-action verification;
- replay log and correction path.

Acceptance:

- both agents maintain private planning state;
- both agents consume public events;
- supervisor approves each mutation;
- stale or replayed approval tokens fail closed;
- event intake updates belief state after friendly and opponent actions;
- the system can replan after a dice or board-state change.

### Phase 6 - TTS Toolkit Expansion

Goal: expand from MVP proof to useful TTS companion tooling.

Scope candidates:

- selected-model LOS checker;
- unit visibility summary;
- terrain collider/proxy audit;
- threat/range overlays;
- hidden/staging overlays;
- roster-object linking workflow;
- Phase 0/1 War Organ, Hutber, ForceOrg adapters based on representative fixtures.

Acceptance:

- additions reuse the snapshot, event, belief, and action contracts;
- no tool bypasses readiness or source trust;
- batch-heavy work runs in Python companion, not Lua-only loops.

### Phase 7 - Final-Product Expansion

Goal: move beyond controlled self-play fixtures.

Scope candidates:

- arbitrary valid army lists;
- full mission packs with primary and secondary missions;
- melee protocols;
- battleshock;
- transports, reserves, deep strike, disembark;
- broader stratagem/reactive ability coverage;
- live human-opponent UI;
- lower-friction packaging.

Acceptance:

- each expansion has source/version/freshness gates;
- each new protocol has reducer, event, verifier, rollback, and tests;
- human-facing UI does not compromise agent privacy, source trust, or data guardrails.

## Review And QA Gates

Every implementation phase should include:

- focused unit tests for new domain records and reducers;
- application-service tests for orchestration;
- fixture tests using sanitized JSON;
- protected-artifact scan;
- `ruff format --check src tests`;
- `ruff check .`;
- `mypy src` when production Python changes;
- targeted pytest for touched services;
- desktop smoke when desktop surfaces change;
- browser/manual QA when web routes, HTML, SVG, or visual layout change;
- adversarial review for new protocol or trust boundaries.

TTS-specific manual QA should record:

- TTS version;
- mod/save used;
- host machine behavior;
- whether remote clients need local services;
- cast count and interaction latency;
- Hutber dice capture path;
- rollback result.

## Open Questions

- Which controlled TTS save should be the first harness target?
- Which Hutber dice output path is easiest to capture reliably?
- Where should local TTS harness artifacts live so generated data stays ignored?
- What tolerance is acceptable for TTS-to-battlefield coordinate round trips?
- Should the first supervisor surface be CLI-only, web, desktop, or log-driven?
- Which prepared mini-forces should define the first shooting protocol proof?
- Which named prepared-roster effects are in MVP scope, if any?

## Acceptance Criteria For This Spec

- Captures the TTS pivot and self-play harness research in one migration roadmap.
- Preserves Python-first durable engine boundaries.
- Defines core contracts needed before implementation planning.
- Splits work into phases with goals, scope, and acceptance criteria.
- Keeps MVP constrained to prepared rosters, `NormalMove`, scripted scoring, shooting, Hutber dice,
  supervisor approval, and replayable events.
- Defers arbitrary rosters, full missions, melee, complex abilities, live human-opponent UI, and
  side engines.
- Includes data guardrails and verification expectations.
