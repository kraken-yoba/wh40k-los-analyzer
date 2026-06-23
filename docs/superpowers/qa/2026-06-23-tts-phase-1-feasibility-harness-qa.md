# TTS Phase 1 Feasibility Harness QA

Date: 2026-06-23

Scope:

- Verify the local companion TTS bridge endpoints and the controlled-save Lua harness path.
- Record only booleans, short blocker labels, and sanitized response summaries.
- Do not commit or paste raw TTS saves, screenshots, generated captures, Steam state, local paths,
  rosters, Codex/OpenAI auth state, or logs.

## Automated QA

Commands:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_tts_domain.py tests\test_tts_bridge.py tests\test_web_server.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
```

Expected:

- All commands pass.

## Browser QA

Setup:

```powershell
.\.venv\Scripts\python.exe -m warhammer_companion.app
```

Checks:

- Open `http://127.0.0.1:8000/api/tts/health`.
- Confirm the response is JSON.
- Confirm `ok=true`.
- Confirm `data.host_only=true`.
- Confirm `data.local_companion_required=true`.
- Confirm `data.live_tts_round_trip_observed=false` until a real TTS call is observed.
- POST `tests/fixtures/tts/minimal_snapshot.json` to `/api/tts/snapshot`.
- Confirm the accepted response has an input hash, object counts, and diagnostic warning labels.
- Confirm the accepted response does not echo submitted objects or diagnostic probe bodies.

Browser QA result:

- Status: blocked
- Shell endpoint fallback: passed
- Health status: 200
- Snapshot status: 200
- Health summary: `ok=true`, `host_only=true`, `local_companion_required=true`,
  `live_tts_round_trip_observed=false`, `readiness=contracts-only`
- Snapshot summary: `ok=true`, `snapshot_schema_version=tts-board-snapshot/v0`,
  `object_counts.attacker=1`, `object_counts.target=1`, `object_counts.terrain=1`,
  `diagnostic_warning_labels=[diagnostic-physics-cast]`
- Browser blocker: in-app Browser returned `ERR_BLOCKED_BY_CLIENT` for both
  `http://127.0.0.1:8000/api/tts/health` and `http://localhost:8000/api/tts/health`.

## TTS Computer-Use QA

Checks:

- Local TTS launches.
- Controlled development save loads.
- Hutber and ForceOrg workshop content is available in the controlled environment.
- `docs/tts/global_lua_echo.lua` is pasted into Global Lua.
- `ttsHealth()` reaches the local companion.
- `ttsSendSnapshot()` reaches the local companion through `WebRequest.custom`.
- The three required tags are present: `tts-attacker`, `tts-target`, and `tts-terrain`.
- Diagnostic `Physics.cast` output is observed.
- Beam/hit marker helper is observed, or recorded as unobserved.
- No raw save, screenshot, generated capture, local Steam state, Codex/OpenAI state, or log is staged.

TTS QA result:

- TTS launches: true
- Controlled save loads: not-observed
- Lua pasted: not-observed
- Health round trip observed: false
- Snapshot round trip observed: false
- Diagnostic cast observed: false
- Beam or marker observed: unobserved
- Protected artifact staged: false
- Blocker: Computer Use launched TTS and found a `Tabletop Simulator` window, but window capture
  failed with `SetIsBorderRequired failed: No such interface supported (0x80004002)`. Per the
  Computer Use safety guidance, app input stopped there.
- Cleanup: the Python companion server was stopped, and the TTS process received a graceful
  termination signal.

## Closeout Rule

If `ttsSendSnapshot()` is not observed reaching the companion from a real TTS host through
`WebRequest.custom`, close Phase 1 as a contracts-only baseline:

- `live_tts_round_trip_observed=false`;
- no live TTS feasibility claim;
- commit message: `Add TTS phase 1 bridge contracts`;
- next loop trigger: prove Phase 1 live TTS round trip.

## Live Proof Attempt - 2026-06-23

Plan:

- `docs/superpowers/plans/2026-06-23-tts-phase-1-live-round-trip-proof.md`

Result:

