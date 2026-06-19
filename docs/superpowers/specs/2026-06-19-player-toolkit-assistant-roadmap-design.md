# Player Toolkit And Assistant Roadmap Design

Date: 2026-06-19

## Status

Approved direction from brainstorming, then hardened through consultant and adversarial review. This is the roadmap contract for the next large development cycle.

This design starts from `C:\Users\Conferences and AI\Downloads\matchup_analysis_11e_design.md`, the existing Python-first Warhammer Tournament Companion codebase, and subagent review passes covering architecture fit, source/IP/security guardrails, and adversarial roadmap critique.

## Product Goal

Evolve Warhammer Tournament Companion from a line-of-sight and layout analysis MVP into a practical player toolkit, then into an AI-assisted companion.

The toolkit comes first. The app should provide deterministic tools that a player or team captain can trust:

- Line-of-sight and hidden coverage checks.
- Safe deployment and exposure checks.
- Model-base-aware movement reach checks.
- Melee and shooting threat range checks.
- Roster-aware damage and survivability profiles.
- Mission/action feasibility checks.
- Team-pairing scenario comparison that supports captain decisions without pretending to be calibrated until a pairing model is validated.

The AI companion should be a later explanation and orchestration layer over those deterministic tools. It must not be the primary rules interpreter or the first source of tactical truth.

## Current System Fit

The current repo already has the correct foundation:

- `warhammer_companion.domain` owns `MapPacket`, board, terrain, dense/light features, and deployment zones.
- `warhammer_companion.los.geometry` owns Shapely-based LOS, deployment-edge heatmaps, hidden coverage, and base-aware visibility checks.
- `warhammer_companion.ingestion` owns official source URLs, local PDF ingestion, source manifests, packet building, and validation reports.
- `warhammer_companion.application.services` is the right boundary for new toolkit service methods.
- `warhammer_companion.rendering.svg` can support early overlays for movement, threat, deployment, and mission regions.
- The web MVP and PySide desktop migration both depend on the Python engine, which should remain the durable product core.

The roadmap should extend this package structure. Do not introduce a second backend tree such as `backend/fortyk_los_backend`, and do not rewrite the UI in React as part of this roadmap.

## External Source Findings

The app should reduce manual maintenance of minute points, profile, and roster data where possible, but not by treating third-party/community data as authoritative without provenance.

Observed source landscape:

- Official Games Workshop sources remain the terminology and mechanics anchor. Current public source set includes the free core rules PDF, Event Companion PDFs, and app/MFM update cadence from Warhammer Community.
- The architecture must not hard-code an edition label such as `11e` into module names, schemas, or test fixtures. It should store source-derived `ruleset_id`, `edition_id`, `season_id`, `source_version`, and `effective_date` fields. User-facing shorthand can say "current rules" only when the active `RulesPack` proves the underlying source set.
- The online Munitorum Field Manual is the primary source candidate for points. It is live as `v1.0`; the Warhammer downloads page marks it updated 17/6/2026; the app/MFM article says it contains unit and upgrade points, leader/support join data, Detachment Points, and Force Dispositions.
- New Recruit is a candidate roster-builder/export ecosystem. Its public site states it supports Warhammer 40k, BattleScribe roster compatibility, and list validation using BSData community datasets from GitHub.
- BSData is a community-maintained datafile ecosystem for list-building software. Its homepage says it is maintained by volunteers and currently developed for compatibility with New Recruit. The checked `BSData/wh40k-10e` repository contains BattleScribe-style catalogue files and presents itself as community-maintained, not publisher-endorsed. Because this checked repository is explicitly 10e while official new-edition sources are live, imported BSData/New Recruit packs must pass edition/freshness compatibility gates before profile resolution can use them.
- BattleScribe-style data uses `.gst`/`.gstz` game-system files, `.cat`/`.catz` catalogue files, index files, and `.bsr` repository distributions. A `.ros`/`.rosz` roster can identify selections, but roster parsing must remain separate from profile and mechanic authority.
- No reliable current public source was confirmed for a distinct "YellowScribe" integration during this pass. Treat it as a named candidate to investigate further if a concrete URL/package/export format is supplied. Do not block the roadmap on it.

