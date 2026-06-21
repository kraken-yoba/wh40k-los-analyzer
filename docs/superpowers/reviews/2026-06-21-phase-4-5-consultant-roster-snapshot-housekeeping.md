# Phase 4.5 Consultant Review - Roster Snapshot Housekeeping

Date: 2026-06-21

## Review Scope

Consultant reviewers evaluate whether extracting roster snapshot/index builder behavior from
`application.roster_import` is the right narrow housekeeping target after Phase 4B and before Phase
5 movement work.

## Initial Findings

Reviewer: `019eebac-62b1-7983-adbd-0ac8ac4d44ee`

Status: approved with guardrails.

- The proposed extraction is the right Phase 4.5 housekeeping target before Phase 5.
- `application.roster_import` currently mixes admission orchestration with pure roster projections:
  source-ref propagation, canonical index building, snapshot profile pack construction, selection
  key hashing, and pack hashing.
- Extracting those pure helpers makes later profile-resolution work less likely to mutate the
  hostile-input admission boundary.
- The extraction must be more than cosmetic: the new module needs direct contracts, not just moved
  private functions.

## Triage

- Accepted: keep `build_roster_import_result_from_bytes(...)` behavior and payload shape identical.
- Accepted: keep durable dataclasses in `domain.rosters`.
- Accepted: make the new module pure: no archive inspection, XML parsing, filesystem, UI,
  persistence, BoardState, profile resolution, official points, or solver imports.
- Accepted: preserve `estimated`, `local_evidence`, `not_source_authority`, `not_official_points`,
  and `not_profile_resolution` boundaries.
- Accepted: direct tests must cover stable duplicate selection keys, parent/depth/source paths,
  source-ref propagation into nested profiles/characteristics, snapshot hash sensitivity, and no
  retained rule-description text.
- Accepted: keep existing `test_roster_snapshot_profiles.py` behavior passing unchanged.

## Final Approval Gate

Final consultant approval requires:

- The slice remains behavior-preserving housekeeping.
- The extracted module has a small application-layer API.
- Direct tests prove deep source refs, roster index identity, candidate markers, and snapshot pack
  hash behavior.
- No profile resolution, official points, UI, persistence, BoardState, movement, threat, damage,
  mission, analytics, or AI scope is introduced.

## Implementation Review

Reviewer: `019eebb1-ff3d-7742-8b76-2f7e64e35eb4`

Status: approved.

Outcome:

- No Phase 4.5 spec-compliance issues found.
- `build_roster_import_result_from_bytes(...)` remains the only roster byte-admission entrypoint.
- The new `application.roster_snapshots` module contains typed pure builders only.
- Source-ref propagation, selection-key hashing, snapshot-pack hashing, unresolved/local authority
  markers, and rule-description hash/length behavior are preserved.
- No `domain` or `ingestion` import of `application.roster_snapshots` was found.
