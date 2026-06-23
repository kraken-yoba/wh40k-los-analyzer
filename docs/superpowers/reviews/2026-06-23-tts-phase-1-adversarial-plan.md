# TTS Phase 1 Adversarial Plan Review

Date: 2026-06-23

Initial reviewer: adversarial subagent `019ef392-c135-7561-91b1-97564c14c211`

Scope:

- `docs/superpowers/plans/2026-06-23-tts-phase-1-feasibility-harness.md`

Initial result:

- CHANGES_REQUIRED.

P1 findings:

- The plan still advanced unconditionally to Phase 1.5 even when live TTS was unavailable.
- Malformed API payload handling could leak raw input through default FastAPI/Pydantic 422 bodies.
- Accepted snapshot responses risked echoing live TTS payload data once real snapshots include
  session/save/object metadata.

Accepted fixes:

- The plan now has a hard contracts-only closeout gate: without an observed real TTS
  `WebRequest.custom` round trip, the commit/work-log/next loop must say live TTS feasibility
  remains incomplete and the next loop is to prove the live round trip.
- The plan now requires the `/api/tts/snapshot` route to accept raw dictionaries and call bridge
  validation itself so invalid snapshots return the sanitized typed error envelope.
- Accepted snapshot responses now return only response schema/version, deterministic hash, object
  counts, diagnostic warning labels, and sanitized readiness metadata. They must not echo submitted
  snapshot bodies.

Re-review result:

- PASS.