Roadmap implication:

- Build adapters for `.ros`, `.rosz`, New Recruit/BattleScribe-style exports, BSData-derived local profile packs, and an `OfficialMfmAdapter -> PointsPack`.
- Do not bundle community data as official truth.
- Let users import or refresh local data packs, then hash, validate, version, and review them.
- Prefer adapter-backed profile resolution over hand-maintaining every point value and profile inside this repo. Official MFM points are authoritative when successfully imported; roster/community points are snapshots or cross-checks and must warn on divergence.
- Keep official mechanics, terminology, and mission/action rules source-anchored separately from community roster/profile catalogs.

Reference URLs checked during this pass:

- Core rules article: `https://www.warhammer-community.com/en-gb/articles/nhqt9wx3/new40k-rules-download-the-free-core-rules-now/`
- Core rules PDF: `https://assets.warhammer-community.com/eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf`
- Event Companions article: `https://www.warhammer-community.com/en-gb/articles/lszdpzmc/new40k-download-the-new-event-companions-today/`
- App/MFM article: `https://www.warhammer-community.com/en-gb/articles/dv1aslrr/new40k-new-app-for-a-new-edition/`
- Munitorum Field Manual: `https://mfm.warhammer-community.com/`
- Warhammer 40,000 downloads page: `https://www.warhammer-community.com/en-gb/downloads/warhammer-40000/`
- New Recruit: `https://www.newrecruit.eu/`
- BSData homepage: `https://www.bsdata.net/`
- BSData 40k data repository checked as a community-data example: `https://github.com/BSData/wh40k-10e`
- BSData catalogue data-structure wiki: `https://github.com/BSData/catalogue-development/wiki/Data-structure-overview`

## Source Trust Contract

Every source-derived artifact must carry provenance and readiness. This is mandatory for official PDFs, public Google Sheets, community roster data, profile packs, points packs, mission packs, and user uploads.

Required source reference kinds:

- `remote_http`: URL, publisher/domain, retrieval timestamp, HTTP status, content type, byte size, redirect target, ETag, Last-Modified, SHA-256, parser version, schema version, extraction version.
- `local_file`: filename, local ignored-cache path, import timestamp, byte size, SHA-256, parser version, schema version, local-storage policy.
- `manual_entry`: operator id or local user marker, entry timestamp, reason, reviewed fields, and override history.
- `derived_artifact`: parent source refs, derivation step, algorithm/parser version, source hash, artifact hash, reviewer state.
- `community_pack`: package URL or local source path, game system id, edition/ruleset marker, package commit/tag/version, retrieval/import timestamp, package hash, compatibility status against the active official rules/MFM packs.

Required canonical data fields:

- Per-field `source_refs`, not only pack-level provenance.
- Anchors where applicable: PDF page and section, sheet id/gid/range, row id, card id, image id/hash, bounding box for image-derived facts.
- Validation state, confidence, warnings, reviewer state, compatibility state, freshness state, and override history.

Do not store or redistribute:

- Official PDFs, mission-card images, full card text, datasheet text, or long copied rules passages in any distributed artifact.
- Community spreadsheet exports or BSData-derived data as bundled application data unless redistribution is explicitly reviewed.
- Generated packs that reconstruct protected rules/card/datasheet text.
- User rosters outside local user-controlled storage by default.
- Protected or community-derived raw data inside the repository, wheel/package, installer, docs artifact, sample/test fixture, export bundle, generated pack, or app bundle unless redistribution rights are explicitly reviewed. Allowed distributed metadata is limited to source anchors, hashes, IDs, short labels, and schemas.

Fail closed when:

