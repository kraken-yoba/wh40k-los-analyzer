# Matchup Roadmap Foundation Design

Date: 2026-06-19

## Goal

Start the matchup-analysis roadmap with a source-backed foundation that can safely support roster import, mission analysis, damage math, movement reach, deployment candidates, and codex findings later.

The first implementation slice is intentionally narrow: define the source trust contract and a canonical 11e RulesPack skeleton. It must not implement matchup simulation, roster parsing, or profile resolution yet.

## Context

The current app is a Python-first Warhammer 40,000 tournament companion. Its useful surface today is table analysis: official layout ingestion, terrain feature extraction, map packets, LOS heatmaps, LOS checker, hidden coverage, web UI, desktop UI, and Windows packaging.

The GPT-Pro roadmap expands that table foundation into roster-aware matchup analysis. The expansion is too large for one implementation plan, so this spec decomposes it into phases and makes Phase 0 and Phase 1 the first buildable unit.

LazyCodex/OMO status in this session:

- `git_bash` is available and is the shell surface used for repo inspection.
- The OMO `omo sparkshell` command is not on PATH.
- LSP status is available, but no Python language server is active, so document-symbol CodeGraph lookup is unavailable.
- Implementation should therefore rely on normal repo inspection, tests, and type checks until a richer LazyCodex CodeGraph surface is available.

## Source Trust Model

### Official Core Rules PDF

The official Core Rules PDF is authoritative for terminology, rule anchors, and mechanics used by the app. The local cache and manifest already record the official URL, local filename, page count, and hash.

RulesPack data may store:

- source document id
- local filename
- source URL
- SHA-256 hash
- page count
- section ids and page anchors
- short internal concept mappings

RulesPack data must not store long copied rules text.

### Official Event Companion And Terrain PDFs

The existing official terrain and event companion PDFs remain authoritative for map/layout extraction. Their current use through `MapPacket`, `OfficialLayoutMetadata`, terrain areas, dense features, and deployment zones should not be replaced by the matchup roadmap.

### Public Google Sheet

The public Google Sheet can be used as untrusted mission/card metadata input. Anything extracted from it must be normalized into a canonical MissionPack, schema-checked, source-hashed, and treated as data only.

The app must not execute sheet content, render raw HTML from sheet cells, or silently overwrite official/source-backed records with sheet-derived records.

### Wahapedia 10e

Wahapedia 10e is a provisional bootstrap source for unit/profile data only. It can help with datasheet names, unit profiles, weapon profiles, abilities, keywords, and stratagem identifiers because much profile vocabulary carried over into the new edition.

Any data derived from Wahapedia must be marked as provisional:

```text
source_kind = wahapedia_10e
authority = provisional_profile_bootstrap
edition_id = wh40k-10e
profile_resolution_confidence = provisional_10e_carryover
```

Wahapedia must not control 11e terminology, movement rules, terrain rules, visibility rules, action rules, mission rules, or source-anchor wording.

## Architecture

Add a new `rules` domain area under the existing package:

```text
src/warhammer_companion/rules/
  __init__.py
  sources.py
  models.py
  core_rules.py
```

Responsibilities:

- `sources.py`: source trust enums and source-reference models.
- `models.py`: canonical rules-pack models, concept mappings, glossary terms, validation records, readiness states.
- `core_rules.py`: builder for the bundled 11e core RulesPack skeleton from known official source metadata and source anchors.

Later phases should add sibling areas rather than overloading this one:

```text
src/warhammer_companion/missions/
src/warhammer_companion/profiles/
src/warhammer_companion/rosters/
src/warhammer_companion/matchups/
```

## Phase Roadmap

### Phase 0: Source Trust Contract

Define source kinds, authority levels, validation records, readiness states, and source refs. This phase gives later adapters one shared vocabulary for trusted, estimated, degraded, blocked, official, public, and provisional data.

Acceptance:

- Source references can represent official PDF anchors, public sheet rows, and provisional Wahapedia records.
- Untrusted/provisional sources are explicit in serialized data.
- Tests cover official, public untrusted, and provisional source examples.

### Phase 1: RulesPack And 11e Glossary

Define `CanonicalRulesPack` and build the first core-rules skeleton for key source anchors:

