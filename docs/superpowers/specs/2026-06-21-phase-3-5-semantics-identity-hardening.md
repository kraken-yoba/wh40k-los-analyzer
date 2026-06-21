# Phase 3.5 Semantics Identity Hardening Spec

Date: 2026-06-21

Parent roadmap:

- `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`
- `docs/superpowers/specs/2026-06-20-base-size-and-terrain-semantics-spec.md`

## Goal

Close small provenance, identity, and unsupported-shape gaps in the Phase 3 semantics foundation
before Phase 4 introduces roster archives, XML, pasted text, and community-derived profile data.

This is a housekeeping hardening slice. It does not add roster import, profile resolution, movement
reach, threat range, UI behavior, or official/community data bundles.

## Scope

Harden the existing Phase 3 contracts in four focused ways:

- Terrain semantics toolkit input identity must include provenance-sensitive inputs.
- Manual model-frame toolkit input identity must use a structured canonical payload instead of a
  partial delimited string.
- Empty manual unit footprints must not be treated as usable estimated inputs.
- Unsupported hull/custom base shapes must fail explicitly until the app has a real footprint
  geometry or measurement policy for them.

## Non-Goals

- No roster, `.ros`, `.rosz`, New Recruit, BattleScribe, BSData, or pasted-roster parsing.
- No profile, points, datasheet, mission, damage, movement, threat, analytics, or AI companion
  implementation.
- No source fetching, PDF ingestion, public-sheet ingestion, or community-pack ingestion.
- No web route, Jinja template, custom frontend JavaScript, desktop screen, renderer, or packaging
  change.
- No official Games Workshop source PDFs, mission-card images, roster archives, community catalogs,
  processed packs, or protected text committed to the repository.

## Design Decisions

- Phase 4 implementation is blocked until its fine-grain spec and QA path are written. Phase 3.5 is
  only a prerequisite hardening loop.
- Result identity should account for all durable inputs that influence payload provenance or audit
  meaning. Hashes do not need to include rendered UI state because this slice has no UI projection.
- Provenance source refs are canonicalized as a sorted unique set for hashing. This avoids cache
  churn from tuple order while still changing identity when the source set changes.
- Non-finite numeric inputs still produce blocked toolkit results instead of uncaught exceptions.
  Hashing must therefore encode non-finite values safely before validation rejects them.
- `BaseShape` may keep future shape literals, but hull/custom are unsupported in Phase 3.5 unless a
  future slice adds explicit polygon footprint or measurement-policy fields.

## Acceptance Criteria

- `build_terrain_semantics_result(...)` input hashes change when `source_ref_ids` change.
- `build_terrain_semantics_result(...)` input hashes change when source freshness changes.
- Stale terrain source freshness produces a blocked result with no overlays.
- `build_manual_model_frame_result(...)` input hashes change when `model_label`, `base_label`,
  `reason`, or `source_ref_ids` change.
- Non-finite manual base dimensions still return blocked toolkit results, not uncaught hash errors.
- `ManualUnitFootprint.readiness_report()` blocks empty footprints with `missing-unit-models`.
- `ManualUnitFootprint.readiness_report()` preserves footprint-level source refs.
- `BaseGeometry(shape="hull")` and `BaseGeometry(shape="custom")` fail with an explicit unsupported
  shape error until a source-backed footprint geometry policy exists.
- Existing LOS, rendering, packet validation, web, and desktop behavior remains unchanged.

## Browser And Computer Use

This slice changes no UI code, but the user has requested full manual QA via built-in Browser for
the ongoing phase loops. Final QA must therefore launch the local web app and run the established
route and interaction smoke checks with Browser if the Browser tool is available. If Browser fails,
record the blocker and try Computer Use/Firefox as the fallback.
