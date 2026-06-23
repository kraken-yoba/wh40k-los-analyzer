# TTS Phase 0 Adversarial Plan Review

Date: 2026-06-23

Initial reviewer: adversarial subagent `019ef369-119e-79a1-a4f8-0f74199ab8d8`

Re-reviewer: adversarial subagent `019ef36c-1a8b-7c63-995d-abfd570d2eaa`

Scope:

- `docs/superpowers/plans/2026-06-23-tts-phase-0-safety-baseline.md`

Initial result:

- CHANGES_REQUIRED.

P1 findings:

- Preflight expected state allowed only untracked `AGENTS.md`, but the Phase 0 plan file itself was
  also visible before implementation.
- Ignore rules did not cover the full protected artifact set named by the plan.
- Manual QA instructions could allow protected local TTS or War Organ metadata to be copied into
  the QA file or work log.

Accepted fixes:

- The preflight expectation now allows user-owned `AGENTS.md` plus this Phase 0 plan before the
  rest of the Phase 0 edits.
- The ignored local buckets now include explicit paths for TTS saves, TTS screenshots, raw rosters,
  Steam state, War Organ data, Codex state, and OpenAI state.
- Manual QA reporting is boolean-only and forbids screenshots, raw file contents, copied metadata,
  full local paths, shortcut targets, Steam account details, TTS save names, War Organ local data,
  and credential material.

Re-review result:

- PASS.
