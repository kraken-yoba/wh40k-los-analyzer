# TTS Phase 1 Mac Mini Continuation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue the Phase 1 live Tabletop Simulator proof on a Mac mini and determine whether
the Windows blocker is local platform friction or a TTS scripting/editor initialization issue.

**Architecture:** Keep the durable companion engine in Python and keep Lua at the TTS table edge.
The only Phase 1 completion proof is a Global Lua-originated `WebRequest.custom` request reaching
the local Python companion with the exact receipt and proof header. Runner-owned health receipts
are useful transport diagnostics, but they do not complete the Global-script objective by
themselves. A sent External Editor message, a responsive companion health endpoint, or an
operator-visible loaded table is not proof without the companion-side receipt.

**Tech Stack:** macOS, Steam Tabletop Simulator, Hutber/ForceOrg development table, Python 3.12,
`warhammer-companion` CLI, TTS External Editor API on `127.0.0.1:39999`, TTS System Console `lua`
command, reviewed Lua templates under `docs/tts/`, and sanitized QA/work-log evidence.

---

## Current State To Preserve

- Branch: `codex/assistant-companion-roadmap`.
- Windows handoff baseline: commit `4de96b6 Log TTS console proof timeout`.
- Active goal remains incomplete: no real TTS-originated receipt has been observed.
- TTS table absence is ruled out for the latest Windows attempt. The operator manually loaded a
  table/server with models and Hutber available.
- Windows TTS process was responsive, but no localhost listener on ports `39999` or `39998` was
  observed after the table was loaded.
- Loaded-table External Editor proof result:
  - Command: `.\.venv\Scripts\warhammer-companion.exe tts-proof-health --wait-seconds 30`
  - Receipt: `tts-proof-54f5eeeb206d`
  - Blocker: `tts-external-editor-unavailable`
  - `external_editor_message_sent=false`
  - `companion_receipt_observed=false`
  - `live_tts_round_trip_observed=false`
- Loaded-table manual System Console proof result:
  - Receipt: `active-table-console-2`
  - Runner-owned listener: `127.0.0.1:54750`
  - Blocker: `companion-receipt-not-observed`
  - `companion_receipt_observed=false`
  - `live_tts_round_trip_observed=false`
  - Operator reported no visible TTS output after the command was supplied.
- Player log keyword scans did not show `WebRequest`, receipt, port, Lua error, or companion proof
  clues.
- Raw local proof logs remain ignored/generated and must not be committed.

## Source Facts

- Official TTS External Editor API documentation says TTS listens for incoming localhost TCP
  connections on port `39999`, while the editor side listens on `39998`:
  <https://api.tabletopsimulator.com/externaleditorapi/>
- The same documentation says Execute Lua Code is message ID `3` with a target `guid` and `script`.
  The Global script target is `guid="-1"`.
- Official TTS System Console documentation says backtick opens the console and the `lua` command
  executes Lua code as if run by the current mod:
  <https://api.tabletopsimulator.com/systemconsole/>
- Do not use `bootexec.cfg`, `autoexec.cfg`, OS/Steam launch command-line Lua payloads, or blind UI
  automation for this proof. That path previously created Windows Security false-positive risk and
  is not needed for the Mac parity spike. The approved manual diagnostic is only the one-line
  System Console `lua ...` command printed by `tts-manual-health`.

## Mac-Specific Caveat

The existing `tts-proof-health` command has a Windows-only process-owner verifier in
`src/warhammer_companion/application/tts_live_proof.py`. On macOS it is expected to fail closed with
`tts-external-editor-process-check-unsupported` until a Darwin process verifier is implemented.

That means the Mac continuation has two safe options:

- Preferred: add a small tested Darwin verifier that checks port `39999` with `lsof` and confirms
  the listener process name contains `Tabletop` before `tts-proof-health` sends Lua.
- Temporary diagnostic only: independently verify port `39999` is owned by Tabletop Simulator with
  `lsof`, then use `tts-execute-lua` and require a companion-side receipt before recording success.

Do not treat `tts-execute-lua` output as proof by itself. It only proves the socket write was
attempted.