- Status: blocked
- Companion health before TTS launch: true
- Companion readiness before TTS launch: `contracts-only`
- TTS launch attempted through Computer Use: interrupted
- Interruption: Computer Use reported that it was stopped by a physical Escape key.
- TTS window inspected: false
- Controlled save used: false
- Lua pasted: false
- Health round trip from TTS observed: false
- Snapshot round trip from TTS observed: false
- Server-side TTS receipt observed: false
- Protected artifact staged: false
- Cleanup: companion server stopped; no port 8000 listener remained; no TTS process remained.

Closeout:

- `live_tts_round_trip_observed=false`
- No live TTS feasibility claim.
- Next loop should resume with an operator-approved or operator-assisted TTS UI path.

## Live Proof Continuation - 2026-06-23

Plan adjustment:

- Prefer the TTS External Editor API proof path when localhost port 39999 is available.
- Do not send External Editor `Save & Play`, do not update `scriptStates`, and do not persist a TTS
  save.
- Treat a TTS window that is visible to the operator but not visible to process/window/API tooling
  as a tooling blocker, not as evidence that TTS is unavailable.

Result:

- Status: blocked
- Companion health before TTS launch: true
- Companion readiness before TTS launch: `contracts-only`
- Direct executable launch returned a short-lived TTS process and then handed off to Steam.
- Steam launch request was accepted.
- TTS visible to operator: true
- TTS visible to process/API tooling during the proof window: false
- External Editor API port 39999 observed: false
- Health round trip from TTS observed: false
- Snapshot round trip from TTS observed: false
- Server-side TTS receipt observed: false
- User closed TTS after reporting the visibility mismatch.
- Cleanup: no companion listener remained on port 8000; no TTS process was visible to process
  tooling; Steam background processes remained.

Closeout:

- `live_tts_round_trip_observed=false`
- No live TTS feasibility claim.
- Next loop should use an operator-assisted proof step with TTS already on a controlled table, or
  use the reviewed External Editor helper when localhost port 39999 is available.

## Programmatic Proof Helper - 2026-06-23

Reason:

- Programmatic TTS integration remains required for manual end-to-end QA and later harness work.
- Windows Security flagged a Computer Use generated command-line event from this thread. The report
  indicated the event did not execute, was not active, and removal succeeded. No repo artifact,
  downloaded file, raw TTS save, roster, or companion source path was identified as the affected
  resource.

Policy update:

- Keep Computer Use and startup-script mechanisms available only after explicit review of their
  command-line/payload shape.
- Prefer small reviewed package code and reviewed Lua templates for TTS integration.
- Do not use temporary `bootexec.cfg`, long generated command-line Lua payloads, or unreviewed
  paste-and-run artifacts for the current proof path.

Artifacts:

