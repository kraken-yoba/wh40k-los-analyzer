# TTS Phase 1 Consultant Closeout Review

Date: 2026-06-23

Reviewer: consultant subagent `019ef3b1-29a9-79b1-a658-eec973833d46`

Scope:

- Phase 1 implementation diff for TTS bridge contracts, API routes, Lua harness template, sanitized
  fixture, tests, QA, and work log.

Result:

- CHANGES_REQUIRED.

P1 finding:

- `/api/tts/snapshot` still used FastAPI body parsing for invalid JSON bodies, so malformed JSON
  returned the default FastAPI `detail` response instead of the typed TTS bridge error envelope.

Accepted fix:

- The snapshot route now reads `request.json()` itself and converts JSON decode failures into
  `TtsBridgeResponse(ok=false, error={code,message,field_path})` with `code=invalid-json`.
- A regression test posts malformed JSON and asserts the response has no `detail` field and no
  `json_invalid` leak.

Re-review result:

- PASS.

Re-review notes:

- The malformed JSON path now returns the typed `TtsBridgeResponse` envelope.
- The reviewer spot-verified the live route response and confirmed accepted snapshot readiness is
  server-authoritative as `contracts-only`.

Notes:

- CodeRabbit was attempted but blocked: PowerShell has no `coderabbit` command and WSL failed with
  `Wsl/Service/CreateInstance/CreateVm/HCS/0x800705aa`.
