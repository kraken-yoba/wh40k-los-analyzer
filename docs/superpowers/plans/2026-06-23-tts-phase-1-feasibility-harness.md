# TTS Phase 1 Feasibility Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the code-ready TTS feasibility harness baseline without overclaiming live TTS
feasibility before a real local Tabletop Simulator round trip is observed.

**Architecture:** Keep Python as the durable engine. Add JSON-bound TTS contracts in the domain
layer, companion bridge orchestration in an application module, and thin FastAPI JSON endpoints for
TTS Lua `WebRequest.custom` calls. Lua remains a paste-in controlled-save harness asset; raw TTS
saves, screenshots, logs, and local captures remain ignored.

**Tech Stack:** Python 3.12, Pydantic v2, FastAPI, pytest, Ruff, mypy, Markdown QA records, TTS
Global Lua harness template using `WebRequest.custom`.

---

## Consultant Inputs

- Spec consultant `019ef38f-30f9-70b3-a986-332e68c4ebde`: PASS with concerns. Required explicit
  transform tolerance, snapshot host/local marker, endpoint/error envelope, diagnostic LOS wording,
  Lua asset location, and a no-live-TTS/no-feasibility-claim branch.
- Codebase consultant `019ef38f-4618-7dc2-ac42-3e1be98d38fe`: recommended
  `src/warhammer_companion/domain/tts.py`,
  `src/warhammer_companion/application/tts_bridge.py`, thin `/api/tts/health` and
  `/api/tts/snapshot` routes, `tests/fixtures/tts/minimal_snapshot.json`, and
  `docs/tts/global_lua_echo.lua`.

## Phase 1 Contract Decisions

- Transform axis mapping: TTS `x` maps to battlefield `x`; TTS `z` maps to battlefield `y`; TTS
  `y` is retained as height and ignored for Phase 1 2D battlefield conversion.
- Origin convention: battlefield `(0, 0)` is the lower-left board corner in inches; TTS origin is
  the world-space point that corresponds to that battlefield origin.
- Board rotation: clockwise degrees around TTS `y`, default `0.0`. Phase 1 fixture uses no rotation.
- Scale: fixture uses `1.0` TTS world unit per battlefield inch, with board bounds `44 x 60`.
- Round-trip tolerance: Phase 1 accepts calibration points with maximum error `<= 0.25` inches.
- Snapshot host marker: snapshots carry `host_context.local_companion_required=true` and a
  host-only note. If a live TTS field is unavailable, encode its provenance as `unsupported`.
- LOS wording: all `Physics.cast` data is labeled diagnostic and non-authoritative. It is not a
  gameplay LOS ruling.
- Live feasibility gate: if a real TTS `WebRequest.custom` round trip cannot be observed, this loop
  must close as a Phase 1 contracts-only baseline. The commit message, work log, and next loop
  trigger must say live TTS feasibility remains incomplete and the next loop must be "prove live TTS
  round trip", not Phase 1.5 housekeeping.
- Response privacy: accepted snapshot responses must not echo submitted snapshot bodies. They return
  only `ok`, response schema/version, deterministic input hash, object counts, diagnostic warning
  labels, and sanitized readiness metadata.
- Error privacy: all bridge/API failures use the typed `TtsBridgeResponse(ok=false,
  error={code,message,field_path})` shape. Error responses must not include raw Pydantic/FastAPI
  validation payloads, submitted input excerpts, save names, local paths, Steam identifiers,
  screenshots, raw rosters, credentials, or generated capture contents.

## File Map

- Create: `src/warhammer_companion/domain/tts.py`
  - Pydantic contracts for `TtsBoardSnapshot`, `TtsBoardTransform`, `TtsObjectRef`, diagnostic LOS
    probe records, host context, and bridge responses.
- Create: `src/warhammer_companion/application/tts_bridge.py`
  - Bridge health response, snapshot validation/normalization, deterministic input hash, and
    structured success/error envelopes.
- Modify: `src/warhammer_companion/application/services.py`
  - Add pass-through TTS bridge methods while keeping `services.py` thin.
- Modify: `src/warhammer_companion/web/server.py`
  - Add `GET /api/tts/health` and `POST /api/tts/snapshot` JSON routes only.
- Create: `tests/fixtures/tts/minimal_snapshot.json`
  - Synthetic sanitized fixture with three tagged objects: attacker, target, terrain.
