# Agentic Self-Play Harness Research Note

Date: 2026-06-22

## Decision

The long-term agentic direction should be a supervised two-agent self-play harness. The target is
not only tactical advice: each LLM-powered agent should be able to observe the table, plan, execute
typed game actions in TTS, process the opponent's actions, update probabilities, and continue play
under supervisor control.

The first autonomous-play target is not live play against a human opponent. That requires a
human-facing UI and stronger social/recovery guarantees. Start with two autonomous agents playing
opposing prepared forces in a controlled TTS save, with a supervisor approving mutating actions and
resolving ambiguity.

## Core Architecture

The harness should be event-driven and split into four cooperating layers:

```text
TTS table + Hutber tooling
  -> event intake and board observer
  -> information and belief harness
  -> private agent planners
  -> typed execution harness
  -> post-action verifier
  -> replay and correction log
```

Key ownership:

- **Shared public state:** board snapshot, rosters, mission/scenario state, dice events, public
  declarations, visible model positions, score, and public event log.
- **Agent private state:** strategy, candidate plans, utility estimates, risk posture, and hidden
  deliberation for one side only.
- **Supervisor state:** complete logs, approvals, corrections, rollback records, and evaluation
  metrics.
- **Execution layer:** the only layer allowed to mutate TTS objects, roll dice, remove models, or
  post chat declarations.

Each planner should receive an `AgentView`, not the raw supervisor state:

```text
AgentView = shared_public_state + own_private_state + own_belief_store
```

Every event and belief record needs a visibility label: `public`, `side_private`, or `supervisor`.
The supervisor may inspect all views. A planner may not inspect the opposing agent's private state,
candidate plans, utility estimates, or side-private belief records.

The LLM must not directly manipulate TTS objects. It should choose from typed actions and typed
protocol steps. Validators, approval gates, and verifiers decide whether those actions can mutate
the table.

State should be reconstructed from append-only events through deterministic reducers. Each event is
wrapped in an `EventEnvelope` with event id, actor side, source, visibility, protocol instance id,
protocol step, input state version, output state version, correlation id, verifier result, and
optional correction/rollback link.

## Information And Belief Harness

The information harness maintains the agent's game understanding:

- current TTS board snapshot;
- canonical game state;
- observed, inferred, unknown, and manually corrected fields;
- LOS, movement, threat, damage, scoring, and heatmap tool outputs;
- probability distributions for likely outcomes;
- event-driven updates after dice rolls, opponent actions, failed checks, or supervisor rulings.

This should be Bayesian in direction, but pragmatic in the MVP. Early versions can use structured
probability records without implementing a full formal Bayesian update engine.

Use records shaped like:

```text
BeliefVariable
  id
  subject
  value_space
  current_distribution
  evidence_refs
  update_history
  confidence
```

Allowed MVP distributions:

- boolean state with confidence;
- categorical probabilities;
- numeric distributions;
- sampled outcome pairs such as damage/probability;
- expected VP or scoring probability ranges.

Avoid loose prose scores or planner-only probabilities that tools cannot inspect. The future formal
Bayesian model should be able to enrich the same belief variables, evidence references, and update
history rather than replace the harness.

Each update history entry should store the prior distribution, evidence event ids, update method
(`heuristic`, `simulation`, or `bayesian`), method version, posterior distribution, and calibration
notes. MVP updates can be heuristic, but they should still leave a migration path to explicit
priors, likelihoods, and posterior snapshots.

## Event Intake Layer

The information harness must ingest events from both sides, not just its own execution outputs.
Opponent declarations and TTS actions should be classified into typed game events before they update
belief state.

Examples:

- `ActionDeclared`
- `UnitSelectedForPhaseAction`
- `MovementDeclared`
- `MovementResolved`
- `UnitMoved`
- `TargetsDeclared`
- `DiceRolled`
- `DamageAllocated`
- `ModelsRemoved`
- `ObjectiveScored`
- `PhaseAdvanced`
- `ManualRuling`
- `StateCorrection`

If an opponent declares "I activate unit X and make a normal move," the event intake layer should
classify it as `UnitSelectedForPhaseAction` plus `MovementDeclared(mode=NormalMove)`, watch for the
resulting board-state change, append `MovementResolved`, refresh relevant probabilities, and trigger
replanning if the current plan is affected.

Declaration, board delta, dice output, and supervisor ruling can disagree. Observed deltas should
first become provisional events. The verifier or supervisor then confirms them, appends a
`StateCorrection`, or appends a `ManualRuling`. Belief updates should consume confirmed events by
default; provisional events are allowed only when explicitly marked as such in the dependent belief
record.

## Execution Harness

The execution harness turns approved decisions into TTS actions:

- moving models;
- declaring actions in chat;
- selecting targets;
- invoking Hutber dice roller machinery;
- recording dice results;
- assigning damage;
- removing or moving casualty models;
- advancing phase/turn state;
- verifying the table after each mutation.

TTS supports object manipulation and chat/message functions, so action execution and public
declarations should happen through Lua bridge calls. Hutber's Lua dice roller should be used for
gameplay rolls where available. Dice outputs must be captured as structured `DiceRolled` events with
source metadata such as `hutber_dice`.