- Redirects leave an allowlist.
- Content type, size, page count, hash, or schema validation fails.
- A public sheet/image contains formulas, HTML/script content, or malformed data.
- Required source anchors are missing or contradictory.
- Archive imports exceed size, decompression ratio, or member-count limits; contain path traversal, absolute paths, nested archives, encrypted members, or unexpected file types.
- XML imports require external entities, DTD expansion, entity expansion, remote includes, or network access from parsed content.
- Public sheet imports are not values-only, or image imports exceed dimension/format limits.
- Pasted roster text contains markup/script content or cannot be canonicalized without preserving executable content.

Importer quarantine:

- All public sheets, images, `.rosz/.catz/.gstz` archives, `.ros/.cat/.gst` XML files, pasted rosters, and community packs are quarantined before canonicalization.
- Canonicalization must use safe parsers, no network fetches from parsed content, strict schema validation, and explicit `blocked` readiness on failure.

Freshness gate:

- Mutable sources must carry retrieval time plus ETag, Last-Modified, upstream version, or latest-known version when available.
- Unknown freshness cannot be `trusted`.
- Stale legality, points, mission, or pack-compatibility data must block tactical recommendations. If stale data affects only a non-critical display field, the output may be `degraded` instead.

## Readiness States

All significant outputs must report one of:

- `trusted`: all required source fields, freshness checks, pack versions, geometry assumptions, compatibility checks, and validation records are present. The tool may use words such as legal, safe, recommended, or likely only when the underlying result supports them.
- `estimated`: output is useful but relies on approximated 2D movement, inferred terrain semantics, community data, or manual assumptions. The tool may show exploratory overlays, ranges, and diagnostics only, with an assumption banner. It must not call a move legal or a plan safe.
- `degraded`: output has unresolved warnings that materially affect interpretation. The tool may show diagnostics and missing-data guidance, but no recommendations.
- `blocked`: required data is missing, stale, unsafe, incompatible, or contradictory. The tool must produce no tactical output beyond the block reason and remediation steps.

False precision is a product bug. Avoid exact-looking scores, legal claims, and optimal plans unless the input state supports them.

Tests must enforce allowed wording and behavior by readiness. In particular, `estimated`, `degraded`, and `blocked` outputs must not leak recommendation language through the UI, exported reports, or AI companion summaries.

## Shared Toolkit Result Contract

Before adding new movement, threat, deployment, damage, or mission tools, define a shared result shape:

```text
ToolkitResult[T]
  result_id
  tool_id
  input_hash
  readiness
  payload: T
  assumptions
  warnings
  block_reasons
  source_refs
  validation_records
  export_metadata
```

Map-facing tools should return deterministic overlay primitives before rendering:

```text
MapOverlayLayer
  layer_id
  layer_kind
  geometry
  units
  style_token
  label
  readiness
  source_refs
```

The current service layer can continue returning rendered SVG to web/desktop screens, but toolkit services should first produce `ToolkitResult` and `MapOverlayLayer` data. Rendering then becomes a projection, not the durable analysis result.

## Roadmap Overview

### Phase 1 - Source, Ruleset, And Rules Foundation

Goal: make current Warhammer 40,000 mechanics source-backed before solvers depend on them, without hard-coding edition labels into architecture.

Add:

- `RulesPack`: source-anchored mechanics, glossary, terminology mappings, `ruleset_id`, `edition_id`, `season_id`, source versions, effective dates, and old-terminology blacklist.
- `SourcePackRegistry`: local pack discovery, hashes, versions, timestamps, compatibility state, and stale-data warnings.
- `MissionPack` skeleton: mission/card/action/objective source refs without full recommendation logic.
- `OfficialMfmAdapter -> PointsPack`: primary points path when the official MFM can be fetched and validated.
- `ProfilePack` skeleton: adapters can populate it from user-supplied/community data, but it is not treated as official rules truth.
- `BaseSizePack`: model base/frame data needed by movement, threat, and deployment tools.

