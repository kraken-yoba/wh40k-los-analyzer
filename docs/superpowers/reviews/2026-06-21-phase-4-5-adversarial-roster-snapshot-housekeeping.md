# Phase 4.5 Adversarial Review - Roster Snapshot Housekeeping

Date: 2026-06-21

## Review Scope

Adversarial reviewers evaluate whether the Phase 4.5 extraction could accidentally change roster
import behavior, weaken source-trust/security guarantees, broaden roster authority, or hide new
features under a housekeeping label.

## Initial Findings

Reviewer: `019eebac-9415-7510-ae38-42e0e1b2767d`

Status: approved only as a narrow behavior-preserving extraction.

- Stable identity semantics are part of the Phase 4B contract. Extraction must not change selection
  keys, duplicate handling, ordinal paths, snapshot pack hash fields, or source-ref normalization.
- Source refs must remain deep through `payload.army`, nested profiles, characteristics,
  `roster_index`, and `snapshot_profile_pack`.
- Candidate authority markers must remain unresolved, local, non-official-points, and
  non-profile-resolution.
- Rule descriptions must remain hash/length only, and long characteristic values must remain
  hash/length only.
- Archive and XML admission limits belong in `ingestion`; the new helper module must not parse
  bytes, inspect archives, parse XML, or move quarantine logic.

## Triage

- Accepted: direct tests must cover index counts, parent keys, depths, sibling ordinals, duplicate
  raw IDs, source paths, candidate authority markers, nested source refs, snapshot hash identity,
  and no retained rule-description text.
- Accepted: existing Phase 4A/4B tests must pass after extraction.
- Accepted: run a narrow import-boundary check that `domain` and `ingestion` do not import the new
  application helper module.
- Accepted: avoid changes to `domain.rosters`, `ingestion.roster_xml`, `ingestion.roster_archives`,
  web, desktop, persistence, BoardState, movement, threat, damage, mission, analytics, AI,
  official-source, points, or profile-resolution files.

## Final Approval Gate

Final adversarial approval requires:

- Existing Phase 4A and Phase 4B tests still pass.
- Blocked imports still produce no army, roster index, or snapshot profile pack.
- Extracted builders do not parse bytes, inspect archives, parse XML, call external services, or
  introduce profile resolution/points authority.
- Source refs and snapshot hashes remain deterministic.
- Protected-artifact scans and manual Browser QA are recorded before commit.

## Implementation Review

Reviewer: `019eebb2-3146-7530-9614-267372618b96`

Status: ready, no critical or important findings.

Minor finding:

- Direct tests could more explicitly lock source-ref hash normalization behavior.

Triage:

- Accepted: added a direct test that `("source:b", "source:a", "source:a")` and
  `("source:a", "source:b")` produce the same `pack_hash` while exposed `source_ref_ids` preserve
  the original tuple.

Outcome:

- The reviewer found no domain or ingestion safety drift and no downstream product-surface changes.
- The reviewer locally verified the roster regression suite, Ruff format/check, mypy, and
  `git diff --check`.
