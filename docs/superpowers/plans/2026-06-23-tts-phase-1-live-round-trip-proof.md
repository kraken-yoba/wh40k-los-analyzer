# TTS Phase 1 Live Round Trip Proof Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove or explicitly block the real Tabletop Simulator Global Lua `WebRequest.custom`
round trip to the local companion without committing raw local TTS artifacts.

**Architecture:** Reuse the committed Phase 1 contracts and `docs/tts/global_lua_echo.lua`. The
Python companion remains the server of record. This loop may use a local-only server stdout line or
in-memory receipt counter as proof evidence, but committed evidence is limited to sanitized booleans,
schema labels, endpoint path, and a short receipt id. TTS may claim it sent a request, but companion
readiness remains contracts-only until a later server-side observation gate is implemented.

**Tech Stack:** Local FastAPI companion, Tabletop Simulator Global Lua, `WebRequest.custom`, scoped
PowerShell HTTP checks, operator-assisted TTS steps, and factual QA logging.

---

## Scope

Allowed:

- Launch the local companion and TTS.
- Prefer an operator-assisted proof path using repo-reviewed Lua from `docs/tts/global_lua_echo.lua`.
- Prefer a programmatic TTS External Editor proof through
  `warhammer-companion tts-execute-lua` when localhost port 39999 is available.
- Use sanitized companion access-log receipt ids to distinguish TTS-originated traffic from shell
  probes.
- Use the External Editor API only through reviewed package code and reviewed Lua templates, not
  ad hoc command-line payloads.
- If TTS is visible to the operator but not visible to process/window/API tooling, record that as a
  tooling blocker and switch to an operator-assisted proof path.
- If a human/operator micro-step is needed, document the exact safe step rather than guessing.
- Update QA/work-log/review docs with sanitized booleans and blocker labels.

Forbidden:

- No raw TTS saves, screenshots, generated captures, Steam state, logs, rosters, local paths,
  Codex/OpenAI state, or credentials in committed artifacts.
- No blind keyboard/mouse input into TTS after Computer Use capture fails.
- No Computer Use for this TTS proof until the Windows Security false-positive path is understood
  and the command-line payload shape has been reduced.
- No temporary `bootexec.cfg`, long generated command-line Lua payloads, or unreviewed
  paste-and-run automation artifacts for this proof path.
- No claim of live TTS feasibility unless the companion receives a real request from TTS.
- No change to server readiness semantics; Phase 1 remains contracts-only until a separate
  server-side observation gate exists.
- No save, Save & Play, Workshop upload, export, or local save-file mutation during the proof.

## Proof Criteria

Minimum proof for this loop:

- Companion server is reachable on `127.0.0.1`.
- Phase 1 contracts commit `887335c` is HEAD or an ancestor of HEAD before proof starts.
- TTS is open on a controlled table according to the operator, or TTS exposes the External Editor
  API on localhost port 39999.
- The operator runs the reviewed Global Lua harness from `docs/tts/global_lua_echo.lua`, or the
  reviewed CLI helper runs `docs/tts/external_editor_health_receipt.lua` through the TTS External
  Editor API.
- Global Lua harness can run `ttsHealth()` or `ttsSendSnapshot()` from TTS.
- The companion receives a real request from TTS using `WebRequest.custom`.
- Proof evidence distinguishes the TTS-originated request from PowerShell probes through a
  local-only server receipt: endpoint path, timestamp/sequence, request id if available, and the
  response schema label. Raw server logs are not committed.
- The evidence recorded in repo docs is sanitized: only status booleans, response schema,
  readiness label, and blocker labels.

If the TTS UI path cannot be operated safely, close this loop as blocked or docs-only with
`live_tts_round_trip_observed=false` and keep the next loop trigger focused on an operator-assisted
or reviewed-helper proof path.

## File Map

- Create: `docs/superpowers/plans/2026-06-23-tts-phase-1-live-round-trip-proof.md`
  - This plan.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-1-live-proof-consultant-plan.md`
  - Consultant plan review record.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-1-live-proof-adversarial-plan.md`
  - Adversarial plan review record.
- Modify: `docs/superpowers/qa/2026-06-23-tts-phase-1-feasibility-harness-qa.md`
  - Append sanitized live-proof attempt evidence.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Append live-proof attempt result and next loop trigger.
- Add: `src/warhammer_companion/application/tts_external_editor.py`
  - Reviewed localhost External Editor API helper.
- Add: `docs/tts/external_editor_health_receipt.lua`
  - Reviewed transient Lua proof template.
- Add: `tests/test_tts_external_editor.py`
  - Helper and CLI contract tests.

## Task 1: Preflight

- [ ] **Step 1: Confirm repository state**

Run:

```powershell
git status -sb
git show --stat --oneline --name-only HEAD
git merge-base --is-ancestor 887335c HEAD
```

Expected: Phase 1 contracts commit `887335c` is HEAD or an ancestor; `AGENTS.md` may remain
user-owned and untracked.

- [ ] **Step 2: Confirm no server/TTS leftovers**