Key rule concepts to model first:

- Terrain Area, Terrain Feature, Terrain Category, and source-backed visibility traits.
- Candidate/source-pending terminology for Benefit of Cover, Hidden, Obscuring, Solid, and similar terms until each active `RulesPack` field has a source ref.
- Model bases, measuring, engagement, coherency, and movement types.
- Attack sequence and common weapon/core abilities.
- Objective control, terrain objectives, actions, reserves, transports, and disembark modes.

Acceptance:

- Packs include source refs and hashes.
- Old assumptions are blocked by tests: cover as default +1 save, 1-inch-only engagement, all reserves as Deep Strike, objectives as only markers, visibility as only boolean.
- Solvers can request rule concepts without hard-coded user-facing labels.
- The active pack proves `edition_id` and `ruleset_id`; otherwise user-facing labels must say "source pending" or "current source candidate" and tactical outputs are not `trusted`.
- Official MFM points override roster/community point snapshots when both are available and compatible; divergences are warnings or blocks depending on impact.

### Phase 2 - Shared Toolkit Result And Canonical Board State

Goal: give every tool the same result contract and game-state model.

Add:

- `ToolkitResult[T]` and `MapOverlayLayer`.
- `BoardState`.

`BoardState` includes:

- Selected `MapPacket`.
- Round, turn, phase, active player, and going-first/going-second assumption.
- Units, models, base sizes, current positions, and footprints.
- Friendly/enemy status.
- Move history, battle-shock state, objective control, action state, reserves, transports, embarked units, CP and stratagem toggles.
- Per-field source refs and readiness warnings.

Do not store mechanics inside `MapPacket`. `MapPacket` remains layout geometry; `BoardState` binds layout, rules, mission, and army state.

Acceptance:

- Existing LOS/heatmap tools can be wrapped by board state without changing their geometry semantics.
- Missing model positions or base sizes produce `estimated` or `blocked` outputs, not silent defaults.
- New toolkit services produce `ToolkitResult` before rendering SVG or desktop widgets.
- Overlay fixtures prove the same analysis payload can render in web and desktop without recomputing tactical semantics.

### Phase 3 - Base Size And Terrain Semantics

Goal: unlock manual deterministic movement, threat, and exposure tools before roster/profile import is complete.

Add:

- Base-size and model-frame records with source refs and manual fallback.
- Terrain area/feature/category/visibility-trait adapter over `MapPacket`.
- Manual unit footprint inputs for early tools.
- Degrade/block triggers for unknown base, unknown terrain trait, vertical/height assumptions, and incompatible source pack versions.

Acceptance:

- A player can run manual-base movement/threat/exposure checks without roster import.
- Unknown base or terrain semantics cannot produce `trusted` legal/safe claims.
- Base and terrain data can later be enriched by roster/profile adapters without changing movement/threat APIs.

### Phase 4 - Roster And Profile Adapter Layer

Goal: streamline army data without hand-maintaining every point/profile in the app.

Inputs:

- `.rosz` upload.
- `.ros` upload.
- New Recruit/BattleScribe-compatible export where available.
- Pasted roster text as a fallback.
- Manual correction UI for unresolved entries.

Pipeline:

```text
Roster Source
  -> RosterImportRecord
  -> CanonicalArmy
  -> RosterSnapshotProfilePack / ProfileCandidate
  -> ProfileResolution
  -> ProfilePack / PointsPack / BaseSizePack refs
  -> BoardState-ready army
```

Important separation:

- Roster import identifies selected units, wargear, enhancements, detachments, transports, reserves, and points as-presented.
- `.ros/.rosz` import preserves embedded selected profiles, rules, and characteristics as local `RosterSnapshotProfilePack` or `ProfileCandidate` data with raw XML hash/source path and no redistribution.
- Profile resolution maps those selections to source/versioned profiles.
- Rules mechanics come from `RulesPack`, not roster text.
- Official MFM-derived points are authoritative when compatible. Roster/community points are imported snapshots or cross-checks and must warn or block on divergence.
- Community catalogs can be used as profile candidates, but must be versioned, hashed, validated, and explicitly labeled community-derived unless an official local source backs them.
- Imported packs must carry `edition`, `game_system_id`, data package URL or local path, commit/tag/version, retrieval/import timestamp, and compatibility state versus active official rules and MFM packs.

