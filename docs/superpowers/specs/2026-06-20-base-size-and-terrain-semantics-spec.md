# Base Size And Terrain Semantics Spec

Date: 2026-06-20

Parent roadmap:

- `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`

## Goal

Add the first source-aware base-size, model-frame, manual footprint, and terrain semantics
records needed by later movement, threat, and exposure tools.

This phase does not add movement or threat solvers. It defines deterministic inputs those solvers
can consume without requiring roster/profile import first.

## Scope

Add focused domain and application modules that can represent:

- Manual model base records with source refs and explicit manual-fallback readiness.
- Unknown or unresolved base records that block legal/safe claims.
- Model-frame records that bind a model label to base geometry assumptions.
- Manual unit footprints made from model-frame records.
- Terrain area/feature semantics adapted from an existing `MapPacket`.
- Readiness and warning aggregation for future movement/threat/exposure tools.

The adapter must treat `MapPacket` as layout geometry only. It must not mutate packets or store
rules mechanics inside packet models.

## Non-Goals

- No roster, profile, points, or datasheet import.
- No official rules text extraction.
- No bundled official PDFs, mission-card images, roster exports, community catalogs, or copied
  rules passages.
- No movement reach, threat range, damage, mission, team-pairing, AI, web, desktop, or rendering
  UI changes.
- No custom frontend JavaScript or TypeScript.

## Data Model

Create immutable domain dataclasses:

- `BaseGeometry`: normalized base shape and dimensions in inches.
- `BaseSizeRecord`: source-aware base-size record.
- `ModelFrameRecord`: model label plus optional base record.
- `ManualUnitFootprint`: rosterless/manual unit footprint input for early tools.
- `TerrainSemanticsRecord`: terrain-area, dense-feature, or light-feature semantics derived from
  a map packet.
- `TerrainSemanticsIndex`: packet-level semantics collection and lookup helpers.
- `SemanticsReadinessReport`: aggregated readiness, warnings, and block reasons.

Implemented module boundaries should be:

- `warhammer_companion.domain.semantics`: shared field-source, validation, block-reason, and
  readiness reducer primitives.
- `warhammer_companion.domain.base_sizes`: base, model-frame, and manual footprint records.
- `warhammer_companion.domain.terrain_semantics`: `MapPacket` terrain adapter records.
- `warhammer_companion.application.base_sizes`: thin `ToolkitResult` builder for manual
  model-frame records.
- `warhammer_companion.application.terrain_semantics`: thin `ToolkitResult` builder for terrain
  semantics records.

The domain modules may reuse `ToolkitReadiness`, `ToolkitAssumption`, and `ToolkitWarning`, but
they must remain domain-focused and avoid importing web, desktop, rendering, or solver code.

## Readiness Rules

Manual base entries:

- Are useful for exploratory geometry.
- Must be `estimated`, not `trusted`.
- Must carry a manual-entry warning and at least one source ref when provided.

Unknown base entries:

- Must be `blocked`.
- Must add a block reason such as `missing-base-size`.
- Must not allow trusted legal/safe claim wording.

Terrain semantics derived from current packet geometry:

- Preserve current LOS blocker flags.
- Are `estimated` until terrain category, visibility trait, movement trait, and vertical assumptions
  are source-backed.
- Must warn on unknown terrain traits and vertical/height assumptions.

Incompatible source pack versions:

- Must downgrade the aggregate report to `blocked`.
- Must expose a block reason that later tools can surface to the user.

## API Contract

Future movement, threat, and exposure APIs should be able to accept:

- `ManualUnitFootprint`
- `TerrainSemanticsIndex`
- `SemanticsReadinessReport`

without caring whether base data came from manual entry, roster import, profile resolution, or a
future official/community profile adapter.

This means the source identity and readiness belong on the records, not in solver-specific
parameters.

## Acceptance Criteria

- A player can create manual round or oval base records without roster import.
- Manual base records are `estimated` and carry manual-fallback warnings.
- Unknown base records are `blocked` and cannot allow legal/safe trusted claims.
- Manual unit footprints aggregate model-frame readiness and report missing bases.
- `TerrainSemanticsIndex.from_packet(packet)` creates area, dense-feature, and light-feature
  semantics without mutating the packet.
- Dense-feature `blocks_los_2d` values match the current `MapPacket` LOS model.
- Unknown terrain traits and vertical assumptions prevent trusted legal/safe claims.
- Incompatible source packs block aggregate semantics reports.
- Existing LOS toolkit, rendering, and packet validation behavior remains unchanged.

## Browser And Computer Use

This phase changes no web route, Jinja template, static asset, generated SVG behavior, desktop
screen, installer, OS interaction, or packaged UI behavior. Browser and Computer Use checks are
therefore not required for Phase 3 unless code changes drift into UI/runtime behavior.