- `src/warhammer_companion/application/tts_external_editor.py`
- `docs/tts/external_editor_health_receipt.lua`
- `tests/test_tts_external_editor.py`

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests\test_tts_external_editor.py -q`
- Initial red run failed with missing `warhammer_companion.application.tts_external_editor`.
- After the first implementation, targeted helper tests returned 5 passed.
- Consultant and adversarial reviewers required stricter local-origin, loopback-host, and
  reviewed-template enforcement.
- Post-fix targeted helper tests returned 14 passed.
- Focused regression tests returned 63 passed with the existing Starlette `TestClient`
  deprecation warning:
  `.\.venv\Scripts\python.exe -m pytest tests\test_tts_external_editor.py tests\test_cli.py tests\test_tts_bridge.py tests\test_web_server.py -q`
- Static gates passed:
  `.\.venv\Scripts\python.exe -m ruff format --check src tests`,
  `.\.venv\Scripts\python.exe -m ruff check src tests`, and
  `.\.venv\Scripts\mypy.exe src`.
- Full pytest passed:
  `.\.venv\Scripts\python.exe -m pytest` returned 515 passed with the existing Starlette
  `TestClient` deprecation warning.
- Consultant re-review passed.
- Adversarial re-review passed.
- CodeRabbit was attempted but unavailable on the PowerShell PATH.

Live proof status:

- External Editor helper implemented: true
- External Editor helper live-tested against TTS: false
- Health round trip from TTS observed: false
- Snapshot round trip from TTS observed: false
- Server-side TTS receipt observed: false
- `live_tts_round_trip_observed=false`
- Next loop should open a controlled TTS table and run the reviewed helper if port 39999 is
  available; otherwise use the operator-assisted reviewed Global Lua path.

## Reviewed Helper Live Attempt - 2026-06-23

Plan:

- Launch TTS without Computer Use or temporary startup scripts.
- Use only the reviewed External Editor helper if TTS exposes localhost port 39999.
- Verify a short server-side receipt before claiming live proof.

Result:

- Status: blocked
- Phase 1 contracts commit `887335c` ancestor check: true
- Temporary `bootexec.cfg` present before attempt: false
- TTS launched through the installed executable: true
- TTS process observed: true
- TTS External Editor API port 39999 observed: false
- Companion server proof process owned port 8000: false
- Companion health response usable as proof evidence: false
- Blocker: a non-proof listener answered the health check while the proof server failed to bind port
  8000. The raw temporary log was not committed and was removed after diagnosis.
- Reviewed helper executed against TTS: false
- Health round trip from TTS observed: false
- Snapshot round trip from TTS observed: false
- Server-side TTS receipt observed: false
- Cleanup: temporary logs removed; no listener remained on ports 8000 or 39999; TTS process launched
  by the loop was closed.

Closeout:

- `live_tts_round_trip_observed=false`
- No live TTS feasibility claim.
- Next loop must compare the port 8000 `OwningProcess` to the recorded proof-server PID before
  health/receipt checks, then use the reviewed helper after a controlled TTS table exposes port
  39999.

## Runner-Owned Health Proof Helper - 2026-06-23

Reason:

- Manual end-to-end QA and future TTS harness work require a programmatic interface, not only an
  operator-assisted proof path.
- The previous full-app proof attempt was ambiguous because a non-proof listener answered health
  while the proof server failed to bind port 8000.

Implementation:

- Added `warhammer_companion.application.tts_live_proof`.
- Added `warhammer-companion tts-proof-health`.
- The proof command verifies that the target External Editor listener is owned by a Tabletop
  Simulator process before it sends Lua.
- The proof command starts a temporary loopback-only health server on an ephemeral port.
- It renders only `docs/tts/external_editor_health_receipt.lua` with a safe receipt and the
  runner-owned local base URL.
- It sends the reviewed Lua through the TTS External Editor API and waits for the exact receipt.
- PowerShell process-verification timeout or startup failure returns a sanitized unverified-process
  blocker rather than a traceback.
- It prints sanitized JSON only: booleans, receipt id, readiness, source, endpoint path, status,
  process-verification status, local listener host/port, and blocker label.

Verification:

- Red test first failed with missing `warhammer_companion.application.tts_live_proof`.
- Focused proof-helper tests passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_tts_external_editor.py -q`
  returned 21 passed.
- Static gates passed:
  `.\.venv\Scripts\python.exe -m ruff format --check src tests`,
  `.\.venv\Scripts\python.exe -m ruff check .`, and `.\.venv\Scripts\mypy.exe src`.