Acceptance:

- No roster entry is silently discarded.
- `.ros/.rosz` parsing preserves raw ids, names, selections, costs, and source paths.
- Embedded roster profiles/rules/characteristics are preserved as local evidence, not source authority.
- Profile statuses include `resolved_exact`, `resolved_alias`, `resolved_manual`, `ambiguous`, `unresolved`, and `unsupported`.
- The UI shows unresolved profile/base/points data before downstream analysis runs.
- Edition/ruleset mismatches between roster/community packs and active official packs produce `blocked` for legality/points-sensitive analysis, or `degraded` for non-critical display.

### Phase 5 - Movement Reach Toolkit

Goal: add the first new deterministic player tool beyond LOS.

Scope:

- Base-aware 2D movement reach.
- Dense/solid-feature collision checks.
- Board-edge constraints.
- Friendly/enemy model collision assumptions.
- Coherency checks for simple unit formations.
- Move type support for initial Normal Move, Advance, Charge, Scout, Ingress, and Disembark estimates.
- Terrain and vertical assumptions surfaced as warnings.
- Separate "geometrically reachable estimate" from "rules-legal endpoint."

Output:

- Reachable region overlay.
- Blocked/illegal endpoint reasons.
- Objective/action reach markers.
- Exposure and hidden/covered endpoint summary.
- Readiness state.

Acceptance:

- Tool reuses existing Shapely geometry and SVG overlay patterns.
- It clearly distinguishes "estimated 2D reach" from exact 3D legality.
- It can be invoked from `WarhammerCompanionService` before desktop/web rendering choices diverge.
- Endpoint legality is `trusted` only when source-backed movement, base, terrain, coherency, vertical, reserve, charge, and disembark mechanics required by that query are present.
- Manual/minimal `BoardState` inputs are supported before roster/profile import.

### Phase 6 - Threat Range Toolkit

Goal: show areas held at risk by melee, shooting, reserves, transports, and actions.

Threat modes:

- Raw weapon range.
- Movement plus range.
- Advance/charge distribution.
- Charge probability with modifiers and rerolls.
- Board-eligible visibility/LOS reach.
- Transport disembark threat.
- Ingress and Deep Strike-modified Ingress threat.
- Objective flip and action denial reach.

Output should be probability/distribution based, not max-range-only. Max range can be shown, but recommendations must account for modeled dice, rerolls, modifiers, CP/stratagem availability, and readiness warnings.

Acceptance:

- Threat overlays can be calculated without a full damage engine.
- Unsupported modifiers are visible and default to disabled.
- Threat tools can run in rosterless mode with manually entered movement/base/range, then become roster-aware when profiles resolve.
- Each threat distribution lists exactly which dice, reroll, modifier, CP, and stratagem rules are modeled. Unsupported modifiers must be absent from calculations and cannot appear in recommendations.

### Phase 7 - Early Safe Exposure And Deployment MVP

Goal: add deterministic safe-area and exposure tooling before full mission-aware deployment optimization.

Build:

- Exposure overlays from known or manual unit footprints.
- Safe staging regions by selected enemy threat/LOS assumptions.
- Deployment-zone safe-area checks using current map geometry.
- Manual unit placement diagnostics.

Acceptance:

- The tool can run after movement/threat tools with manual base and range inputs.
- It must not claim a full legal deployment plan unless roster, base sizes, coherency, terrain semantics, and active mission/deployment constraints are source-backed.
- Outputs are component diagnostics and overlays, not optimized deployment candidates.

