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
