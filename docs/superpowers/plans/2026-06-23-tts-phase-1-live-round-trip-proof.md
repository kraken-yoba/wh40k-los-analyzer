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
PowerShell HTTP checks, Computer Use when the TTS window can be safely captured, and factual QA
logging.

---

## Scope

Allowed:

- Launch the local companion and TTS.
- Use Computer Use to inspect TTS only if window capture works.
- If Computer Use capture is blocked, record the blocker and stop UI automation.
- If a human/operator micro-step is needed, document the exact safe step rather than guessing.
- Update QA/work-log/review docs with sanitized booleans and blocker labels.

Forbidden:

- No raw TTS saves, screenshots, generated captures, Steam state, logs, rosters, local paths,
  Codex/OpenAI state, or credentials in committed artifacts.
- No blind keyboard/mouse input into TTS after Computer Use capture fails.
- No claim of live TTS feasibility unless the companion receives a real request from TTS.
- No change to server readiness semantics; Phase 1 remains contracts-only until a separate
  server-side observation gate exists.
- No save, Save & Play, Workshop upload, export, or local save-file mutation during the proof.

## Proof Criteria

Minimum proof for this loop:

- Companion server is reachable on `127.0.0.1`.
- Phase 1 contracts commit `887335c` is HEAD or an ancestor of HEAD before proof starts.
- TTS launches and a usable TTS window is inspectable, or the capture blocker is recorded.
- Global Lua harness can run `ttsHealth()` or `ttsSendSnapshot()` from TTS.
- The companion receives a real request from TTS using `WebRequest.custom`.
- Proof evidence distinguishes the TTS-originated request from PowerShell probes through a
  local-only server receipt: endpoint path, timestamp/sequence, request id if available, and the
  response schema label. Raw server logs are not committed.
- The evidence recorded in repo docs is sanitized: only status booleans, response schema,
  readiness label, and blocker labels.

If the TTS UI path cannot be operated safely, close this loop as blocked or docs-only with
`live_tts_round_trip_observed=false` and keep the next loop trigger focused on the UI blocker.

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

- [ ] **Step 2: Launch TTS through Computer Use**

Use Computer Use app discovery and launch `Tabletop Simulator`.

Expected: TTS launches and exposes a targetable window.

- [ ] **Step 3: Capture TTS state**

Use `get_window_state` on the TTS window.

Expected: a usable menu/table state is inspectable. If capture fails, stop UI automation and record
the exact blocker.

- [ ] **Step 4: Run Lua proof if capture succeeds**

Only if TTS is inspectable and a throwaway/controlled development save is loaded, use the visible UI
to load or paste `docs/tts/global_lua_echo.lua` and run `ttsHealth()` or `ttsSendSnapshot()`.

Do not press Save, Save & Play, upload to Workshop, export, or otherwise persist the modified save.
Record only `controlled_save_used=true/false`.

Expected: companion receives a request from TTS and returns the typed bridge response.
Acceptable proof must include a sanitized server-side receipt that distinguishes the TTS-originated
request from the PowerShell health probe.

- [ ] **Step 5: Cleanup**

Always stop the companion server and close TTS if this loop launched them, including failure paths.
Track process ids/windows started by this loop and close only those.

Expected: no port 8000 listener and no leftover TTS process.

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

If blocked: resolve TTS Computer Use/window-capture path or perform an operator-assisted TTS Lua
round-trip proof.

If proven: start Phase 1.5 TTS bridge housekeeping.
Success wording must remain narrow: `live_tts_round_trip_observed=true`,
`readiness=contracts-only`, `source=TTS Global Lua WebRequest.custom`. Do not claim LOS
correctness, production readiness, save automation reliability, or broader TTS feasibility.
