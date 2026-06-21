# Phase 4B Adversarial Review - Roster Snapshot Candidates

Date: 2026-06-21

## Review Scope

Adversarial reviewers evaluate false-authority risks, protected-data/IP guardrails, XML/profile
text handling, architecture boundaries, and QA adequacy for Phase 4B.

## Initial Findings

Reviewer: `019eeaae-0dbc-7ba1-94b1-e510635af8e0`

Initial status: failed as stated until the Phase 4B contract and guardrails were tightened.

- P0: Phase 4B needs its own spec, plan, QA, and review files before code.
- P0: the existing parser indexed only the first force; Phase 4B must not silently discard
  multi-force roster content.
- P0: embedded profile/rule/characteristic extraction is a protected-data surface and needs
  text-minimization rules.
- P1: XML safety must add whole-document structural limits before profile/rule traversal.
- P1: false-authority controls must exist on candidate records, not only at `ToolkitResult` level.

## Triage

- Accepted: add Phase 4B spec, plan, QA, and review files before implementation.
- Accepted: block multi-force and zero-force roster XML with explicit block reasons until
  force-aware indexing is designed.
- Accepted: keep rule descriptions hash/length only.
- Accepted: cap characteristic values and store long values as hash/length only.
- Accepted: add global element/depth/attribute/text and profile/rule/characteristic count limits.
- Accepted: add record-level `local_evidence`, `unresolved`, `not_official_points`, and
  `not_profile_resolution` markers.

## Implementation Review

Reviewer: `019eeab9-9805-7c13-a4ca-a998cbd25d89`

Status: changes required.

- P1: text limits were per XML node, while rule-description extraction used aggregate
  `itertext()`. Fragmented descriptions could exceed the intended cap and still import.
- P1: `source_ref_ids` were applied to snapshot profiles, but not to nested characteristic records.

Triage:

- Accepted: add a fragmented-description regression and block on aggregate collapsed description
  length before snapshot extraction.
- Accepted: add aggregate characteristic text length checks.
- Accepted: propagate source refs into nested `RosterSnapshotCharacteristic` records.

## Final Re-Review

Reviewer: `019eeabe-fc0d-7f22-b3e9-bf4fcab4d0a4`

Status: changes required.

- P1: the snapshot profile pack propagated nested characteristic source refs, but the exposed
  `RosterImportPayload.army` tree still retained parsed profiles/characteristics with empty nested
  source refs.

Triage:

- Accepted: add a regression for source refs on `payload.army.selections[*].profiles[*]` and their
  nested characteristics.
- Accepted: deep-propagate source refs through the canonical army selection tree before exposing the
  import payload, building the index, or building the snapshot pack.

## Final Re-Review 2

Reviewer: `019eeac5-197c-7000-900c-784ebf63468e`

Status: changes required.

- P1: the suite covered fragmented aggregate rule text, but not fragmented aggregate
  characteristic text.
- P1: source-ref regression coverage covered only top-level snapshot records, not nested child
  selection profiles/characteristics in both `payload.army` and `snapshot_profile_pack`.

Triage:

- Accepted: add a fragmented-characteristic aggregate text regression.
- Accepted: assert nested child profile and characteristic source refs in both the exposed army tree
  and snapshot profile pack.

## Final Approval

Reviewer: `019eead0-337e-7732-8778-2124147c562b`

Status: approved.

- Critical: none.
- Important: none.
- Minor: none.
- Prior findings are addressed: fragmented aggregate characteristic text is covered, nested child
  profile/characteristic source refs are asserted in both payload surfaces, no profile resolution or
  points authority is introduced, rule descriptions remain hash/length only, candidates stay local
  unresolved evidence, blocked imports expose no tactical payloads, and no protected source data was
  found in changed artifacts.

## Final Approval Gate

Final adversarial approval requires:

- No profile resolution, official points, legality, recommendations, UI, persistence, or solver
  integration.
- Rule description text is not retained in canonical payloads.
- Snapshot characteristics and costs remain local evidence and are never labeled official/trusted.
- Blocked hostile inputs produce no index or profile pack.
- No protected roster/profile/rule/community data is staged.
