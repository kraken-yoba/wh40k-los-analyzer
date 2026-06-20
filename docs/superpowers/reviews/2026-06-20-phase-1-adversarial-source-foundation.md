# Phase 1 Adversarial Review - Source Foundation

Date: 2026-06-20

Reviewed artifacts:

- `docs/superpowers/specs/2026-06-20-source-pack-registry-and-rulespack-current-spec.md`
- `docs/superpowers/plans/2026-06-20-source-pack-registry-and-rulespack-current.md`
- `docs/superpowers/qa/2026-06-20-source-pack-registry-and-rulespack-current-qa.md`
- `src/warhammer_companion/ingestion/rules_sources.py`
- `tests/test_rules_sources.py`
- `docs/work-log/player-toolkit-implementation.md`

## Scope

Adversarial review checks source-trust/IP/security, protected-content redistribution risk,
unsupported trusted claims, stale-source failure modes, QA adequacy, and Phase 1 scope creep.

## Findings

- Initial adversarial review found no copied protected rules text, bundled PDFs/data, Phase 1 scope
  creep, hard-coded `11e` module/schema naming, or untracked-file QA blind spot.
- Initial adversarial review found the remote verifier was too easy to trust and needed explicit
  URL allowlisting, redirect validation, status-code checks, byte-size/content-type/hash checks,
  and tests for failed source metadata.
- Initial adversarial review found MFM freshness was hard-coded as `current` without requiring a
  refresh timestamp.

## Triage

- Accepted: `verify_remote_http_source()` now validates HTTPS and approved hosts before network
  access.
- Accepted: redirected final URLs are validated and unapproved redirects return `blocked`.
- Accepted: non-200 responses, empty content, and missing content type return `blocked`.
- Accepted: MFM freshness is `unknown` unless `build_current_rules_foundation()` receives a
  refresh timestamp.
- Accepted: tests cover failed status, incomplete metadata, rejected host, rejected redirect, and
  refresh-timestamp-gated freshness.

## Final Status

Final adversarial approval: `APPROVED`.

Approver: `019ee4f2-6019-78d1-b684-43c09d549a91`

Final approval findings:

- Initial URL validation requires HTTPS and an approved host before fetch.
- Redirect final URL validation blocks unapproved targets.
- Non-200 responses, empty content, and missing content type return `blocked`.
- `trusted_ref` is returned only after approved source checks, status 200, bytes, content type, and
  SHA-256.
- MFM freshness is `unknown` unless `retrieved_at` is supplied.
- No copied protected rules text was found in implementation or tests.
