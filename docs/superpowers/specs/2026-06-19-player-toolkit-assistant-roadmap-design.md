# Player Toolkit And Assistant Roadmap Design

Date: 2026-06-19

## Status

Approved direction from brainstorming, written as the roadmap contract for the next large development cycle.

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
- Matchup analytics that support team-pairing decisions.

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
- New Recruit is a candidate roster-builder/export ecosystem. Its public site states it supports Warhammer 40k, BattleScribe roster compatibility, and list validation using BSData community datasets from GitHub.
- BSData is a community-maintained datafile ecosystem for list-building software. Its homepage says it is maintained by volunteers and currently developed for compatibility with New Recruit. The `BSData/wh40k-10e` repository contains BattleScribe-style catalogue files and presents itself as community-maintained, not publisher-endorsed.
- BattleScribe-style data uses `.gst`/`.gstz` game-system files, `.cat`/`.catz` catalogue files, index files, and `.bsr` repository distributions. A `.ros`/`.rosz` roster can identify selections, but roster parsing must remain separate from profile and mechanic authority.
- No reliable current public source was confirmed for a distinct "YellowScribe" integration during this pass. Treat it as a named candidate to investigate further if a concrete URL/package/export format is supplied. Do not block the roadmap on it.

Roadmap implication:

- Build adapters for `.ros`, `.rosz`, New Recruit/BattleScribe-style exports, and BSData-derived local profile packs.
- Do not bundle community data as official truth.
- Let users import or refresh local data packs, then hash, validate, version, and review them.
- Prefer adapter-backed profile resolution over hand-maintaining every point value and profile inside this repo.
- Keep official mechanics, terminology, and mission/action rules source-anchored separately from community roster/profile catalogs.

Reference URLs checked during this pass:

- Core rules article: `https://www.warhammer-community.com/en-gb/articles/nhqt9wx3/new40k-rules-download-the-free-core-rules-now/`
- Core rules PDF: `https://assets.warhammer-community.com/eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf`
- Event Companions article: `https://www.warhammer-community.com/en-gb/articles/lszdpzmc/new40k-download-the-new-event-companions-today/`
- App/MFM article: `https://www.warhammer-community.com/en-gb/articles/dv1aslrr/new40k-new-app-for-a-new-edition/`
- New Recruit: `https://www.newrecruit.eu/`
- BSData homepage: `https://www.bsdata.net/`
- BSData 40k data repository checked as a community-data example: `https://github.com/BSData/wh40k-10e`
- BSData catalogue data-structure wiki: `https://github.com/BSData/catalogue-development/wiki/Data-structure-overview`

## Source Trust Contract

Every source-derived artifact must carry provenance and readiness. This is mandatory for official PDFs, public Google Sheets, community roster data, profile packs, mission packs, and user uploads.

Required source metadata:

- `source_id`, `source_kind`, `source_label`, `source_url`, publisher/domain, retrieval timestamp.
- HTTP metadata where applicable: status, content type, byte size, redirect target, ETag, Last-Modified.
- Integrity fields: SHA-256, parser version, schema version, extraction version.
- Anchors: PDF page and section, sheet id/gid/range, row id, card id, image id/hash, bounding box for image-derived facts.
- Per-field `source_refs` on canonical data, not only pack-level provenance.
- Validation state, confidence, warnings, reviewer state, and override history.

Do not store or redistribute:

- Official PDFs, mission-card images, full card text, datasheet text, or long copied rules passages in the public repo.
- Community spreadsheet exports or BSData-derived data as bundled application data unless redistribution is explicitly reviewed.
- Generated packs that reconstruct protected rules/card/datasheet text.
- User rosters outside local user-controlled storage by default.

Fail closed when:

- Redirects leave an allowlist.
- Content type, size, page count, hash, or schema validation fails.
- A public sheet/image contains formulas, HTML/script content, or malformed data.
- Required source anchors are missing or contradictory.

## Readiness States

All significant outputs must report one of:

- `trusted`: all required source fields, pack versions, geometry assumptions, and validation records are present.
- `estimated`: output is useful but relies on approximated 2D movement, inferred terrain semantics, community data, or manual assumptions.
- `degraded`: output has unresolved warnings that materially affect interpretation.
- `blocked`: required data is missing or contradictory; the tool must not produce tactical recommendations.

False precision is a product bug. Avoid exact-looking scores, legal claims, and optimal plans unless the input state supports them.

## Roadmap Overview

### Phase 1 - Source And Rules Foundation

Goal: make current 11e mechanics source-backed before solvers depend on them.

Add:

- `RulesPack`: source-anchored mechanics, glossary, terminology mappings, and old-terminology blacklist.
- `SourcePackRegistry`: local pack discovery, hashes, versions, timestamps, and stale-data warnings.
- `MissionPack` skeleton: mission/card/action/objective source refs without full recommendation logic.
- `ProfilePack` and `PointsPack` skeletons: adapters can populate them from user-supplied/community data, but they are not treated as official rules truth.
- `BaseSizePack`: model base/frame data needed by movement, threat, and deployment tools.