The bridge contract should be narrow:

- a controlled test save with a Global Lua harness script;
- whitelisted JSON actions only;
- GUID-targeted operations;
- `dry_run -> supervisor_approve -> execute`;
- structured success/error responses with timeouts;
- chat declarations that include `action_id`, side, phase, action type, relevant target GUIDs, and
  human-readable text.

Typed actions should move through explicit records:

```text
ActionProposal
  side
  protocol_instance_id
  step_name
  typed_parameters
  target_guids
  preconditions
  expected_public_effects
  belief_refs_used
  validator_result

ApprovedAction
  proposal_id
  supervisor_approval_token
  executor_result
```

Before shooting depends on Hutber dice, the harness must prove one Hutber roll round trip on a
representative save: action id, raw source payload, parsed dice, player/side, phase, and duplicate
protection.

For model removal, prefer moving models to a casualty zone during early harness work because it is
more recoverable than permanent deletion. Direct deletion can be supported later or when a mod
convention requires it. In either case, removal must be GUID-specific and post-action verified.

Direct deletion should remain disabled until rollback is tested. MVP rollback should use
snapshot-backed inverse operations or controlled-save reload for bad moves, casualty-zone transfers,
dice-action misreads, and phase/score mistakes.

## MVP Scope

The MVP should support supervised self-play with:

- two private agents playing opposing sides;
- one pinned rules profile: 11th edition free core rules, one fixed Event Companion
  mission/terrain layout, and prepared development rosters;
- prepared development rosters only;
- known unit profiles, weapons, base sizes, and TTS object mappings;
- movement, scoring, and shooting;
- Hutber dice roller integration;
- generic objective: maximize expected VP / win-proxy;
- supervisor approval before every TTS-mutating action;
- replay log and correction path.

Prepared rosters should be deliberately small and designed for development. Arbitrary valid army
lists are a final-product requirement, not an MVP requirement.

The generic MVP objective can reward:

- holding objectives;
- denying opponent objectives;
- preserving useful units;
- removing enemy units;
- improving future scoring position.

For the first scoring proof, use one scripted non-tournament scoring rule, such as end of active
player turn: score a fixed VP value if the side controls a designated terrain objective. Full
mission rules are deferred.

Full mission-pack support should later replace the generic objective with primary and secondary
mission protocols for both players.

## Shooting Protocol

Shooting should not be implemented as one atomic `resolve_shooting` action. It should mirror real
play as an alternating protocol:

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
  -> DefenderRollsFnPOrSimilar
  -> DefenderSelectsCasualties
  -> DefenderRemovesModels
  -> PostAttackStateVerified
```

Each step emits typed events. The attacking agent should not roll defender saves or decide defender
casualties in the normal protocol. Shortcuts may exist for isolated tests, but the gameplay harness
should preserve control handoff between attacker and defender.

Only named effects in the prepared development rosters should be available in the MVP. FnP-like
abilities can be included only if one prepared roster needs them. General battleshock, melee,
mortal-wound edge cases, transports, reserves, and unusual timing interactions are deferred.

## Approval And Verification

The first playable harness should require supervisor approval before every TTS-mutating action.
This is slower, but it prevents early automation bugs from corrupting the table.

Later versions can auto-execute low-risk, high-confidence actions. Post-action verification should
remain mandatory:

- expected objects moved to expected positions;
- expected dice result captured;
- expected model GUIDs removed or moved to casualty zone;
- score and phase state changed as expected;
- replay log appended with before/after state references.

Every correction should become a typed `StateCorrection` or `ManualRuling` event so the belief
harness and replay log stay coherent.

Generated replay logs, snapshots, TTS payloads, chat captures, and dice payloads should stay under
ignored local data/log paths. Committed fixtures must be sanitized minimal JSON. Do not commit raw
TTS saves, screenshots, raw rosters, official PDFs, caches, Codex/OpenAI auth, or local secrets.

## Deferred Scope

Defer these until the core supervised self-play loop is proven:

- live play against a human opponent;
- arbitrary roster import and legality checks;
- full primary/secondary mission pack support;
- melee protocols;
- battleshock;
- transports, reserves, deep strike, and disembark timing;
- complex mortal-wound/devastating-wound interactions;
- broad stratagem and reactive ability coverage;
- fully unattended games;
- polished human-facing UI.

## First Milestone

The first development milestone should prove one narrow loop:

- one controlled TTS test save;
- two prepared mini-forces;
- one `NormalMove` action with `MovementDeclared` and `MovementResolved` events;
- one scripted non-tournament scoring update;
- one shooting interaction using Hutber dice;
- defender-controlled saves and casualty selection;
- supervisor approval before each table mutation;
- chat declaration for each public action;
- post-action verification;
- replay log with typed events and before/after state refs.

Success means the system can observe, plan, ask approval, execute, verify, update beliefs, and
replan in a controlled self-play scenario.

## Recommendation

Write the next implementation plan around a supervised self-play harness, not a general gameplay
agent. Build the information harness and execution harness together, connected by typed events. Keep
the probability model structured enough to evolve into formal Bayesian planning, but constrain the
first playable loop to prepared rosters, movement, scoring, shooting, Hutber dice, supervisor
approval, and replayable state transitions.
