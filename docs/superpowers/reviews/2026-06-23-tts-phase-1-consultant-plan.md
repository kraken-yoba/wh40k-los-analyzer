# TTS Phase 1 Consultant Plan Review

Date: 2026-06-23

Initial reviewer: consultant subagent `019ef392-acb1-77f2-a06e-7b64c1dd3d27`

Scope:

- `docs/superpowers/plans/2026-06-23-tts-phase-1-feasibility-harness.md`

Initial result:

- CHANGES_REQUIRED.

P1 findings:

- API error envelope was underspecified. The plan required safe 422 details but did not require all
  bridge/API failures to use the same typed `TtsBridgeResponse(ok=false, error=...)` shape.
- Manual QA expected beam/marker observation while the Lua task only required placeholder visual
  functions.

Accepted fixes:

- The plan now requires the snapshot route to convert invalid payloads into the sanitized
  `TtsBridgeResponse(ok=false, error={code,message,field_path})` envelope and to test that raw
  validation payloads and protected-looking inputs are absent from response bodies.
- The plan now requires minimal visual helper behavior when TTS can be run, or explicit
  `unobserved` visual status with live feasibility kept incomplete when it cannot.

Re-review result:

- PASS.