### Phase 8 - Damage And Survivability Profiles

Goal: calculate roster-aware attrition metrics after source/profile resolution exists.

Start with:

- Core hit/wound/save/damage expected value.
- Monte Carlo distribution where needed.
- Common weapon/core abilities from the supported mechanics list.
- Cover/visibility state integration only when source-backed.

Views:

- Unit-vs-unit damage matrix.
- Survivability profile by opposing threat.
- Target priority and bad-target warnings.
- Fragile mission-critical unit warnings.

Acceptance:

- Benefit of Cover is applied according to the current source-backed rules model, not legacy assumptions.
- Unsupported faction/detachment/stratagem effects are explicit.
- Results include source refs, assumptions, and readiness state.

### Phase 9 - Mission Pack And Game Analytics Primitives

Goal: model the scoring environment before captain-level matchup analytics.

Add:

- Mission, primary, secondary/action, terrain objective, deployment map, and timing records.
- Action eligibility and disruption checks.
- Objective control and contest calculations.
- Durable OC, hidden action capacity, reserve action reach, objective flip potential, and denial potential.

Inputs can include the public Google Sheet with mission card images/data as candidate data, but it must be treated as untrusted/public input until validated and reviewed. The app should store anchors and derived mechanics, not protected card images or full card text.

Acceptance:

- Each mission/action mechanic has source refs and card-level validation.
- Community or image-derived mission data is `estimated` or `degraded` until reviewed.
- Analytics primitives expose components rather than one opaque score.

### Phase 10 - Mission-Aware Deployment Toolkit

Goal: help players evaluate deployment safety and staging without pretending to solve the whole game.

Build:

- Safe deployment area overlays.
- Exposure-minimizing candidate regions.
- Objective/action reach from deployment.
- Screening gaps against Ingress/Deep Strike-modified Ingress.
- Transport staging lanes.
- Manual deployment edit and rescore.

Defer:

- Full mixed-integer optimization.
- Perfect legal placement for complex 3D terrain.
- Opponent-intent prediction.

Acceptance:

- Candidate outputs explain tradeoffs and warnings.
- Tool can run with manual unit footprints before full roster placement exists.
- Going-first/going-second assumptions are explicit.

### Phase 11 - Matchup Analytics For Team Pairing

Goal: support team tournament captains comparing pairing scenarios.

This phase must come after toolkit primitives. The analytics engine should aggregate deterministic tool outputs:

- Damage/survivability asymmetry.
- Mission scoring capacity.
- Objective and action reliability.
- Deployment safety and staging quality.
- Threat projection pressure.
- Mobility and screening gaps.
- Unsupported-data penalties.

Output:

- Pairing matrix with component scorecards and scenario ranges.
- Component breakdown, not one opaque number.
- Scenario assumptions: mission pack, terrain layout, player skill assumptions, going-first/second, list archetype tags.
- Sensitivity analysis for captain-reviewed decisions.

Do not start with game-theoretic captain automation. Do not claim calibrated expected tournament points until a `PairingModelSpec` defines priors, weights, historical or coach-entered calibration data, sample sizes, validation error, and uncertainty propagation.

Acceptance:

- Pairing estimates are blocked or degraded when required tools are missing.
- Captain-facing output shows why a pairing scenario appears favorable or risky under stated assumptions.
- The app can export the assumptions and component metrics used for each estimate.
- Confidence bands, recommended pairings, and expected tournament-point optimization are unavailable until the pairing model is calibrated and validated.

### Phase 12 - AI Companion

Goal: turn deterministic tools and analytics into a useful assistant.

The AI companion may:

- Ask which toolkit check the user wants.
- Call deterministic tools.
- Summarize results in tactical language.
- Cite source anchors and pack versions.
- Explain assumptions and missing data.
- Generate checklists for deployment, threat avoidance, and mission scoring.
- Help a captain compare pairings once analytics are available.

The AI companion must not:

- Interpret raw rules text live as authoritative.
- Invent unsupported faction/detachment interactions.
- Hide warnings or readiness states.
- Export user rosters or private tournament data to external services without per-session or per-request opt-in.
- Replace deterministic tool output with prose-only advice.

Privacy defaults:

- Local/offline analysis is the default.
- External AI calls require data preview, least-necessary-field transfer, anonymization where possible, and a clear provider retention/training note.
- Private roster, matchup, tournament, prompt, cache, log, and error-report data must not leave local storage unless the user opts in for that request/session.
- The companion must refuse external calls when consent or privacy guarantees are absent.

Acceptance:

- Tool calls are inspectable and reproducible.
- Responses include pack/source/version context.
- Unsupported claims are refused or redirected to manual review.

## UI Direction

The app should remain a work-focused toolkit, not a marketing experience.

Near-term web/desktop navigation should evolve from current pages toward:

- Sources & Packs.
- Map Viewer.
- LOS / Hidden Coverage.
- Movement Reach.
- Threat Range.
- Roster Import.
- Profile Resolution.
- Damage & Survivability.
- Mission Analytics.
- Deployment Safety.
- Team Pairing.
- Assistant.

Each screen should expose readiness state, assumptions, warnings, and export options. For dense operational tools, prefer compact forms, overlays, tables, and comparison panels over decorative cards.

## Phase Gate Matrix

| Phase | Required inputs | Allowed outputs | Block/degrade triggers | Minimum tests |
| --- | --- | --- | --- | --- |
| Source/rules foundation | Official source refs, source hashes, ruleset metadata, MFM freshness metadata | Pack registry, glossary candidates, source anchors | Missing hash, stale mutable source, unproved edition, old terminology | Source hash, freshness, terminology blacklist |
| Shared result and board state | `ToolkitResult`, `MapOverlayLayer`, minimal `BoardState` | Shared payloads and overlay fixtures | Missing readiness, missing assumptions, screen-only SVG result | Schema, rendering projection, export metadata |
| Base/terrain semantics | `MapPacket`, base data or manual base, terrain trait refs | Manual geometry diagnostics and exploratory overlays | Unknown base/terrain trait for legal/safe claims | Base fallback, terrain unknown, readiness wording |
| Roster/profile adapters | Quarantined roster/archive/XML, source refs, active rules/MFM packs | Canonical army, profile candidates, resolution statuses | Unsafe import, edition mismatch, MFM divergence | `.ros/.rosz` fixtures, archive/XML safety, profile ambiguity |
| Movement reach | Board state, base/terrain semantics, selected move mode | Geometric reach; legal endpoints only when trusted | Missing movement/coherency/terrain/vertical rule for legal claim | Reach geometry, block reasons, readiness language |
| Threat range | Movement/range inputs, modeled dice/reroll/modifier list | Threat overlays and probability distributions | Unsupported modifier in calculation, stale profiles, missing dice rule | Probability fixtures, unsupported-modifier exclusion |
| Early safe exposure | LOS/threat assumptions, manual or resolved footprints | Exposure and safe-staging diagnostics | Missing footprint/threat assumptions for safe claim | Exposure overlays, no recommendation under estimated |
| Damage/survivability | Resolved profiles, supported ability list, visibility state | Damage matrix and survivability diagnostics | Unsupported ability affects result, stale profiles/points | Core math, ability support, unsupported warnings |
| Mission primitives | Reviewed mission/action/objective mechanics | Objective/action feasibility components | Unreviewed card/image-derived mechanic | Mission/action fixtures, objective geometry |
| Deployment toolkit | Mission/deployment constraints, unit footprints, threat state | Candidate diagnostics and manual rescore | Missing mission/base/coherency for legal plan | Candidate explanations, block/degrade triggers |
| Team pairing | Deterministic component outputs, scenario assumptions | Scenario scorecards and ranges | Missing components, uncalibrated pairing model for expected-points claims | Aggregation, sensitivity, no confidence bands until calibrated |
| AI companion | Tool registry, privacy decision, source/readiness context | Tool orchestration and cited summaries | Missing consent, unsupported claim, hidden readiness warning | Tool-call traces, refusal/privacy tests |

