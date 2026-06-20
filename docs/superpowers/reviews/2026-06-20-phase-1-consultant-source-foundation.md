# Phase 1 Consultant Review - Source Foundation

Date: 2026-06-20

Reviewed artifacts:

- `docs/superpowers/specs/2026-06-20-source-pack-registry-and-rulespack-current-spec.md`
- `docs/superpowers/plans/2026-06-20-source-pack-registry-and-rulespack-current.md`
- `docs/superpowers/qa/2026-06-20-source-pack-registry-and-rulespack-current-qa.md`
- `src/warhammer_companion/ingestion/rules_sources.py`
- `tests/test_rules_sources.py`
- `docs/work-log/player-toolkit-implementation.md`

## Scope

Consultant review checks source freshness, architecture fit, minimality, and handoff readiness for
later rules-aware toolkit phases.

## Findings

- Source research consultant approved a metadata-only Phase 1 slice that stores source metadata,
  readiness states, source refs, terminology candidates, and no copied rules/PDF text.
- Source research found current metadata: MFM updated `17/6/2026`, MFM version `v1.0`, current core
  rules PDF candidate URL, New Recruit BattleScribe compatibility, and BSData as community data.
- Source research warned that the direct core rules PDF asset must be treated as a candidate until
  fetched and hashed successfully.
- Architecture consultant approved `src/warhammer_companion/ingestion/rules_sources.py` as the
  correct placement and advised no service, CLI, UI, `MapPacket`, or LOS changes in this slice.
- Architecture consultant recommended frozen dataclasses, strict typed APIs, source-pending
  concepts, no trusted concepts, and tests for mutable source metadata and legacy blockers.

## Triage

- Accepted: the implementation is metadata-only and does not bundle official/community/user data.
- Accepted: `verify_remote_http_source()` streams bytes and computes SHA-256 only when explicitly
  called; tests use an injected fake response and do not make live network calls.
- Accepted: no service, CLI, web, desktop, `MapPacket`, or LOS behavior is changed.
- Accepted: all current concepts are `source_pending`; no concept is `trusted_ref`.
- Accepted: final consultant review found that non-200 responses could be trusted if an injected
  response no-opped `raise_for_status()`. The verifier now blocks any status other than 200 before
  hashing, and tests prove failed status cannot return `trusted_ref`.

## Final Status

Final consultant approval: `APPROVED`.

Approver: `019ee4f2-376b-75e3-b5a3-f615cda286e2`

Final approval findings:

- Non-200 remote verifier blocker is fixed.
- Regression test `test_verify_remote_http_source_blocks_failed_status` exists.
- Targeted tests pass: 11 passed.
- Review records and work log record the accepted verifier/freshness hardening.
