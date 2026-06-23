# TTS Phase 1 Adversarial Closeout Review

Date: 2026-06-23

Reviewer: adversarial subagent `019ef3b1-3df9-74c3-9aae-54d464dda5d1`

Scope:

- Phase 1 implementation diff for TTS bridge contracts, API routes, Lua harness template, sanitized
  fixture, tests, QA, and work log.

Result:

- CHANGES_REQUIRED.

P1 finding:

- `live_tts_round_trip_observed` and live readiness were derived from the submitted snapshot, so a
  client could claim live TTS feasibility without server-side evidence.

Accepted fix:

- Accepted snapshot responses now report `live_tts_round_trip_observed=false` and
  `readiness=contracts-only` from server-owned Phase 1 state, regardless of the submitted host
  context.
- A regression test submits a valid snapshot with `host_context.live_tts_round_trip_observed=true`
  and asserts the accepted response remains contracts-only.

Re-review result:

- PASS.

Re-review notes:

- Accepted snapshot responses now keep `live_tts_round_trip_observed=false` and
  `readiness=contracts-only` regardless of submitted host context.
- The reviewer checked malformed JSON handling, `WebRequest.custom` usage, absence of
  `WebRequest.post`, sanitized invalid-response tests, staged state, and work-log evidence.
- Reviewer reran `.\.venv\Scripts\python.exe -m pytest tests\test_tts_bridge.py tests\test_web_server.py -q`,
  which returned 46 passed with the existing Starlette `TestClient` deprecation warning.

Notes:

- CodeRabbit was attempted but blocked: PowerShell has no `coderabbit` command and WSL failed with
  `Wsl/Service/CreateInstance/CreateVm/HCS/0x800705aa`.