- Focused TTS/web regression tests passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_tts_external_editor.py tests\test_tts_bridge.py tests\test_web_server.py -q`
  returned 67 passed with the existing Starlette `TestClient` deprecation warning.
- The fake-TTS test used a fake External Editor socket plus the runner-owned HTTP server. It did
  not require a real TTS instance because the process-verification preflight was injected.
- No-TTS CLI probe passed fail-closed:
  `.\.venv\Scripts\warhammer-companion.exe tts-proof-health --receipt no-tts-local-check --wait-seconds 0.01`
  exited nonzero with `blocker=tts-external-editor-unavailable`, no proof listener, no sent Lua,
  no observed receipt, and `live_tts_round_trip_observed=false`.
- Broad non-desktop regression passed:
  `.\.venv\Scripts\python.exe -m pytest --ignore=tests\test_desktop_app.py -q` returned
  500 passed with the existing Starlette `TestClient` deprecation warning.
- Full `.\.venv\Scripts\python.exe -m pytest` was attempted with a 300-second timeout and did not
  complete. Isolating `tests\test_desktop_app.py -q` also timed out after 180 seconds, so the
  remaining full-suite blocker is the desktop test file rather than the new TTS proof runner.
- Adversarial reviewer approved the false-positive guard after the Tabletop-owned External Editor
  process preflight was added.
- Code-quality reviewer approved the final proof runner and CLI changes after the subprocess
  timeout/startup fail-closed regression was added.
- CodeRabbit review was attempted. The CLI was unavailable on the PowerShell PATH, and WSL fallback
  failed with `Wsl/Service/CreateInstance/CreateVm/HCS/0x800705aa`, so no CodeRabbit review result
  was obtained.

Live proof status:

- Runner-owned health proof helper implemented: true
- Tabletop-owned External Editor listener required for real success: true
- Runner-owned health proof live-tested against real TTS: false
- Health round trip from real TTS observed: false
- Snapshot round trip from real TTS observed: false
- Server-side TTS receipt observed from real TTS: false
- `live_tts_round_trip_observed=false`

Next loop:

- Open a controlled local TTS table and run
  `.\.venv\Scripts\warhammer-companion.exe tts-proof-health --wait-seconds 30`.
- If TTS still does not expose localhost port 39999, record
  `blocker=tts-external-editor-unavailable` and continue with the operator-assisted reviewed
  Global Lua path.

## Real TTS Port Availability Attempt - 2026-06-23

Plan:

- Launch TTS directly through its installed executable.
- Avoid Computer Use, temporary boot scripts, generated command-line Lua payloads, Save & Play, and
  save mutation.
- Poll for a Tabletop-owned External Editor listener on localhost port 39999.
- If port 39999 appears, run `warhammer-companion tts-proof-health`.

Reference:

- Official TTS External Editor API documentation says TTS listens for editor messages on localhost
  port 39999: `https://api.tabletopsimulator.com/externaleditorapi/`.
- Official TTS Atom integration documentation says TTS must be running with a game loaded for
  integration commands to work: `https://api.tabletopsimulator.com/atom/`.

Result:

- Status: blocked
- Baseline `tts-proof-health --receipt baseline-no-tts --wait-seconds 0.01` exited nonzero with
  `blocker=tts-external-editor-unavailable`.
- TTS launched through the installed executable: true
- TTS process observed: true
- TTS process remained responsive during polling: true
- Poll duration before operator prompt: 90 seconds
- Poll duration after operator prompt: 5 minutes
- TTS External Editor API port 39999 observed: false
- Reviewed Lua sent to TTS: false
- Runner-owned proof listener started for live proof: false
- Health round trip from TTS observed: false
- Snapshot round trip from TTS observed: false
- Server-side TTS receipt observed from real TTS: false
- Targeted local TTS log scan found no useful External Editor or port initialization clue.
- Raw local logs, save files, workshop files, screenshots, rosters, and command-line payloads were
  not committed.

Closeout:

- `live_tts_round_trip_observed=false`
- No live TTS feasibility claim.
- Most likely next step is operator-assisted: load a controlled local TTS table/save, verify that
  the External Editor listener appears on localhost port 39999, then run
  `.\.venv\Scripts\warhammer-companion.exe tts-proof-health --wait-seconds 30`.
- If port 39999 still does not appear after a loaded game is confirmed, investigate TTS External
  Editor configuration or continue with the reviewed Global Lua operator path.

## Active Table External Editor Investigation - 2026-06-23

Result:

- Status: blocked
- Operator confirmed an active TTS table with terrain and two armies.
- TTS process observed: true
- TTS process path: installed Steam Tabletop Simulator executable.
- TTS process responsive: true
- TTS External Editor API port 39999 observed: false
- TTS editor-side port 39998 observed: false
- TTS-owned TCP listener observed: false
- `tts-proof-health --receipt active-table-check --wait-seconds 0.01` exited nonzero with
  `blocker=tts-external-editor-unavailable`.