## Task 1: Mac Checkout And Local Verification

- [ ] **Step 1: Fetch the pushed branch**

```bash
git fetch origin
git switch codex/assistant-companion-roadmap
git pull --ff-only
```

Expected: branch contains this continuation plan and the latest Windows QA/work-log evidence.

- [ ] **Step 2: Create the Python environment**

```bash
python3.12 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e ".[dev]"
```

Expected: editable install succeeds and `./.venv/bin/warhammer-companion --help` lists
`tts-proof-health`, `tts-execute-lua`, and `tts-manual-health`.

- [ ] **Step 3: Run focused proof helper tests**

```bash
./.venv/bin/python -m pytest tests/test_tts_external_editor.py tests/test_tts_manual_proof.py -q
```

Expected: PASS. These tests use fake/local proof servers; they do not prove live TTS.

## Task 2: Load TTS And Inspect External Editor Availability

- [ ] **Step 1: Load the development TTS table**

Open Steam Tabletop Simulator on the Mac mini. Load the prepared table with Hutber/ForceOrg and the
same development armies/terrain if available. Keep the table unsaved.

Expected: the operator can see a loaded table with models and terrain.

- [ ] **Step 2: Check the official External Editor ports**

```bash
lsof -nP -iTCP:39999 -sTCP:LISTEN
lsof -nP -iTCP:39998 -sTCP:LISTEN
```

Expected for the programmatic proof path: port `39999` is listening and the owning process is
Tabletop Simulator. Port `39998` may be absent unless an editor-side listener is running.

- [ ] **Step 3: If port 39999 is absent, initialize scripting without mutating the save**

Open the in-game scripting editor or object scripting editor through normal TTS UI controls. Do not
press Save, Save & Play, Workshop upload, export, or any save mutation control. Re-run:

```bash
lsof -nP -iTCP:39999 -sTCP:LISTEN
```

Expected: either port `39999` appears under Tabletop Simulator, or the blocker remains
`tts-external-editor-unavailable-on-loaded-table`.

## Task 3: Preferred Programmatic Proof

- [ ] **Step 1: If needed, implement the Darwin verifier before using `tts-proof-health`**

If `./.venv/bin/warhammer-companion tts-proof-health --wait-seconds 1` reports
`tts-external-editor-process-check-unsupported`, add a Darwin branch in
`verify_tts_external_editor_process()` that shells out to `lsof -nP -iTCP:<port> -sTCP:LISTEN -F pc`
and accepts only a listener whose command/process name contains `tabletop`.

Add focused tests in `tests/test_tts_external_editor.py` by monkeypatching `platform.system()` to
`Darwin` and `subprocess.run()` to return:

```text
p12345
cTabletop Simulator
```

Expected: the verifier returns `verified=True` for the Tabletop listener and fails closed for no
listener, malformed output, timeout, and non-Tabletop process names.

- [ ] **Step 2: Run the reviewed External Editor health proof**

```bash
./.venv/bin/warhammer-companion tts-proof-health --wait-seconds 30
```

Expected success JSON:

```json
{
  "schema_version": "tts-health-proof/v0",
  "proof_server_owned_listener": true,
  "tts_external_editor_process_verified": true,
  "external_editor_message_sent": true,
  "companion_receipt_observed": true,
  "live_tts_round_trip_observed": true,
  "readiness": "contracts-only",
  "source": "TTS External Editor WebRequest.custom",
  "receipt_endpoint_path": "/api/tts/health",
  "receipt_status_code": 200,
  "blocker": null
}
```

If this fails, record the sanitized JSON exactly and keep
`live_tts_round_trip_observed=false`.

## Task 4: Manual System Console Diagnostic

- [ ] **Step 1: Start the manual proof runner**

```bash
./.venv/bin/warhammer-companion tts-manual-health --wait-seconds 300
```

Expected: the command prints a one-line `lua WebRequest.custom(...)` command with a fresh receipt
and waits for the exact receipt.

- [ ] **Step 2: Execute the one-line command inside TTS**