- Create: `tests/test_tts_domain.py`
  - Contract validation, fixture loading, transform round-trip, invalid object kind checks.
- Create: `tests/test_tts_bridge.py`
  - Health, snapshot response, deterministic hash, diagnostic LOS label, structured errors.
- Modify: `tests/test_web_server.py`
  - Thin API route checks for health, snapshot, malformed payload behavior, and no HTML/JS coupling.
- Create: `docs/tts/global_lua_echo.lua`
  - Minimal Global Lua paste-in harness using `WebRequest.custom`, explicit JSON headers, response
    code handling, timeout/error comments, object tags, diagnostic cast, beam/marker placeholders.
- Create: `docs/superpowers/qa/2026-06-23-tts-phase-1-feasibility-harness-qa.md`
  - Manual QA checklist for local TTS, browser/computer use, and sanitized evidence capture.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-1-consultant-plan.md`
  - Consultant plan review record.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-1-adversarial-plan.md`
  - Adversarial plan review and triage record.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-1-consultant-closeout.md`
  - Consultant closeout review record.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-1-adversarial-closeout.md`
  - Adversarial closeout review and triage record.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Record decisions, verification, TTS manual QA status, CodeRabbit status, and next loop trigger.

## Task 1: Preflight And Plan Review

- [ ] **Step 1: Confirm starting state**

Run:

```powershell
git status -sb
git show --stat --oneline --name-only HEAD
```

Expected: branch is `codex/assistant-companion-roadmap`, Phase 0.5 commit is current, and only
user-owned untracked `AGENTS.md` plus this Phase 1 plan file are visible before implementation.

- [ ] **Step 2: Run consultant plan review**

Ask a consultant subagent to review this plan for spec coverage, local TTS feasibility gating,
transform assumptions, and endpoint clarity.

Expected: PASS or concrete P0/P1 findings.

- [ ] **Step 3: Run adversarial plan review**

Ask an adversarial subagent to look for overclaiming, raw artifact leakage, schema ambiguity,
unsafe route behavior, or missed manual QA evidence.

Expected: PASS or concrete P0/P1 findings.

- [ ] **Step 4: Triage and re-review**

Patch accepted P0/P1 findings, record reasoning in the review files, and resubmit until both plan
reviews pass.

## Task 2: Domain Contract Tests And Models

- [ ] **Step 1: Write failing domain tests**

Create `tests/test_tts_domain.py` with tests for:

- loading `tests/fixtures/tts/minimal_snapshot.json`;
- requiring `schema_version == "tts-board-snapshot/v0"`;
- exactly one attacker, one target, and one terrain object;
- invalid object kinds fail validation;
- transform fixture round-trips calibration points within `0.25` inches;
- diagnostic LOS probe cannot be marked authoritative.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_tts_domain.py -q
```

Expected: FAIL because `warhammer_companion.domain.tts` does not exist.

- [ ] **Step 2: Implement domain contracts**

Create `src/warhammer_companion/domain/tts.py` with Pydantic models and helper methods:

- `TtsVector3`;
- `BattlefieldPoint`;
- `TtsBoardCalibrationPoint`;
- `TtsBoardTransform.world_to_battlefield()` and `.round_trip_error_inches()`;
- `TtsObjectRef`;
- `TtsHostContext`;
- `TtsDiagnosticLosProbe`;
- `TtsBoardSnapshot`;
- `TtsBridgeError`;
- `TtsBridgeResponse`.

Keep all schema versions explicit and use constrained literals for object kind, provenance, and
diagnostic status.

- [ ] **Step 3: Add sanitized fixture**

Create `tests/fixtures/tts/minimal_snapshot.json` as a synthetic minimal fixture. It must not
contain save names, Steam IDs, local paths, screenshots, raw rosters, or official source text.

- [ ] **Step 4: Run domain tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_tts_domain.py -q
```

Expected: PASS.
Accepted responses must not echo submitted snapshot bodies. Invalid responses must use
`TtsBridgeResponse(ok=false, error=...)` and omit raw input excerpts or protected local artifact
hints.

## Task 3: Application Bridge And API Routes

- [ ] **Step 1: Write failing bridge and web tests**

Create `tests/test_tts_bridge.py` and extend `tests/test_web_server.py`.

Required checks:

- bridge health response reports `host_only=true` and `live_tts_round_trip_observed=false`;
- snapshot response returns `ok=true`, deterministic input hash, object counts, and diagnostic LOS
  warning labels without echoing the submitted snapshot body;
