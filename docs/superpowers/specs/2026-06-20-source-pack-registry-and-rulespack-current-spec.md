# Source Pack Registry And Current RulesPack Spec

Date: 2026-06-20

## Status

Draft Phase 1 fine-grain implementation spec for the first developmental slice after Phase 0.5.

Parent roadmap: `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`

## Goal

Add the first source/rules foundation that downstream deterministic tools can query before they
make legality, safety, or recommendation claims.

This slice creates typed source-pack and rules-pack metadata. It records current source candidates,
freshness markers, readiness state, compatibility state, and terminology blockers without bundling
official PDFs, public-sheet data, community packs, roster data, or copied rules text.

## Current Source Facts Checked

Freshness check date: 2026-06-20.

- Warhammer Community downloads page lists the Munitorum Field Manual for Warhammer 40,000 and
  marks it updated `17/6/2026`.
- The Munitorum Field Manual page reports `v1.0`.
- The active core rules PDF candidate remains
  `https://assets.warhammer-community.com/eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf`.
- New Recruit publicly describes Warhammer 40k support and BattleScribe roster compatibility.
- New Recruit states that its tournament/list validation uses BattleScribe data sets maintained by
  BSData communities and downloaded from GitHub.
- BSData presents itself as a community-maintained GitHub-hosted project.

These facts are metadata only. They do not make any mechanics `trusted` until hashes, field-level
source refs, and reviewed mechanics are present.

## Scope

Add:

- `SourceRef`, `SourcePackEntry`, `SourcePackRegistry`, and related readiness/freshness/
  compatibility values.
- `RulesConcept` and `RulesPack` metadata for current-source candidate mechanics.
- A builder for the current Warhammer 40,000 source/rules foundation.
- A fetch-and-hash verifier for remote HTTP source refs, injectable for tests and not invoked by
  the default builder.
- Unit tests proving source metadata, freshness, readiness, no-protected-text guardrails, and legacy
  assumption blockers.

## Non-Goals

This slice must not:

- Download or store official PDFs.
- Store copied rules paragraphs, mission card text, datasheet text, roster text, faction-pack text,
  or community catalog content.
- Parse MFM points, New Recruit exports, `.ros/.rosz`, BSData, mission cards, or Google Sheet data.
- Add web/desktop UI.
- Claim that any rules concept is `trusted`.
- Implement movement, threat, damage, mission, roster, profile, or AI tools.

## Architecture

Add the source/rules foundation under `src/warhammer_companion/ingestion/` because `AGENTS.md`
places official-source registries, ingestion artifacts, and source handling there.

The first implementation should be pure, deterministic, and side-effect free:

```text
build_current_rules_foundation()
  -> SourceRulesFoundation
       registry: SourcePackRegistry
       rules_pack: RulesPack
```

No network access occurs at runtime in this builder. Current external facts are represented as
explicit metadata from this reviewed spec and can later be refreshed by a dedicated adapter.

A separate `verify_remote_http_source()` function may fetch bytes when explicitly called by future
refresh workflows. It must validate HTTPS scheme and approved source hosts before network access,
validate redirected final URLs, stream content, compute SHA-256, record content type, byte size,
final URL, and fail closed on non-200 responses, unsafe source kinds, empty content, or missing
content type. Tests must use injected fake responses, not live network calls.

Mutable source freshness must not default to `current` unless the builder receives a refresh
timestamp. Without a refresh timestamp, mutable source entries must report `unknown` freshness even
when an upstream version/update label is known.

## Data Model Requirements

`SourceRef` must include:

- `source_id`
- `kind`
- `label`
- `url`
- `publisher`
- optional `retrieved_at`
- optional `upstream_version`
- optional `upstream_updated`
- optional `sha256`
- optional `content_type`
- optional `byte_size`
- optional `anchors`

`SourcePackEntry` must include:

- `pack_id`
- `label`
- `role`
- `source_ref_ids`
- `readiness`
- `freshness`
- `compatibility`
- `mutable`
- `warnings`

`RulesPack` must include:

- `ruleset_id`
- `edition_id`
- `season_id`
- `source_version`
- `effective_date`
- `readiness`
- `source_ref_ids`
- `concepts`
- `terminology_blacklist`
- `warnings`

## Initial Concept IDs

The initial `RulesPack` should expose source-pending concept IDs only:

- `terrain_area`
- `terrain_feature`
- `terrain_category`
- `visibility_trait`
- `benefit_of_cover`
- `hidden`
- `obscuring`
- `solid`
- `model_base`
- `measuring`
- `engagement`
- `coherency`
- `normal_move`
- `advance`
- `charge`
- `attack_sequence`
- `objective_control`
- `actions`
- `reserves`
- `transports`
- `disembark`

Do not add mechanics text or exact rule effects in this slice.

## Legacy Assumption Blockers

The initial `RulesPack` must block these assumption keys:

- `cover_as_default_plus_one_save`
- `engagement_range_one_inch_only`
- `reserves_are_deep_strike`
- `objectives_are_markers_only`
- `visibility_boolean_only`

Downstream solvers can use these keys in tests before implementing exact mechanics.

## Acceptance Criteria

- Unit tests cover registry lookup, mutable-source freshness, missing-hash readiness, current MFM
  version/date metadata, timestamp-gated freshness, source-pending concepts, remote fetch/hash
  verification, non-200 blocking, unsafe URL rejection, redirect blocking, incomplete metadata
  blocking, and legacy assumption blockers.
- Tests prove no initial rules concept is `trusted`.
- Tests prove no protected source text is stored in the initial pack.
- No raw official PDFs, generated packs, community data, roster data, or source-derived rules text
  are committed.
- Existing validation commands pass.
- Consultant and adversarial reviewers approve the source/rules foundation before the checkpoint is
  committed.
