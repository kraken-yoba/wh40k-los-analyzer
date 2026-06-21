# Roster Canonical Index And Snapshot Profiles Spec

Date: 2026-06-21

## Goal

Add the next narrow Phase 4B roster-enrichment slice after Phase 4A: deterministic canonical roster
indexing plus local roster-snapshot profile/rule evidence extracted from admitted synthetic
`.ros`/`.rosz` inputs.

This phase makes imported rosters more useful for later profile resolution, base-size enrichment,
movement, threat, damage, and matchup tools while preserving the Phase 4A trust boundary.

## Scope

Implement local, deterministic records for:

- A canonical selection index over `CanonicalArmy`.
- Source-path-addressable embedded roster profiles and characteristics.
- Source-path-addressable embedded roster rule references with description hashes/lengths, not rule
  description text.
- Unresolved profile candidates attached to roster selections.
- Toolkit import payload enrichment that remains `estimated`, has no overlays, and cannot produce
  recommendation/legal/safe/official-points language.

Supported input remains exactly the Phase 4A admitted input set:

- `.ros` XML bytes that pass the existing XML quarantine gate.
- `.rosz` archive bytes that pass the existing archive quarantine gate and contain one selected
  `.ros` member.

## Non-Goals

- No profile resolution against official, community, BSData, New Recruit, YellowScribe, or local
  profile packs.
- No official MFM import, points authority, points divergence checks, legality checks, or list
  validation.
- No movement, threat, damage, survivability, mission, deployment, team-pairing, or AI companion
  behavior.
- No web UI, desktop UI, upload workflow, persistence, export workflow, or BoardState adapter.
- No pasted roster text, `.cat`, `.catz`, `.gst`, `.gstz`, `.bsr`, or community-pack refresh.
- No real roster archives, community catalogs, official PDFs, protected profile/rule text, or
  processed roster packs committed to the repository.

## Safety Hardening Decisions

Phase 4B expands the local XML surface beyond Phase 4A shallow selections, so it adds stricter
admission limits before snapshot extraction:

- The parser must block rosters with zero forces or more than one force until the canonical data
  model supports force-aware roster indexing. This is an explicit unsupported shape, not silent
  discard.
- The parser must enforce whole-document structural limits for element count, element depth,
  attributes per element, attribute/text length, profiles per selection, rules per selection, and
  characteristics per profile.
- Extracted characteristic values are capped. Short synthetic/stat-like values may be stored as
  presented; longer values must be represented by SHA-256 and length only.
- Rule descriptions are always represented by SHA-256 and length only.

## Data Model

Extend `domain.rosters` with immutable records:

- `RosterSnapshotCharacteristic`: raw ID, name, type ID, source path, optional short value as
  presented, value SHA-256, and value length.
- `RosterSnapshotProfile`: raw ID, name, type ID/name, source path, and characteristics.
- `RosterSnapshotRule`: raw ID, name, source path, optional description SHA-256, and description
  length. Do not store rule description text in the canonical toolkit payload.
- `RosterSnapshotProfileCandidatePack`: roster ID, format, source refs, selected XML hash, pack
  hash, readiness, profiles, rules, source policy `local_evidence`, and authority marker
  `not_source_authority`.
- `RosterProfileCandidate`: selection ID/name/type/source path, unresolved status, referenced
  profile IDs, rule IDs, cost IDs, source policy `local_evidence`, points authority
  `not_official_points`, and mechanics authority `not_profile_resolution`.
- `RosterSelectionIndexEntry`: selection ID/name/type/source path, depth, child/profile/rule/cost
  counts, and a stable selection key derived from source path plus sibling ordinal.
- `CanonicalRosterIndex`: roster ID/name, total selection count, top-level selection count, type
  counts, index entries, and unresolved candidate records.

`ProfileResolutionStatus` is declared now for future phases:

- `resolved_exact`
- `resolved_alias`
- `resolved_manual`
- `ambiguous`
- `unresolved`
- `unsupported`

Phase 4B only emits `unresolved`.

## Parser Behavior

The existing XML safety gate remains authoritative. After an XML document is admitted:

- Extract profiles nested under each selection's direct `profiles` child.
- Extract profile characteristics nested under each profile's direct `characteristics` child.
- Extract rules nested under each selection's direct `rules` child.
- Record profile/rule source paths under the owning selection path.
- Include sibling ordinals when deriving stable selection keys so duplicate raw selection IDs do not
  collide.
- Hash rule descriptions but do not store the text in canonical records.
- Store characteristic values as text only when they pass the configured short-value cap; otherwise
  store only hash and length.
- Keep all candidate records local evidence. Do not convert roster profiles/rules into mechanics.

If a selection has no embedded profiles/rules, it still appears in the canonical index and gets an
unresolved candidate with empty profile/rule refs.

## Application Behavior

`build_roster_import_result_from_bytes(...)` enriches successful import payloads with:

- `CanonicalRosterIndex`
- `RosterSnapshotProfileCandidatePack`

Blocked imports still have no canonical army, no index, no snapshot pack, and no overlays.

Successful imports remain:

- `readiness = "estimated"`
- `tool_id = "roster_import"`
- no overlays
- no recommendation language

Warnings must explicitly say that roster snapshot profiles, rules, characteristics, and costs are
local evidence, not source authority.

## Acceptance Criteria

- Synthetic `.ros` XML with embedded profiles, characteristics, rules, nested selections, and costs
  produces an estimated import payload with a canonical army, selection index, unresolved
  candidates, and snapshot profile pack.
- Nested selection profiles/rules are not silently discarded.
- Multi-force roster XML is blocked with an explicit unsupported-shape block reason until force-aware
  indexing is implemented.
- Duplicate raw selection IDs do not collide in the canonical index.
- Rule descriptions are represented only by hash and length in canonical records.
- Long characteristic values are represented only by hash and length in canonical records.
- Candidate statuses are `unresolved`; no candidate is marked resolved, legal, official, or trusted.
- Import hash and snapshot pack hash change when embedded profile/rule/characteristic data changes.
- Excessive non-selection nesting, excessive element count, excessive attributes, excessive
  profile/rule/characteristic counts, and excessive text lengths produce blocked results.
- Blocked Phase 4A inputs remain blocked and produce no index/profile pack.
- Existing Phase 4A archive/XML hardening tests still pass.
- Existing LOS, rendering, web, desktop, packet validation, and Phase 1-3.5 contracts remain
  unchanged.

## Security And Source Trust

- Treat roster snapshot profiles/rules as user-local evidence only.
- Do not treat roster snapshot costs as official points.
- Do not store, display, log, export, or commit real roster/profile/rule text in this phase.
- Keep source refs and source paths so future resolution can explain every candidate.
- Keep all fixtures synthetic and intentionally non-games-specific.

## Browser And Computer Use

Phase 4B changes no UI, but the active roadmap loop requires manual QA. Final closeout must run
the established Browser route sweep against the local web app. If Browser fails, record the exact
blocker and try Computer Use/Firefox before marking manual UI QA blocked.