Key rule concepts to model first:

- Terrain Area, Terrain Feature, Terrain Category, and visibility traits.
- Benefit of Cover, Hidden, Obscuring, Solid.
- Model bases, measuring, engagement, coherency, and movement types.
- Attack sequence and common weapon/core abilities.
- Objective control, terrain objectives, actions, reserves, transports, and disembark modes.

Acceptance:

- Packs include source refs and hashes.
- Old assumptions are blocked by tests: cover as default +1 save, 1-inch-only engagement, all reserves as Deep Strike, objectives as only markers, visibility as only boolean.
- Solvers can request rule concepts without hard-coded user-facing labels.

### Phase 2 - Canonical Board State

Goal: give every tool the same game-state model.

Add `BoardState` with:

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

### Phase 3 - Roster And Profile Adapter Layer

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
  -> ProfileResolution
  -> ProfilePack / PointsPack / BaseSizePack refs
  -> BoardState-ready army
```

Important separation:

- Roster import identifies selected units, wargear, enhancements, detachments, transports, reserves, and points as-presented.
- Profile resolution maps those selections to source/versioned profiles.
- Rules mechanics come from `RulesPack`, not roster text.
- Community catalogs can be used as profile candidates, but must be versioned, hashed, validated, and explicitly labeled community-derived unless an official local source backs them.

Acceptance:

- No roster entry is silently discarded.
- `.ros/.rosz` parsing preserves raw ids, names, selections, costs, and source paths.
- Profile statuses include `resolved_exact`, `resolved_alias`, `resolved_manual`, `ambiguous`, `unresolved`, and `unsupported`.
- The UI shows unresolved profile/base/points data before downstream analysis runs.

### Phase 4 - Movement Reach Toolkit

Goal: add the first new deterministic player tool beyond LOS.

Scope:

- Base-aware 2D movement reach.
- Dense/solid-feature collision checks.
- Board-edge constraints.
- Friendly/enemy model collision assumptions.
- Coherency checks for simple unit formations.
- Move type support for initial Normal Move, Advance, Charge, Scout, Ingress, and Disembark estimates.
- Terrain and vertical assumptions surfaced as warnings.

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

### Phase 5 - Threat Range Toolkit

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

Output should be probability/distribution based, not max-range-only. Max range can be shown, but recommendations must account for dice, rerolls, modifiers, CP/stratagem availability, and readiness warnings.

Acceptance:

- Threat overlays can be calculated without a full damage engine.
- Unsupported modifiers are visible and default to disabled.
- Threat tools can run in rosterless mode with manually entered movement/base/range, then become roster-aware when profiles resolve.

### Phase 6 - Damage And Survivability Profiles

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

### Phase 7 - Mission Pack And Game Analytics Primitives

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

### Phase 8 - Deployment And Safe-Area Toolkit

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

### Phase 9 - Matchup Analytics For Team Pairing

Goal: support team tournament captains selecting favorable pairings to maximize expected total tournament points.

This phase must come after toolkit primitives. The analytics engine should aggregate deterministic tool outputs:

- Damage/survivability asymmetry.
- Mission scoring capacity.
- Objective and action reliability.
- Deployment safety and staging quality.
- Threat projection pressure.
- Mobility and screening gaps.
- Unsupported-data penalties.

Output:

- Pairing matrix with confidence bands.
- Component breakdown, not one opaque number.
- Scenario assumptions: mission pack, terrain layout, player skill assumptions, going-first/second, list archetype tags.
- Recommended pairings with sensitivity analysis.

Do not start with game-theoretic captain automation. Start with explainable metrics and conservative expected-point bands.

Acceptance:

- Pairing estimates are blocked or degraded when required tools are missing.
- Captain-facing output shows why a pairing is favorable or risky.
- The app can export the assumptions and component metrics used for each estimate.

### Phase 10 - AI Companion

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
- Export user rosters or private tournament data to external services without explicit consent.
- Replace deterministic tool output with prose-only advice.

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
7. What confidence-band model is acceptable for team-pairing expected points.
8. Which AI runtime/tool-calling boundary is acceptable for private roster and tournament data.

## Immediate Next Specs

Write fine-grain implementation specs in this order:

1. `source-pack-registry-and-rulespack-11e-spec.md`
2. `canonical-board-state-spec.md`
3. `roster-import-and-profile-adapter-spec.md`
4. `base-size-and-terrain-semantics-spec.md`
5. `movement-reach-toolkit-spec.md`
6. `threat-range-toolkit-spec.md`
7. `damage-survivability-profile-spec.md`
8. `mission-pack-and-actions-spec.md`
9. `deployment-safety-toolkit-spec.md`
10. `team-pairing-analytics-primitives-spec.md`
11. `ai-companion-tool-orchestration-spec.md`

Implementation should not begin until the first fine-grain spec is reviewed and approved.