- Local `atom` command observed on PATH: false
- Local `code` command observed on PATH: false
- Local Atom/VS Code TTS scripting package observed in standard user package directories: false
- Targeted TTS log keyword scan found no External Editor, Atom, Lua, WebRequest, 39999, or 39998
  initialization clue.
- TTS build id observed from Steam appmanifest: `22179756`.

Reference:

- Official TTS External Editor API documentation says TTS listens for editor messages on localhost
  port 39999: `https://api.tabletopsimulator.com/externaleditorapi/`.
- Official TTS Atom integration documentation says TTS must be running with a game loaded for
  integration commands to work: `https://api.tabletopsimulator.com/atom/`.

Closeout:

- Active table alone is not sufficient to expose the External Editor listener in this local setup.
- `live_tts_round_trip_observed=false`
- Continue with the operator-assisted Global Lua receipt path while separately investigating
  External Editor activation/configuration.

## Operator-Assisted Manual Proof Hardening - 2026-06-23

Reason:

- Adversarial review found that an exact receipt alone can be satisfied by any local process with
  the URL, so it proves only "some local caller had the URL" rather than a TTS Global Lua request.
- The existing plan also still pointed at `docs/tts/global_lua_echo.lua` for health proof even
  though that script has no receipt.

Implementation:

- Added `docs/tts/manual_global_health_receipt.lua`.
- Added `warhammer-companion tts-manual-health`.
- The manual proof command owns a loopback-only ephemeral health server and prints only reviewed Lua.
- The runner accepts proof only when the request has both the exact receipt query parameter and the
  reviewed `X-Warhammer-TTS-Proof` header emitted by `WebRequest.custom`.
- The evidence boundary remains narrow: this rejects browser/PowerShell/plain URL hits, but is still
  an operator-assisted local transport proof rather than cryptographic TTS-origin attestation.

Verification:

- Red test first failed with missing `run_tts_manual_health_proof`.
- Focused hardened proof tests passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_tts_manual_proof.py tests\test_tts_external_editor.py -q`
  returned 26 passed.
- Zero-wait CLI check printed the reviewed Lua with `X-Warhammer-TTS-Proof` and exited nonzero with
  `blocker=companion-receipt-not-observed`.
- Static gates passed:
  `.\.venv\Scripts\python.exe -m ruff format --check src tests`,
  `.\.venv\Scripts\python.exe -m ruff check .`, and `.\.venv\Scripts\mypy.exe src`.
- Focused TTS/web regression passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_tts_manual_proof.py tests\test_tts_external_editor.py tests\test_tts_bridge.py tests\test_web_server.py -q`
  returned 72 passed with the existing Starlette `TestClient` deprecation warning.
- Broad non-desktop regression passed:
  `.\.venv\Scripts\python.exe -m pytest --ignore=tests\test_desktop_app.py -q` returned
  505 passed with the existing Starlette `TestClient` deprecation warning.
- `git diff --check` passed with only existing CRLF normalization warnings.
- First adversarial review found the exact-receipt false-positive risk and stale plan references to
  the no-receipt `global_lua_echo.lua` health path. Those findings were accepted and fixed.
- Adversarial re-review passed with no actionable findings.
- CodeRabbit was attempted but unavailable: `coderabbit` is not on the PowerShell PATH, and WSL
  fallback failed with `Wsl/Service/CreateInstance/CreateVm/HCS/0x800705aa`.

Live proof status:

- Operator-assisted proof helper implemented: true
- Health round trip from real TTS observed: false
- Server-side TTS receipt observed from real TTS: false
- `live_tts_round_trip_observed=false`

Manual live attempt:

- Receipt: `active-table-manual-5`
- Proof server owned listener: true
- Proof server port: ephemeral loopback port 51688
- Runner stayed open for the 300-second proof window through the persistent Node REPL.
- Companion receipt observed: false
- Exit code: 1
- Blocker: `companion-receipt-not-observed`
- `live_tts_round_trip_observed=false`

Next step:

- With the active TTS table still open, run
  `.\.venv\Scripts\warhammer-companion.exe tts-manual-health --wait-seconds 300`, paste only the
  printed Lua into TTS Global Lua, and record whether the sanitized result reports
  `live_tts_round_trip_observed=true`.