## Testing And Verification Strategy

Each phase must add tests that match its trust level.

Baseline checks:

- `ruff format --check src tests`
- `ruff check src tests`
- `mypy src`
- `pytest`

New test families:

- Source-pack hash and stale-data tests.
- Source-anchor and no-redistribution tests.
- Terminology regression tests.
- Roster parser fixtures for `.ros`, `.rosz`, New Recruit/BattleScribe-compatible exports, and pasted text.
- Profile resolution ambiguity tests.
- Movement reach geometry tests.
- Threat probability tests.
- Damage math tests.
- Mission/action eligibility tests.
- Team pairing aggregation tests with sensitivity checks.
- AI companion tool-call and refusal tests.
- Readiness wording tests that prevent non-`trusted` outputs from saying legal, safe, recommended, likely, optimal, or expected points unless the specific result contract permits it.
- Malicious import fixtures for archives, XML, public sheets, images, pasted rosters, and community packs.
- Distributed-artifact scans that fail if raw official/community protected data or near-verbatim rules/card/profile text is bundled.

Browser/desktop QA should keep using page 9/page 52 map packets as smoke tests for complex terrain overlays.

## Subagent Review Findings Integrated

Consultant architecture review:

- Extend the existing Python package and service layer.
- Reuse `MapPacket`, LOS geometry, source manifests, packet builder validation, and SVG rendering.
- Add `RulesPack` and `BoardState` before advanced solvers.
- Avoid a second backend architecture or frontend rewrite.

Source/security review:

- Treat official PDFs, public sheets, community catalogs, and user rosters as separate trust domains.
- Store source refs, hashes, parser versions, validation records, and readiness states.
- Do not redistribute raw or near-verbatim protected rules/card/profile data.
- Fail closed on malformed, oversized, unauthenticated, or contradictory inputs.

Adversarial review:

- The original feature list was directionally right but too wishlist-like.
- Source packs and board state are hard prerequisites.
- Movement-first is tempting but risks false precision unless readiness states and base/terrain semantics exist.
- Roster import must be separate from profile resolution.
- AI must be last and must explain deterministic outputs.

## Open Decisions For Implementation Planning

1. Which concrete `.ros/.rosz` parser library or in-house parser should be used first?
2. Which New Recruit export formats are stable enough to support without account/API dependence?
3. Whether BSData-derived local profile packs are acceptable for internal user-side import, and what license/IP review is needed before any public distribution support.
4. How users will refresh local community-derived packs and compare them to official source/version dates.
5. Which minimum profile fields unlock movement/threat tools before full damage profiles exist.
6. Which mission pack source should be treated as the first reviewed fixture.
7. What calibration data and `PairingModelSpec` would be required before confidence bands, expected points, or recommended pairings are allowed.
8. Which AI runtime/tool-calling boundary is acceptable for private roster and tournament data.

## Immediate Next Specs

Write fine-grain implementation specs in this order:

1. `source-pack-registry-and-rulespack-current-spec.md`
2. `toolkit-result-and-board-state-spec.md`
3. `base-size-and-terrain-semantics-spec.md`
4. `roster-import-and-profile-adapter-spec.md`
5. `movement-reach-toolkit-spec.md`
6. `threat-range-toolkit-spec.md`
7. `early-safe-exposure-toolkit-spec.md`
8. `damage-survivability-profile-spec.md`
9. `mission-pack-and-actions-spec.md`
10. `mission-aware-deployment-toolkit-spec.md`
11. `team-pairing-scenario-analytics-spec.md`
12. `ai-companion-tool-orchestration-spec.md`

Implementation should not begin until the first fine-grain spec is reviewed and approved.