- malformed snapshot returns `TtsBridgeResponse(ok=false, error={code,message,field_path})`, not
  traceback text or raw validation payloads;
- `GET /api/tts/health` returns JSON, not HTML;
- `POST /api/tts/snapshot` accepts the fixture JSON;
- malformed API payload returns the same sanitized `TtsBridgeResponse(ok=false, error=...)`
  envelope;
- protected-looking malformed values such as `SteamID`, `Saved Objects`, `.tts`, `.png`,
  `auth.json`, and `sk-` are absent from response bodies.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_tts_bridge.py tests\test_web_server.py -q
```

Expected: FAIL because the bridge module and routes do not exist.

- [ ] **Step 2: Implement bridge service**

Create `src/warhammer_companion/application/tts_bridge.py`:

- `TtsBridgeService.health()` returns a `TtsBridgeResponse` with host-only readiness metadata.
- `TtsBridgeService.accept_snapshot(snapshot)` validates a `TtsBoardSnapshot`, computes a stable
  SHA-256 input hash from JSON mode data, and returns a structured accepted response without
  echoing the submitted snapshot body.
- Errors use `TtsBridgeError` with safe `code`, `message`, and `field_path` values.

- [ ] **Step 3: Add service pass-throughs**

Modify `WarhammerCompanionService` to own a `TtsBridgeService` instance and expose:

- `tts_health()`;
- `accept_tts_snapshot(snapshot: TtsBoardSnapshot)`.

- [ ] **Step 4: Add thin FastAPI routes**

Modify `src/warhammer_companion/web/server.py`:

- `GET /api/tts/health`;
- `POST /api/tts/snapshot`.

Routes must return model-dumped JSON-compatible dictionaries and must not render templates or add
frontend JavaScript. The snapshot route must accept raw `dict[str, object]` request bodies and call
the bridge validator itself so invalid snapshots can be converted into the sanitized
`TtsBridgeResponse` envelope rather than FastAPI's default request-body validation detail.

- [ ] **Step 5: Run bridge and web tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_tts_bridge.py tests\test_web_server.py -q
```

Expected: PASS.

## Task 4: Lua Harness Asset And Manual QA Path

- [ ] **Step 1: Add Lua harness template**

Create `docs/tts/global_lua_echo.lua` with:

- `WebRequest.custom`;
- `Content-Type: application/json`;
- explicit response-code handling;
- structured error handling;
- selected/tagged object discovery for `tts-attacker`, `tts-target`, and `tts-terrain`;
- diagnostic `Physics.cast` section labeled non-authoritative;
- minimal visible beam/hit marker behavior, or clearly documented unobserved visual helpers if TTS
  cannot be run locally;
- no `WebRequest.post`.

- [ ] **Step 2: Add manual QA checklist**

Create `docs/superpowers/qa/2026-06-23-tts-phase-1-feasibility-harness-qa.md` with:

- start companion locally with `.\.venv\Scripts\python.exe -m warhammer_companion.app`;
- browser check `http://127.0.0.1:8000/api/tts/health`;
- TTS computer-use checklist: launch local TTS, load controlled save, paste Global Lua, confirm
  bridge health, send snapshot, and observe diagnostic LOS payload. If minimal beam/marker helpers
  can be exercised, record only booleans for beam/marker observation; if not, record the visual
  helpers as unobserved and keep live feasibility incomplete;
- protected artifact check: no raw saves, screenshots, logs, Steam state, Codex/OpenAI state, or
  generated captures are staged;
- fallback branch: if TTS cannot run, record `live_tts_round_trip_observed=false` and do not claim
  Phase 1 live feasibility.

- [ ] **Step 3: Verify Lua contract**

Run:

```powershell
rg -n "WebRequest\\.custom|WebRequest\\.post|Content-Type|diagnostic|Physics.cast" docs/tts/global_lua_echo.lua
```

Expected: `WebRequest.custom`, `Content-Type`, `diagnostic`, and `Physics.cast` appear;
`WebRequest.post` appears only in a negative guard comment or not at all.

## Task 5: Verification, Reviews, And Commit

- [ ] **Step 1: Run targeted tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_tts_domain.py tests\test_tts_bridge.py tests\test_web_server.py -q
```

Expected: PASS.

- [ ] **Step 2: Run standard checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
```

Expected: PASS.