Open the TTS System Console with backtick, paste only the first printed `lua ...` command, and press
Enter. Capture the exact visible TTS console output in notes for the QA/work-log update.

Expected diagnostic success: the runner prints sanitized JSON with
`source="TTS manual Lua WebRequest.custom"` and `live_tts_round_trip_observed=true`. This proves
the narrow manual health transport only. It does not prove Global-script readiness or complete the
Phase 1 objective.

Expected failure evidence: the runner prints `companion-receipt-not-observed`, or TTS prints an
exact Lua/System Console error that explains why the command did not execute.

## Task 5: Global Snapshot Proof Trigger

Run this task only after Task 3 or Task 4 proves the health transport.

- [ ] **Step 1: Confirm required table tags**

Confirm the controlled table has the development tags expected by `docs/tts/global_lua_echo.lua`:
`tts-attacker`, `tts-target`, and `tts-terrain`.

Expected: tags exist on the intended objects, or the blocker is recorded as
`tts-development-tags-missing`.

- [ ] **Step 2: Run the reviewed Global echo harness**

Use `docs/tts/global_lua_echo.lua` through the proven transport path.

Expected: the companion receives a TTS-originated snapshot/echo request from Global Lua. Record this
as `global_script_webrequest_observed=true` only after the companion-side receipt exists.

## Task 6: Evidence, Review, Commit, Push

- [ ] **Step 1: Update repository evidence**

Update:

- `docs/superpowers/qa/2026-06-23-tts-phase-1-feasibility-harness-qa.md`
- `docs/work-log/player-toolkit-implementation.md`

Record only sanitized booleans, schema labels, receipt ids, endpoint path/status, platform, and
blocker labels. Do not commit TTS saves, screenshots, raw logs, Steam state, rosters, Codex/OpenAI
state, or local user paths.

- [ ] **Step 2: Run verification**

```bash
./.venv/bin/python -m ruff format --check src tests
./.venv/bin/python -m ruff check .
./.venv/bin/mypy src
./.venv/bin/python -m pytest tests/test_tts_external_editor.py tests/test_tts_manual_proof.py -q
git diff --check
```

Expected: all commands pass. If only docs changed, a narrower docs scan plus the focused proof tests
is acceptable, but do not claim code readiness from docs-only checks.

- [ ] **Step 3: Review before closeout**

Run a spec-compliance review and an adversarial review of the evidence wording. The reviewers must
check that no wording claims Global-script readiness unless the Global receipt is actually observed.

Expected: PASS or concrete P0/P1 findings that are fixed and re-reviewed.

- [ ] **Step 4: Commit and push**

```bash
git status -sb
git add docs/superpowers/plans/2026-06-23-tts-phase-1-mac-mini-continuation.md docs/superpowers/qa/2026-06-23-tts-phase-1-feasibility-harness-qa.md docs/work-log/player-toolkit-implementation.md
git commit -m "Record macOS TTS phase 1 proof result"
git push
```

If a Darwin verifier is implemented, include the touched `src/` and `tests/` files in the same
atomic commit only if they are required to produce the Mac proof.

## Success And Failure Boundaries

Success:

- `live_tts_round_trip_observed=true` from a TTS-originated receipt is a required diagnostic signal
  but not enough by itself to complete Phase 1 if it came only from the manual health command.
- Phase 1 completion requires a proven Global Lua-originated `WebRequest.custom` receipt reaching
  the local companion, preferably through the reviewed External Editor path using `guid="-1"` or
  through `docs/tts/global_lua_echo.lua`.
- `readiness` remains `contracts-only`.

Failure:

- `tts-external-editor-unavailable`: TTS did not expose or accept the External Editor API.
- `tts-external-editor-process-check-unsupported`: the Mac verifier is missing and must be added or
  bypassed only with independent `lsof` proof.
- `companion-receipt-not-observed`: the proof server was listening, but no exact TTS request reached
  it during the wait window.
- A visible TTS console/Lua error should be copied into the QA/work-log summary in short sanitized
  form.

Do not mark the active Phase 1 goal complete until every requirement in the original objective is
proven by current evidence.
