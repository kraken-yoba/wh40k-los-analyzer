# Phase 3.5 Adversarial Review - Semantics Identity Hardening

Date: 2026-06-21

## Review Scope

Adversarial reviewers evaluate whether the Phase 3.5 slice closes blocker-class risks before
Phase 4 hostile input handling starts.

## Initial Findings

Reviewer: `019ee952-a817-7fe0-8698-a25dd8f3e7b7`

Initial status: changes required before direct Phase 4 implementation.

- P1: do not implement roster/profile adapters until Phase 4 is split into safe quarantine/parse,
  canonical roster, and profile-resolution sub-slices with malicious archive/XML fixtures and
  artifact scans.
- P2: terrain semantics result identity ignores `source_ref_ids` and source freshness.
- P2: empty manual footprints can be reported as `estimated`.
- P2: hull/custom base shapes can be represented without enough geometry or measurement policy.
- P3: manual model-frame hash omits audit fields such as labels and reason.

## Triage

- Accepted: Phase 3.5 happens before Phase 4 implementation.
- Accepted: add terrain source-ref and source-freshness identity tests and fixes.
- Accepted: block empty manual unit footprints and preserve footprint source refs.
- Accepted: reject unsupported hull/custom base geometry explicitly.
- Accepted: replace partial manual model-frame hashing with a structured canonical hash.

## Final Approval Gate

Final adversarial approval requires:

- Failing tests were observed before implementation.
- Provenance-affecting fields no longer collide in Phase 3.5 toolkit hashes.
- Empty footprints and unsupported base shapes cannot produce usable-looking records.
- No protected source data, raw roster/community imports, UI behavior, LOS behavior, or rendering
  behavior was added by this housekeeping slice.

## Final Review

Reviewer: `019ee96e-04e3-7fb3-a2ee-64cf4f6b8cb2`

Status: changes required.

- P2: runtime input could still construct `BaseGeometry(shape="triangle")` because `BaseShape` is
  only a type hint and `__post_init__` did not enforce an explicit shape whitelist.

Triage:

- Accepted: add a hostile runtime-string regression.
- Accepted: add an explicit runtime whitelist for all currently recognized base-shape literals.
- Accepted: continue blocking `hull` and `custom` until a future footprint policy exists.

## Final Re-Review

Reviewer: `019ee971-f6db-7fc1-84bb-15c7ffdcdd14`

Status: approved.

Outcome:

- No critical or important findings remain.
- Runtime shape whitelist rejects unknown shape strings before a record can become usable.
- Hostile `BaseGeometry(shape="triangle")` regression covers the prior bypass.
- Reviewer ran the targeted Phase 3.5 test suite and `git diff --check`; both passed, with only
  normal LF-to-CRLF warnings from Git.