- [ ] **Step 3: Run docs and fixture safety scans**

Run:

```powershell
$files=@(
  'src/warhammer_companion/domain/tts.py',
  'src/warhammer_companion/application/tts_bridge.py',
  'tests/test_tts_domain.py',
  'tests/test_tts_bridge.py',
  'tests/fixtures/tts/minimal_snapshot.json',
  'docs/tts/global_lua_echo.lua',
  'docs/superpowers/qa/2026-06-23-tts-phase-1-feasibility-harness-qa.md',
  'docs/work-log/player-toolkit-implementation.md'
)
$results = foreach ($file in $files) {
  $text=Get-Content -Raw -Path $file
  [pscustomobject]@{
    File=$file
    NonAscii=([regex]::Matches($text,'[^\x00-\x7F]')).Count
    Placeholders=([regex]::Matches($text,'TO[D]O|TB[D]|FIX[M]E')).Count
    ProtectedHints=([regex]::Matches($text,'SteamID|Saved Objects|\.tts|\.png|auth\.json|sk-')).Count
  }
}
$results | ConvertTo-Json
```

Expected: `NonAscii=0`, `Placeholders=0`, and no protected local artifact hints except allowlisted
documentation text in the QA file and synthetic negative-test literals that assert protected-looking
input is absent from API responses.

- [ ] **Step 4: Run manual QA**

Use browser use for `/api/tts/health` and `/api/tts/snapshot` if the local server can be launched.
Use computer use for TTS only if launching the GUI is feasible and non-destructive. Record exact
booleans and blockers in the QA file and work log.
If a real TTS `WebRequest.custom` round trip is not observed, close the loop as contracts-only:
`live_tts_round_trip_observed=false`, no live feasibility claim, contracts-only commit message, and
next loop trigger set to "prove live TTS round trip".

- [ ] **Step 5: Attempt CodeRabbit**

Run:

```powershell
coderabbit --version
coderabbit auth status --agent
coderabbit review --agent -t uncommitted
```

Expected: CodeRabbit review completes or exact install/auth/system blocker is logged. Do not present
manual review as CodeRabbit output.

- [ ] **Step 6: Run consultant closeout review**

Ask a consultant subagent to verify Phase 1 meets the spec without overclaiming live feasibility.

Expected: PASS or concrete P0/P1 findings.

- [ ] **Step 7: Run adversarial closeout review**

Ask an adversarial subagent to inspect the diff for raw artifact leaks, route/schema risks,
diagnostic wording failures, and unsafe staging.

Expected: PASS or concrete P0/P1 findings.

- [ ] **Step 8: Triage and re-review**

Patch accepted P0/P1 findings and resubmit until both closeout reviews pass.

- [ ] **Step 9: Stage exact files**

Run:

```powershell
git add -- src/warhammer_companion/domain/tts.py src/warhammer_companion/application/tts_bridge.py src/warhammer_companion/application/services.py src/warhammer_companion/web/server.py tests/fixtures/tts/minimal_snapshot.json tests/test_tts_domain.py tests/test_tts_bridge.py tests/test_web_server.py docs/tts/global_lua_echo.lua docs/superpowers/plans/2026-06-23-tts-phase-1-feasibility-harness.md docs/superpowers/qa/2026-06-23-tts-phase-1-feasibility-harness-qa.md docs/superpowers/reviews/2026-06-23-tts-phase-1-consultant-plan.md docs/superpowers/reviews/2026-06-23-tts-phase-1-adversarial-plan.md docs/superpowers/reviews/2026-06-23-tts-phase-1-consultant-closeout.md docs/superpowers/reviews/2026-06-23-tts-phase-1-adversarial-closeout.md docs/work-log/player-toolkit-implementation.md
git diff --cached --name-only
```

Expected: exactly those files. `AGENTS.md` is not staged.

- [ ] **Step 10: Commit Phase 1**

Run:

```powershell
git commit -m "Add TTS phase 1 bridge harness"
```

Expected: one atomic Phase 1 implementation commit.
If `live_tts_round_trip_observed=false`, use:

```powershell
git commit -m "Add TTS phase 1 bridge contracts"
```

Expected: one atomic Phase 1 contracts-only commit.

## Next Loop Trigger

Start Phase 1.5 TTS bridge housekeeping.

If `live_tts_round_trip_observed=false`, replace this with:

Prove Phase 1 live TTS round trip.
