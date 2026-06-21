# Phase 4.5 Roster Snapshot Housekeeping Spec

Date: 2026-06-21

Parent roadmap:

- `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`
- `docs/superpowers/specs/2026-06-21-roster-import-safety-and-source-records-spec.md`
- `docs/superpowers/specs/2026-06-21-roster-canonical-index-and-snapshot-profiles-spec.md`

## Goal

Keep the Phase 4 roster adapter foundation maintainable before Phase 5 movement work begins.

Phase 4B added deterministic canonical roster indexes and local snapshot profile candidates. The
pure roster snapshot builders now sit inside `application.roster_import`, mixed with source
admission, archive handling, XML parsing, and toolkit-result construction. Phase 4.5 extracts those
builders into a focused application module and adds direct contract tests.

This is a behavior-preserving housekeeping slice.

## Scope

- Create a focused roster snapshot builder module under `src/warhammer_companion/application/`.
- Move pure helper behavior for:
  - deep source-ref propagation into accepted `CanonicalArmy` trees;
  - canonical roster index construction;
  - roster snapshot profile candidate pack construction;
  - deterministic selection-key and snapshot-pack hashing.
- Update `application.roster_import` to call the extracted module.
- Add direct unit tests against the extracted builder API.
- Keep existing Phase 4A and 4B import behavior unchanged.

## Non-Goals

- No profile resolution.
- No official MFM points import or points authority.
- No roster UI, persistence, BoardState adapter, movement, threat, damage, mission, analytics, or AI
  companion behavior.
- No new supported roster formats.
- No source fetching, community-pack refresh, public-sheet import, or official/community data
  bundles.
- No web route, Jinja template, custom frontend JavaScript, desktop widget, renderer, installer, or
  packaging change.
- No official Games Workshop PDFs, roster archives, community catalogs, processed packs, generated
  databases, logs, screenshots, or protected roster/profile/rule text committed to the repository.

## Design Decisions

- The extracted module is application-layer, not domain-layer, because it assembles source-ready
  application payloads and hashes rather than defining new durable roster records.
- The public builder API remains small:
  - `canonical_army_with_source_refs(...)`
  - `build_canonical_roster_index(...)`
  - `build_roster_snapshot_profile_candidate_pack(...)`
- `build_roster_import_result_from_bytes(...)` remains the only source-admission entrypoint for
  roster bytes.
- Selection keys must remain stable across the extraction.
- Snapshot pack hashes must remain stable for identical inputs and must continue to include
  source refs, embedded local profile/rule evidence, selected XML hash, roster id, and source
  format.
- Source-ref propagation remains deep across profiles, characteristics, rules, and child
  selections.

## Acceptance Criteria

- A direct builder test fails before the new module exists and passes after extraction.
- Existing Phase 4B roster snapshot behavior is unchanged.
- Successful imports still return `estimated` roster results with no overlays and no recommendation
  language.
- Blocked imports still return no army, no roster index, and no snapshot profile pack.
- Candidate records still carry `local_evidence`, `unresolved`, `not_official_points`, and
  `not_profile_resolution` markers.
- No import result claims official points, legality, safety, recommendations, profile resolution, or
  trusted mechanics.
- `application.roster_import` becomes a thinner import/admission adapter.
- Automated checks, protected-artifact scans, desktop smoke, and manual Browser QA pass.

## Browser And Computer Use

This slice changes no UI code, but the user requested full manual QA via built-in Browser for the
phase loops. Final QA must launch the local web app and run the established route and interaction
smoke checks with Browser if available. If Browser fails, record the blocker and try Computer Use
with Firefox as the fallback.
