# TTS Phase 1 Live Proof Consultant Plan Review

Date: 2026-06-23

Initial reviewer: consultant subagent `019ef3c2-eda1-7a61-bdad-79d37d0ea70f`

Scope:

- `docs/superpowers/plans/2026-06-23-tts-phase-1-live-round-trip-proof.md`

Initial result:

- CHANGES_REQUIRED.

P0 finding:

- The plan required companion receipt but had no authoritative proof source beyond TTS/UI output.

P1 findings:

- Preflight checked only the commit subject rather than requiring Phase 1 contracts commit `887335c`
  to be HEAD or an ancestor.
- The docs scan omitted the review records that may be committed.

Accepted fixes:

- The plan now requires a local-only server receipt, such as stdout or an in-memory counter, that
  distinguishes the TTS-originated request from PowerShell probes. Committed evidence remains
  sanitized.
- The plan now requires `git merge-base --is-ancestor 887335c HEAD`.
- The docs scan includes both live-proof review records.

Re-review result:

- PASS.

## Programmatic Helper Review

Reviewer: consultant subagent `019ef3e7-e1a5-7fd1-83b4-61664f17ccfc`

Initial result:

- CHANGES_REQUIRED.

P1 finding:

- The companion base URL was substituted into Lua without strict local-origin canonicalization.

P2 findings:

- The TTS External Editor host option accepted non-loopback hosts despite the localhost-only proof
  boundary.
- The CLI could send arbitrary script files despite the reviewed-template policy.

Accepted fixes:

- Companion base URL validation now accepts only canonical local HTTP origins with no userinfo,
  path, query, params, or fragment.
- TTS External Editor host validation is loopback-only.
- The CLI resolves `--script-file` through a reviewed `docs/tts` template allowlist.
- README and CLI wording now say a sent message is not live proof until the companion receipt is
  verified.

Re-review result:

- PASS.