Run:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
Get-Process | Where-Object { $_.ProcessName -like '*Tabletop*' -or $_.MainWindowTitle -like '*Tabletop Simulator*' }
```

Expected: no companion listener and no TTS process from the previous attempt.
If a companion listener or TTS process already exists, stop and ask before reusing or closing it.

## Task 2: Plan Review

- [ ] **Step 1: Consultant plan review**

Ask a consultant subagent whether this proof path is sufficient and safe.

Expected: PASS or concrete P0/P1 findings.

- [ ] **Step 2: Adversarial plan review**

Ask an adversarial subagent to look for artifact leaks, blind UI automation, overclaiming, or
server-readiness drift.

Expected: PASS or concrete P0/P1 findings.

- [ ] **Step 3: Triage and re-review**

Patch accepted P0/P1 findings and resubmit until both reviews pass.

## Task 3: Attempt Live Proof

- [ ] **Step 1: Start companion server**

Start `.\.venv\Scripts\python.exe -m warhammer_companion.app` in a controlled background process.

Verify:

```powershell
Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/tts/health' -UseBasicParsing -TimeoutSec 2
```

Expected: status 200 and `readiness=contracts-only`.

- [ ] **Step 2: Operator opens controlled TTS table**

Ask the operator to open a controlled local TTS table/save and keep it unsaved. The agent must not
use Computer Use, temporary boot scripts, or generated command-line Lua payloads.

Expected: TTS is open on a controlled table according to the operator.

- [ ] **Step 3: Try reviewed External Editor helper**

If TTS exposes localhost port 39999, run:

```powershell
.\.venv\Scripts\warhammer-companion.exe tts-execute-lua `
  --script-file docs\tts\external_editor_health_receipt.lua `
  --receipt <short-receipt>
```

Expected: the companion receives a `GET /api/tts/health?receipt=<short-receipt>` request from TTS.
This proves programmatic TTS-to-companion transport through reviewed code and reviewed Lua without
saving a TTS script.

- [ ] **Step 4: Operator runs repo-reviewed Lua if helper path is unavailable**

Ask the operator to load or paste only the reviewed Lua in `docs/tts/global_lua_echo.lua` into
Global for the controlled table and run `ttsHealth()` first. If the controlled table has the
required tags (`tts-attacker`, `tts-target`, `tts-terrain`), run `ttsSendSnapshot()` second.

Do not press Save, Save & Play, Workshop upload, export, or any mutation control.

Expected: the companion receives a request from TTS and returns the typed bridge response.
Acceptable proof must include a sanitized server-side receipt that distinguishes the TTS-originated
request from the PowerShell health probe.

- [ ] **Step 5: Cleanup**

Always stop the companion server launched by this loop. The operator closes TTS or leaves it open by
explicit choice; the agent must not force-close an operator-owned TTS session.

Expected: no port 8000 listener from this loop remains.

## Task 4: Verification And Closeout

- [ ] **Step 1: Update docs**

Record sanitized proof evidence or blocker evidence in the QA file and work log.

- [ ] **Step 2: Run docs scans**

Run:

```powershell
$files=@(
  'docs/superpowers/plans/2026-06-23-tts-phase-1-live-round-trip-proof.md',
  'docs/superpowers/reviews/2026-06-23-tts-phase-1-live-proof-consultant-plan.md',
  'docs/superpowers/reviews/2026-06-23-tts-phase-1-live-proof-adversarial-plan.md',
  'docs/superpowers/qa/2026-06-23-tts-phase-1-feasibility-harness-qa.md',
  'docs/work-log/player-toolkit-implementation.md'
)
$results = foreach ($file in $files) {
  $text=Get-Content -Raw -Path $file
  [pscustomobject]@{
    File=$file
    NonAscii=([regex]::Matches($text,'[^\x00-\x7F]')).Count
    Placeholders=([regex]::Matches($text,'TO[D]O|TB[D]|FIX[M]E')).Count
  }
}
$results | ConvertTo-Json
```

Expected: `NonAscii=0`, `Placeholders=0`.

- [ ] **Step 3: Check staged scope**

Run:

```powershell
git diff --name-only --cached
git diff --cached --check
```

Expected: only allowed sanitized docs are staged, `AGENTS.md` is not staged, and cached diff check
has no errors.

- [ ] **Step 4: Re-run minimal regression checks if docs only changed**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_tts_bridge.py tests\test_web_server.py -q
```

Expected: PASS.

- [ ] **Step 5: Closeout review**

Ask consultant and adversarial reviewers to verify the proof result or blocker result.

Expected: PASS or concrete P0/P1 findings.

- [ ] **Step 6: Commit docs if repository artifacts changed**

Stage only this plan, review records, QA file, and work log. Do not stage `AGENTS.md`.

Commit message if blocked:

```powershell
git commit -m "Log TTS phase 1 live proof blocker"
```

Commit message if live round trip is proven:

```powershell
git commit -m "Record TTS phase 1 live round trip"
```

## Next Loop Trigger

If blocked: perform an operator-assisted TTS Lua round-trip proof, or build a small reviewed helper
that avoids Computer Use, temporary boot scripts, and generated command-line Lua payloads.

If proven: start Phase 1.5 TTS bridge housekeeping.
Success wording must remain narrow: `live_tts_round_trip_observed=true`,
`readiness=contracts-only`, `source=TTS Global Lua WebRequest.custom`. Do not claim LOS
correctness, production readiness, save automation reliability, or broader TTS feasibility.
