# TTS Implementation Infrastructure Spec

Date: 2026-06-23

## Status

Short implementation-readiness spec for the TTS bridge and supervised self-play harness roadmap.
This document complements `2026-06-23-tts-agentic-harness-migration-spec.md`; it does not replace
that roadmap or authorize committing raw TTS saves, official PDFs, raw rosters, generated replay
logs, screenshots, caches, credentials, or user-specific Codex/OpenAI state.

## Decision

Phase 0 can begin without Tabletop Simulator. Phase 1 and later require a functional local TTS
instance on the host machine that can load a controlled development save, run Global Lua, reach the
local Python companion through `WebRequest.custom`, and exercise Hutber dice machinery.

The first LLM/agent runtime should be Codex CLI or an equivalent local Codex runner controlled by
the developer, not an in-game TTS script. The agent runtime must produce typed `ActionProposal`
records and must never mutate TTS directly.

## Required Local Infrastructure

### Tabletop Simulator

Required for Phase 1 onward:

- Steam-installed Tabletop Simulator on the host machine.
- Ability to create and edit a local controlled development save.
- Ability to paste, run, and iterate a Global Lua harness script.
- Windowed or otherwise inspectable TTS session for manual verification.
- Access to representative Hutber, ForceOrg, and War Organ mod assets where relevant.

TTS is not needed for pure Python contract work, fixture schemas, reducer tests, or replay tests.

### Controlled Development Save

The first save should be deliberately small:

- one board with known calibration points;
- one attacker unit;
- one target unit;
- one terrain object;
- one objective marker;
- one casualty zone;
- Hutber dice roller present;
- stable object GUIDs or a documented reset workflow;
- human-readable tags for object kind, side, and fixture role.

The raw save remains local and ignored by git. Committed fixtures should be sanitized JSON snapshots
derived from the save.

### Python Companion Service

The existing Python-first architecture remains the durable engine. The local companion needs:

- FastAPI or equivalent local HTTP endpoints bound to `127.0.0.1`;
- snapshot intake;
- bridge health check;
- action dry-run;
- approval lookup;
- execution result intake;
- dice event intake;
- replay/event log writing to ignored local paths;
- structured errors that distinguish unsupported, blocked, invalid, and verifier-failed states.

The host must run this service for TTS-backed features. In hosted multiplayer, `127.0.0.1` is the
host machine, not each remote client.

### TTS Lua Bridge

The Global Lua harness should start as a narrow bridge:

- object discovery for tagged fixture objects;
- `TtsBoardSnapshot` capture;
- board transform calibration probes;
- diagnostic physics LOS probe and visible marker/beam drawing;
- JSON round trip to the local companion via `WebRequest.custom`;
- whitelisted GUID-targeted actions only;
- `dry_run -> supervisor_approve -> execute`;
- no direct LLM-to-object manipulation;
- no broad Lua rewrite of the Python domain engine.

### Agent Runtime

The first agent infrastructure should use Codex CLI or an equivalent Codex-controlled local runner.
It needs:

- a working directory scoped to this repository;
- access to the Python companion APIs or a local harness adapter;
- ability to call deterministic tools that produce toolkit outputs and probability records;
- a strict output contract for `ActionProposal`;
- no direct TTS scripting, mouse control, or object mutation;
- side-private planning state stored outside the public event stream;
- supervisor approval before any `ApprovedAction` reaches the Lua bridge.

The runtime should be replaceable later. The stable boundary is the typed action, event, belief, and
approval contracts, not Codex CLI itself.

### Secrets And Accounts

Do not commit or package credentials. Required local credentials, if any, stay outside the repo:

- Steam account and local TTS install state;
- Codex/OpenAI auth or API keys;
- GitHub auth used for development;
- local browser/session artifacts.

The app may expose sanitized readiness status, but not credential contents.

## Minimum Implementation Sequence

1. Add ignored local artifact paths for TTS saves, snapshots, replay logs, and harness output.
2. Define sanitized fixture schemas for snapshots, object refs, bridge responses, and dice events.
3. Build companion health and JSON echo endpoints.
4. Build the minimal Global Lua bridge and verify `WebRequest.custom` JSON round trip.
5. Capture one sanitized `TtsBoardSnapshot` from the controlled save.
6. Calibrate `TtsBoardTransform` against known board points.
7. Prove one diagnostic LOS cast and visible marker.
8. Prove Hutber dice capture or explicitly select the documented supervisor-entered fallback.
9. Add agent-runtime stub tests with deterministic agents before enabling LLM proposals.
10. Enable Codex CLI or equivalent runner only after proposal validation, approval binding, and
    replay reducers are testable.

## Acceptance Criteria

Infrastructure is ready to implement Phase 1 when:

- a local TTS host can load the controlled save;
- the local companion responds on `127.0.0.1`;
- Global Lua can send and receive JSON through `WebRequest.custom`;
- tagged fixture objects can be discovered and normalized;
- sanitized fixtures can be generated without committing raw saves or source PDFs;
- Codex CLI or equivalent agent runtime can produce a validated stub `ActionProposal`;
- supervisor approval remains mandatory before any TTS mutation;
- local generated artifacts are ignored by git.

If local TTS is unavailable, continue only with Phase 0 contract and fixture work. Do not claim TTS
bridge feasibility until the local TTS round trip has been observed.
