# TTS Phase 1 Live Proof Adversarial Plan Review

Date: 2026-06-23

Initial reviewer: adversarial subagent `019ef3c3-01f2-7880-bd0a-70a5e28da1e8`

Scope:

- `docs/superpowers/plans/2026-06-23-tts-phase-1-live-round-trip-proof.md`

Initial result:

- CHANGES_REQUIRED.

P0 finding:

- Proof criteria were ambiguous without a server-side observation method.

P1 findings:

- The plan under-specified safe TTS save handling before Lua injection.
- The artifact leak scan omitted review records and staged diff hygiene.
- Cleanup was not failure-safe.
- Proof-success wording risked broad overclaiming.

Accepted fixes:

- The plan now requires a local-only sanitized server-side receipt that distinguishes TTS-originated
  `WebRequest.custom` traffic from PowerShell probes.
- The plan now requires a throwaway/controlled development save before Lua injection and explicitly
  forbids Save, Save & Play, Workshop upload, export, or local save mutation.
- The docs scan includes the review records and the plan requires cached diff scope/hygiene checks.
- Cleanup is now an always-run step for every launched companion/TTS path.
- Success wording is restricted to `live_tts_round_trip_observed=true`,
  `readiness=contracts-only`, and `source=TTS Global Lua WebRequest.custom`.

Re-review result:

- PASS.

## Programmatic Helper Review

Reviewer: adversarial subagent `019ef3e7-f623-7281-9111-ebdab60c7942`

Initial result:

- CHANGES_REQUIRED.

P1 findings:

- The companion base URL could alter the reviewed Lua template because raw local URL content was
  inserted into a quoted Lua string.
- The documented local/reviewed boundary was not enforced because the CLI accepted arbitrary script
  files and arbitrary TTS hosts.

P2 findings:

- CLI success meant only "bytes sent" and did not prove companion receipt.
- Tests covered broad unsafe behavior but lacked negative coverage for unsafe URL, host, and script
  inputs.

Accepted fixes:

- Companion base URLs are canonicalized to local HTTP origins only.
- TTS host validation is loopback-only.
- The CLI restricts script execution to reviewed `docs/tts` templates.
- CLI/README wording now requires companion receipt verification before treating the proof as live.
- Tests now cover unsafe URL inputs, unsafe receipts, non-loopback hosts, unreviewed templates, and
  the reviewed-template CLI path.

Re-review result:

- PASS.
