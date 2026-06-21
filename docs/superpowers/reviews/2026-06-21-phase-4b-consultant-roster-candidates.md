# Phase 4B Consultant Review - Roster Snapshot Candidates

Date: 2026-06-21

## Review Scope

Consultants evaluate Phase 4B decomposition, canonical roster indexing, snapshot profile/rule
candidate records, file placement, and QA coverage before profile resolution begins.

## Initial Findings

Reviewer: `019eeaad-e35e-7a20-9079-b5ed81f58a30`

Status: approved direction with required guardrails.

- Phase 4B is the correct next slice if it stays evidence/indexing only.
- Keep `.ros`/`.rosz` as the only supported inputs and reuse the Phase 4A safety gate.
- Build deterministic canonical roster indexes and local snapshot candidates only.
- Do not add profile resolution, `ProfilePack`, `PointsPack`, `BaseSizePack`, aliasing, legality,
  MFM import, UI, persistence, export, logging of raw profile text, or BoardState adapter.
- Do not key only on raw roster IDs; include sibling ordinals and/or hash-derived stable keys.
- Define extraction limits before implementation.
- The Phase 4A work-log closeout note was stale because commit `16a3884` already exists.

## Triage

- Accepted: Phase 4B records carry local-evidence/unresolved/no-authority markers.
- Accepted: add stable selection keys separate from raw roster IDs.
- Accepted: block unsupported multi-force shapes rather than silently indexing the first force.
- Accepted: add string, count, and structural XML limits.
- Accepted: update stale Phase 4A closeout note before Phase 4B commit.

## Final Approval Gate

Final consultant approval requires:

- Phase 4B stays inside local snapshot evidence and unresolved candidate records.
- The implementation does not add profile resolution, points authority, UI, persistence,
  BoardState adapter, or tactical solver behavior.
- Tests prove deterministic indexing, snapshot profile/rule extraction, rule-description hashing,
  blocked-path behavior, identity changes, and warning wording.
- Standard verification and Browser route smoke are recorded before commit.