- core concepts
- datasheets
- movement
- engagement
- attack sequence
- terrain and visibility
- terrain objectives
- actions
- transports
- strategic reserves / ingress
- core and weapon abilities

Acceptance:

- A bundled `wh40k-11e-core-2026-06-01` RulesPack can be constructed without network access.
- The pack references the local official core-rules source metadata and hash.
- Concept mappings expose source-backed display labels for movement, visibility, objectives, reserves, and action eligibility.
- Old-assumption regression tests fail if the glossary maps Benefit of Cover as a save modifier, engagement as a 1-inch-only range, all reserves as Deep Strike, objectives as marker-only, or visibility as binary only.

### Phase 2: MissionPack Adapter

Normalize mission/disposition/card metadata into canonical mission records. The Google Sheet should feed this only through a sanitize-and-validate adapter.

Acceptance:

- Mission records include source refs, retrieval metadata, parser version, and validation state.
- Sheet-derived content cannot overwrite official layout metadata without explicit review state.

### Phase 3: Provisional ProfilePack

Use Wahapedia-derived 10e profile data as a bootstrap profile pack. Keep it visibly provisional.

Acceptance:

- Datasheet/profile records carry source and confidence.
- Profile resolution can distinguish official/future-reviewed data from provisional Wahapedia data.

### Phase 4: Roster Import

Parse `.rosz`, `.ros`, and pasted roster text into `CanonicalArmy`.

Acceptance:

- Two rosters can be normalized.
- Ambiguous or unresolved units are visible and actionable.
- Profile resolution does not silently discard roster entries.

### Phase 5: Damage And Survivability MVP

Add deterministic expected-value damage and survivability matrices using RulesPack mechanics and ProfilePack profiles.

Acceptance:

- Attack sequence follows the 11e pack.
- Visibility and Benefit of Cover integrate through RulesPack concepts.

### Phase 6: Movement, Mission, And Deployment

Reuse current map geometry, LOS, heatmap, and hidden coverage foundations for movement reach, objective/action reach, and deployment candidate scoring.

Acceptance:

- Outputs carry trusted/estimated/degraded/blocked readiness.
- Deployment candidates explain tradeoffs rather than emitting one opaque score.

### Phase 7: Codex Findings And Export

Save structured matchup findings and reproducible export bundles.

Acceptance:

- Findings include evidence, assumptions, source refs, confidence, and warnings.
- Accepted findings can be reviewed later without recomputing the matchup.

## UI Implications

The first implementation slice needs little UI. It should expose source/rules readiness in code and tests first. A later UI can add a Rules/Profile Resolution screen once roster import exists.

The existing web and desktop navigation should not gain a placeholder Matchup page until at least roster import or a useful rules/source status surface exists.

## Error Handling

RulesPack construction must be deterministic and offline. If source metadata is missing, the builder should return validation records or fail in tests rather than reaching the network.

Public and provisional sources must preserve warnings:

- untrusted public spreadsheet source
- provisional 10e profile source
- unsupported source kind
- stale or hash-mismatched official source

## Testing Strategy

Phase 0 and Phase 1 tests should live in:

```text
tests/test_rules_sources.py
tests/test_rules_pack.py
```

The tests should cover:

- source-reference serialization
- public/provisional source classification
- bundled core RulesPack id and source metadata
- source anchors for key 11e sections
- glossary/concept mappings
- old-terminology guardrails

## Out Of Scope For First Implementation Slice

- Roster parsing
- Wahapedia downloading/parsing
- Google Sheet ingestion
- Mission card OCR
- Damage math
- movement pathfinding
- deployment candidate generation
- Codex findings storage
- new navigation screens

## Sources

- Official Core Rules PDF: `https://assets.warhammer-community.com/eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf`
- Public Google Sheet: `https://docs.google.com/spreadsheets/d/1vlRuvuiy6YOOPLmYyLEUfcGVpGL56aWWMA4iWh18Yuw/edit?gid=1565185881#gid=1565185881`
- Wahapedia quick-start guide: `https://wahapedia.ru/wh40k10ed/the-rules/quick-start-guide/`
- Wahapedia data export: `https://wahapedia.ru/wh40k10ed/the-rules/data-export/`
