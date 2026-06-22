# Player Toolkit Implementation Work Log

## 2026-06-19 - Phase 0 - Implementation Readiness

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Prepare the repository for phased implementation of the player-toolkit roadmap.
- Establish the per-phase goal loop, review, QA, work-log, and commit protocol before Phase 1 starts.
- Keep Phase 0 behavior-preserving and documentation-only.

Parent roadmap:

- `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`

Artifacts:

- `docs/superpowers/specs/2026-06-19-phase-0-implementation-readiness-design.md`
- `docs/superpowers/plans/2026-06-19-phase-0-implementation-readiness.md`
- `docs/superpowers/qa/2026-06-19-phase-0-implementation-readiness-qa.md`
- `docs/superpowers/reviews/2026-06-19-phase-0-consultant-readiness.md`
- `docs/superpowers/reviews/2026-06-19-phase-0-adversarial-readiness.md`
- `docs/qa-scenarios.md`
- `docs/work-log/player-toolkit-implementation.md`

Design decisions:

- Phase 0 is documentation scaffolding only. It must not implement Phase 1 runtime behavior.
- Autonomous QA pathways live under `docs/superpowers/qa/`.
- One program-level work log tracks phase decisions, review outcomes, verification, and blockers.
- Durable review records live under `docs/superpowers/reviews/` so final approvals can be inspected without reading the conversation.
- The detailed Phase 1 source/rules spec is intentionally deferred to the Phase 1 goal loop, where source facts can be refreshed before design approval.
- Browser and Computer Use checks are required only for phases that change web, desktop, packaged, or runtime behavior.

Review gates:

- Consultant review must confirm the Phase 0 artifact set is sufficient to start Phase 1.
- Adversarial review must confirm Phase 0 does not prematurely implement Phase 1, lacks no proof gates, and has an executable QA pathway.

Consultant review triage:

- Accepted: add durable review evidence.
- Accepted: update `docs/qa-scenarios.md` with roadmap phase QA expectations.
- Accepted: add preflight, AGENTS compliance, behavior-preservation, optional baseline, and Browser/Computer Use checks to the Phase 0 QA pathway.
- Accepted with scope clarification: do not create the Phase 1 fine-grain spec in Phase 0; create it inside the Phase 1 goal loop.

Adversarial review triage:

- Accepted: record actual consultant and adversarial outcomes in durable review files instead of placeholders.
- Accepted: add freshness/source-refresh requirements for phases using mutable official, public-sheet, MFM, roster, mission-pack, or community-pack data.
- Accepted: replace brittle workspace-path preconditions with a `Resolve-Path .` check.
- Accepted: include untracked files in behavior-preservation checks and use an explicit Phase 0 allowlist.
- Accepted: scope AGENTS compliance checks to changed, staged, and untracked files.
- Accepted: require exact staged-file set in any order, forbid staging user-owned `AGENTS.md`, and add post-commit proof.

Final review approvals:

- 2026-06-20: consultant reviewer `019ee4cb-1a71-72f3-80d2-35838a50cfc9` approved Phase 0 readiness.
- 2026-06-20: adversarial reviewer `019ee4cb-4274-7211-9b4e-a757e02b1110` approved Phase 0 scope, source-trust, IP/security, and QA executability.

Verification to run before commit:

- `git status --short --branch`
- Draft-marker scan across Phase 0 artifacts.
- ASCII scan across Phase 0 artifacts.
- `git diff --check`
- `git diff --cached --check`
- Behavior-preservation check with `git diff --name-only` and `git diff --cached --name-only`

Verification results:

- 2026-06-20: required Phase 0 artifacts exist.
- 2026-06-20: draft-marker scan returned no matches.
- 2026-06-20: ASCII scan returned no non-ASCII findings.
- 2026-06-20: `git diff --check` passed; Git reported only the normal line-ending warning for `docs/qa-scenarios.md`.
- 2026-06-20: behavior-preservation allowlist passed. Visible changed/untracked files are the Phase 0 docs plus user-owned untracked `AGENTS.md`.
- 2026-06-20: AGENTS/source-trust compliance check passed for changed, staged, and untracked files.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff check .` passed; Ruff reported a nonblocking cache-write warning.
- 2026-06-20: `.\.venv\Scripts\mypy.exe src` passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m pytest` passed: 187 passed, 1 warning.
- 2026-06-20: `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets` passed for 45 official seed packets.
- 2026-06-20: `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test` passed with status `ok` and 45 official packets.
- 2026-06-20: Browser and Computer Use checks were not required for Phase 0 because the phase changes no runtime, web, desktop, or packaged behavior.

Baseline note:

- 2026-06-20: optional `.\.venv\Scripts\python.exe -m ruff format --check src tests` reported existing formatting drift in `src\warhammer_companion\los\geometry.py`. Phase 0 did not modify that source file. This should be handled in a later `.5` housekeeping loop rather than inside the docs-only Phase 0 checkpoint unless reviewers decide it blocks readiness.

Known notes:

- `AGENTS.md` is present in the worktree and applies to the repository. It is treated as user-owned unless explicitly staged for this phase.
- No production code, tests, data, packaging, web UI, or desktop UI should change in Phase 0.

## 2026-06-20 - Phase 0.5 - Housekeeping Formatting Baseline

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Resolve the known Phase 0 optional baseline issue where Ruff would reformat `src\warhammer_companion\los\geometry.py`.
- Keep the slice behavior-preserving and formatter-only before Phase 1 begins.

Artifacts:

- `docs/superpowers/specs/2026-06-20-phase-0-5-housekeeping-formatting-design.md`
- `docs/superpowers/plans/2026-06-20-phase-0-5-housekeeping-formatting.md`
- `docs/superpowers/qa/2026-06-20-phase-0-5-housekeeping-formatting-qa.md`
- `docs/superpowers/reviews/2026-06-20-phase-0-5-consultant-housekeeping.md`
- `docs/superpowers/reviews/2026-06-20-phase-0-5-adversarial-housekeeping.md`
- `src/warhammer_companion/los/geometry.py`

Design decisions:

- Phase 0.5 is a behavior-preserving housekeeping slice.
- The only source edit allowed is Ruff formatter output in `src\warhammer_companion\los\geometry.py`.
- No new tests are added because no behavior changes are intended.
- Browser and Computer Use checks are not required because this slice changes no runtime, web, desktop, or packaged behavior.

Verification to run before commit:

- `.\.venv\Scripts\python.exe -m ruff format --check src tests`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\mypy.exe src`
- `.\.venv\Scripts\python.exe -m pytest`
- `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets`
- `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test`
- `git diff --check`
- Phase 0.5 changed-file allowlist check.

Review approvals:

- 2026-06-20: consultant reviewer `019ee4e5-8a9e-7c12-a3a0-28459b4b13ff` approved the Phase 0.5 housekeeping scope and QA pathway.
- 2026-06-20: adversarial reviewer `019ee4e5-b2d2-7681-814c-9407ca9befd3` approved behavior preservation, source-trust/IP/security scope, and QA adequacy.

Verification results:

- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff format src\warhammer_companion\los\geometry.py` reformatted one file.
- 2026-06-20: source diff in `src\warhammer_companion\los\geometry.py` is formatter-only: one chained expression rewrapped.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 73 files already formatted.
- 2026-06-20: Phase 0.5 changed-file allowlist passed. Visible files were Phase 0.5 artifacts plus user-owned untracked `AGENTS.md`.
- 2026-06-20: `git diff --check` passed; Git reported normal line-ending warnings for touched files.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff check .` passed.
- 2026-06-20: `.\.venv\Scripts\mypy.exe src` passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m pytest` passed: 187 passed, 1 warning.
- 2026-06-20: `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets` passed for 45 official seed packets.
- 2026-06-20: `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test` passed with status `ok` and 45 official packets.
- 2026-06-20: Browser and Computer Use checks were not required because Phase 0.5 changes no runtime, web, desktop, or packaged behavior.

## 2026-06-20 - Phase 1 - Source Pack Registry And Current RulesPack

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Add the first source/rules foundation for downstream toolkit solvers.
- Represent current source candidates, freshness metadata, readiness, and legacy assumption blockers.
- Avoid bundling official PDFs, public sheets, roster data, community packs, or copied rules text.

Current source facts checked:

- Warhammer Community downloads page lists the Warhammer 40,000 Munitorum Field Manual and marks it updated `17/6/2026`.
- The Munitorum Field Manual page reports upstream version `v1.0`.
- The current core rules PDF candidate is `https://assets.warhammer-community.com/eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf`.
- New Recruit describes Warhammer 40k support and BattleScribe roster compatibility.
- New Recruit states that BattleScribe data sets are maintained by BSData communities and downloaded from GitHub.
- BSData presents itself as a community-maintained GitHub-hosted project.

Artifacts:

- `docs/superpowers/specs/2026-06-20-source-pack-registry-and-rulespack-current-spec.md`
- `docs/superpowers/plans/2026-06-20-source-pack-registry-and-rulespack-current.md`
- `docs/superpowers/qa/2026-06-20-source-pack-registry-and-rulespack-current-qa.md`
- `docs/superpowers/reviews/2026-06-20-phase-1-consultant-source-foundation.md`
- `docs/superpowers/reviews/2026-06-20-phase-1-adversarial-source-foundation.md`
- `src/warhammer_companion/ingestion/rules_sources.py`
- `tests/test_rules_sources.py`

Design decisions:

- The first implementation is metadata-only and side-effect free.
- Current-source metadata lives under `warhammer_companion.ingestion` to match the existing source registry boundary.
- No rules concept is `trusted` in this slice because field-level source refs, hashes, and reviewed mechanics are not implemented yet.
- Legacy assumptions are represented as explicit blacklist keys so downstream solvers can block them in tests.

Review triage:

- Accepted: add an explicitly invoked `verify_remote_http_source()` fetch/hash verifier with injected fake-response tests.
- Accepted: block non-200 remote responses before hashing, even when an injected response no-ops `raise_for_status()`.
- Accepted: validate HTTPS scheme and approved hosts before remote verification network access.
- Accepted: validate redirected final URLs and block unapproved redirect targets.
- Accepted: block empty content and missing content type.
- Accepted: MFM freshness is `unknown` unless a refresh timestamp is supplied to `build_current_rules_foundation()`.

Final review approvals:

- 2026-06-20: consultant reviewer `019ee4f2-376b-75e3-b5a3-f615cda286e2` approved after verifier hardening.
- 2026-06-20: adversarial reviewer `019ee4f2-6019-78d1-b684-43c09d549a91` approved source-trust/IP/security and QA after verifier hardening.

Verification to run before commit:

- `.\.venv\Scripts\python.exe -m pytest tests\test_rules_sources.py -q`
- `.\.venv\Scripts\python.exe -m ruff format --check src tests`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\mypy.exe src`
- `.\.venv\Scripts\python.exe -m pytest`
- `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets`
- `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test`
- `git diff --check`
- Phase 1 changed-file allowlist and protected-content scan.

Verification results:

- 2026-06-20: red step confirmed `tests\test_rules_sources.py` initially failed because `warhammer_companion.ingestion.rules_sources` did not exist.
- 2026-06-20: targeted `.\.venv\Scripts\python.exe -m pytest tests\test_rules_sources.py -q` passed: 11 passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 75 files already formatted.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff check .` passed.
- 2026-06-20: `.\.venv\Scripts\mypy.exe src` passed.
- 2026-06-20: protected-content scan over `rules_sources.py` and `test_rules_sources.py` returned no matches.
- 2026-06-20: Phase 1 changed-file allowlist passed. Visible files are Phase 1 artifacts plus user-owned untracked `AGENTS.md`.
- 2026-06-20: `.\.venv\Scripts\python.exe -m pytest` passed: 198 passed, 1 warning.
- 2026-06-20: `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets` passed for 45 official seed packets.
- 2026-06-20: `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test` passed with status `ok` and 45 official packets.
- 2026-06-20: `git diff --check` passed; Git reported normal line-ending warnings for touched files.
- 2026-06-20: Browser and Computer Use checks were not required because Phase 1 changes no web, desktop, packaged, or runtime UI behavior.

## 2026-06-20 - Phase 1.5 - Source Foundation Housekeeping

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Perform behavior-preserving cleanup after Phase 1.
- Make the remote verifier test helper contract explicit before Phase 2.

Artifacts:

- `docs/superpowers/specs/2026-06-20-phase-1-5-housekeeping-source-foundation.md`
- `docs/superpowers/plans/2026-06-20-phase-1-5-housekeeping-source-foundation.md`
- `docs/superpowers/qa/2026-06-20-phase-1-5-housekeeping-source-foundation-qa.md`
- `docs/superpowers/reviews/2026-06-20-phase-1-5-consultant-source-foundation.md`
- `docs/superpowers/reviews/2026-06-20-phase-1-5-adversarial-source-foundation.md`
- `src/warhammer_companion/ingestion/rules_sources.py`
- `tests/test_rules_sources.py`

Review triage:

- Consultant approved the narrow cleanup and found no larger cleanup needed before Phase 2.
- Adversarial review found the initial `_fake_get_factory() -> RemoteGet` annotation did not pass
  `mypy tests\test_rules_sources.py`.
- Accepted: `RemoteResponse` fields are now read-only properties, and fake getters use
  `RemoteGet`/`RemoteResponse` explicitly.
- Accepted: Phase 1.5 QA includes `.\.venv\Scripts\mypy.exe tests\test_rules_sources.py`.

Final review approvals:

- 2026-06-20: consultant reviewer `019ee4ff-3ca7-7e30-acac-e0fdf1244884` approved the narrow housekeeping scope.
- 2026-06-20: adversarial reviewer `019ee4ff-65bb-7f01-b412-67b033c8e6b7` approved after the test-mypy fix.

Verification results:

- 2026-06-20: initial `.\.venv\Scripts\mypy.exe tests\test_rules_sources.py` failed with four test helper typing errors.
- 2026-06-20: after the protocol fix, `.\.venv\Scripts\mypy.exe tests\test_rules_sources.py` passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m pytest tests\test_rules_sources.py -q` passed: 11 passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 75 files already formatted.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff check .` passed.
- 2026-06-20: `.\.venv\Scripts\mypy.exe src` passed.
- 2026-06-20: Phase 1.5 changed-file allowlist passed. Visible files are Phase 1.5 artifacts plus user-owned untracked `AGENTS.md`.
- 2026-06-20: `git diff --check` passed; Git reported normal line-ending warnings for touched files.

## 2026-06-20 - Phase 2 - Toolkit Result And Board State Foundation

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Add shared toolkit result and board-state primitives before new deterministic tools are built.
- Keep `MapPacket` as layout geometry and bind game-state assumptions through `BoardState`.
- Prove the LOS checker can produce a `ToolkitResult` before existing SVG projection.

Artifacts:

- `docs/superpowers/specs/2026-06-20-toolkit-result-and-board-state-spec.md`
- `docs/superpowers/plans/2026-06-20-toolkit-result-and-board-state.md`
- `docs/superpowers/qa/2026-06-20-toolkit-result-and-board-state-qa.md`
- `docs/superpowers/reviews/2026-06-20-phase-2-consultant-toolkit-foundation.md`
- `docs/superpowers/reviews/2026-06-20-phase-2-adversarial-toolkit-foundation.md`
- `src/warhammer_companion/domain/board_state.py`
- `src/warhammer_companion/domain/overlays.py`
- `src/warhammer_companion/application/toolkit.py`
- `tests/test_toolkit_contracts.py`
- `tests/test_board_state.py`

Design decisions:

- `MapOverlayLayer`, `ToolkitReadiness`, `ToolkitAssumption`, and `ToolkitWarning` live in
  `domain.overlays` so domain modules do not depend on application modules.
- `BoardState` lives in `domain.board_state` and is a shallow immutable wrapper over a live
  `MapPacket` plus a packet content digest.
- `ToolkitResult` lives in `application.toolkit` as the service envelope returned before web or
  desktop rendering.
- `trusted` toolkit results require both source refs and a passed validation record.
- Phase 2 adds a narrow `los_checker_toolkit_result()` service method. Heatmap and hidden coverage
  toolkit wrappers are deferred to later slices.
- Browser and Computer Use checks are not required because this slice changes no web route,
  template, static asset, generated SVG behavior, desktop widget, installer, OS interaction, or
  packaged UI behavior.

Review triage:

- Accepted: split board-state, overlay, and result-envelope modules by ownership.
- Accepted: add invalid-readiness validation for `ToolkitResult` and `MapOverlayLayer`.
- Accepted: reject blocked results without block reasons and blocked results with tactical
  overlays.
- Accepted: reject trusted results without source refs or a passed validation record.
- Accepted: reject overlays whose readiness exceeds the parent result readiness.
- Accepted: add packet content digest and include it in LOS toolkit input identity.
- Accepted: document `BoardState` shallow immutability and store `packet_digest`.
- Accepted: warn when units contain no models.
- Accepted: prove `los_checker_state()` still matches the direct legacy render path.
- Accepted: update the QA protected-content scan so it does not self-match the QA regex.

Verification results:

- 2026-06-20: red step confirmed Phase 2 tests initially failed because
  `warhammer_companion.application.toolkit` and `warhammer_companion.domain.board_state` did not
  exist.
- 2026-06-20: red step confirmed `MapOverlayLayer` initially accepted invalid readiness.
- 2026-06-20: red step confirmed `trusted` results initially did not require source refs or passed
  validation.
- 2026-06-20: `.\.venv\Scripts\python.exe -m pytest tests\test_toolkit_contracts.py tests\test_board_state.py tests\test_application_service.py -q` passed after fixes: 19 passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m pytest tests\test_toolkit_contracts.py tests\test_board_state.py tests\test_application_service.py tests\test_los_geometry.py tests\test_rendering_svg.py -q` passed after reviewer fixes: 62 passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff check .` passed.
- 2026-06-20: `.\.venv\Scripts\mypy.exe src` passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m pytest` passed: 213 passed, 1 warning.
- 2026-06-20: `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets` passed for 45 official seed packets.
- 2026-06-20: `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test` passed with status `ok` and 45 official packets.
- 2026-06-20: Phase 2 protected-content scan returned no matches.
- 2026-06-20: `git diff --check` passed with normal CRLF warnings for touched files.
- 2026-06-20: `git diff --cached --check` passed before staging.

Final review approvals:

- 2026-06-20: architecture/code-quality re-review `019ee520-1e85-7dd1-ab08-769ccf1df0b3`
  approved with no findings.
- 2026-06-20: spec/readiness re-review `019ee51f-f32c-7b32-a4cd-9c0c8d81ea76` approved with no
  code/spec/QA blockers.

Browser and Computer Use:

- 2026-06-20: not required for Phase 2 because this slice changes no web route, template, static
  asset, generated SVG behavior, desktop widget, installer, OS interaction, or packaged UI
  behavior. Existing service/rendering/desktop smoke checks passed.

## 2026-06-20 - Phase 2.5 - LOS Toolkit Housekeeping

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Keep `WarhammerCompanionService` from owning LOS toolkit construction details after Phase 2.
- Extract behavior-preserving LOS toolkit result construction into a focused application module.

Artifacts:

- `docs/superpowers/specs/2026-06-20-phase-2-5-housekeeping-los-toolkit.md`
- `docs/superpowers/plans/2026-06-20-phase-2-5-housekeeping-los-toolkit.md`
- `docs/superpowers/qa/2026-06-20-phase-2-5-housekeeping-los-toolkit-qa.md`
- `docs/superpowers/reviews/2026-06-20-phase-2-5-consultant-los-toolkit.md`
- `docs/superpowers/reviews/2026-06-20-phase-2-5-adversarial-los-toolkit.md`
- `src/warhammer_companion/application/los_toolkit.py`
- `tests/test_los_toolkit.py`

Design decisions:

- `application.los_toolkit` owns `LosCheckerToolkitPayload`, the LOS toolkit schema version,
  input hashing, assumptions, warnings, overlays, and payload construction.
- `WarhammerCompanionService` still owns packet selection, selector handling, input clamping, and
  view-model projection.
- No domain contracts, LOS geometry, rendering, heatmap, hidden coverage, web route, desktop code,
  or UI behavior changed.

Review triage:

- Consultant approved the extraction as warranted before Phase 3.
- Adversarial reviewer requested tighter builder-contract tests and ASCII-only spec text.
- Accepted: `tests/test_los_toolkit.py` now pins the literal v0 hash format, exact result/layer
  IDs, assumption and warning metadata, overlay metadata, overlay geometry identity,
  recommendation-language guard, and packet non-mutation.
- Accepted: replaced non-ASCII spec text with ASCII `facade`.

Verification results:

- 2026-06-20: red step confirmed `tests\test_los_toolkit.py` failed because
  `warhammer_companion.application.los_toolkit` did not exist.
- 2026-06-20: `.\.venv\Scripts\python.exe -m pytest tests\test_los_toolkit.py tests\test_application_service.py tests\test_toolkit_contracts.py tests\test_board_state.py -q` passed: 20 passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m pytest tests\test_los_toolkit.py tests\test_application_service.py tests\test_los_geometry.py tests\test_rendering_svg.py -q` passed: 51 passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed.
- 2026-06-20: `.\.venv\Scripts\python.exe -m ruff check .` passed.
- 2026-06-20: `.\.venv\Scripts\mypy.exe src` passed.
- 2026-06-20: adversarial re-review approved Phase 2.5 with no critical or important findings.
- 2026-06-20: `.\.venv\Scripts\python.exe -m pytest` passed: 214 passed, 1 warning.
- 2026-06-20: `git diff --check` passed with normal CRLF warnings for touched files.

Browser and Computer Use:

- 2026-06-20: not required because Phase 2.5 changes no web route, template, static asset,
  generated SVG behavior, desktop widget, installer, OS interaction, or packaged UI behavior.
  Existing service and rendering regression tests passed.

## 2026-06-20 - Phase 3 - Base Size And Terrain Semantics

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Add source-aware manual base-size/model-frame records and terrain semantics records before
  movement, threat, and exposure solvers are implemented.
- Let rosterless/manual tool inputs exist without treating manual data or packet labels as trusted
  mechanics.
- Preserve current LOS, `MapPacket`, rendering, web, and desktop behavior.

Artifacts:

- `docs/superpowers/specs/2026-06-20-base-size-and-terrain-semantics-spec.md`
- `docs/superpowers/plans/2026-06-20-base-size-and-terrain-semantics.md`
- `docs/superpowers/qa/2026-06-20-base-size-and-terrain-semantics-qa.md`
- `docs/superpowers/reviews/2026-06-20-phase-3-consultant-base-terrain.md`
- `docs/superpowers/reviews/2026-06-20-phase-3-adversarial-base-terrain.md`
- `src/warhammer_companion/domain/semantics.py`
- `src/warhammer_companion/domain/base_sizes.py`
- `src/warhammer_companion/domain/terrain_semantics.py`
- `src/warhammer_companion/application/base_sizes.py`
- `src/warhammer_companion/application/terrain_semantics.py`
- `tests/test_base_sizes.py`
- `tests/test_terrain_semantics.py`

Design decisions:

- Phase 3 is a contracts-and-adapters slice, not a solver or UI slice.
- Shared semantic readiness primitives live in `domain.semantics`.
- Base and model-frame records live in `domain.base_sizes`.
- Terrain semantics live in `domain.terrain_semantics` and are keyed over `MapPacket` IDs plus
  `map_packet_digest`.
- Thin application builders return `ToolkitResult` payloads for manual model-frame records and
  terrain semantics indexes.
- Manual base records normalize dimensions to inches, retain original units in provenance, and
  remain `estimated`.
- Source refs on a manual record do not make it trusted. Trusted tactical claims still require
  source refs plus passed validation at the `ToolkitResult` level.
- Invalid/missing base data and incompatible source packs return blocked results with block reasons
  and no overlays.
- Terrain semantics preserve existing 2D LOS blocker flags as geometry hints, not official rules
  truth.

Consultant review triage:

- Accepted: split base-size and terrain-semantics records into focused domain modules.
- Accepted: include local operator marker, timestamp, reason, reviewed fields, override history,
  units, field-level source refs, freshness, compatibility, assumptions, warnings, and validation
  record slots for manual base records.
- Accepted: include packet digest in terrain semantics records and toolkit input hashes.
- Accepted: test that manual base size changes, packet digest changes, and source-pack version
  changes alter toolkit input hashes.
- Accepted: keep `MapPacket.blockers()`, LOS toolkit, LOS geometry, rendering, web, and desktop
  paths unchanged.

Adversarial review triage:

- Accepted: reject non-finite base dimensions (`NaN`, `Infinity`) for round and oval manual bases.
- Accepted: ensure app-level manual model-frame builders block non-finite dimensions.
- Accepted: trusted semantic reports require source refs and a passed validation record.
- Accepted: record-level stale freshness or incompatible source-pack state blocks trusted tactical
  claims.
- Accepted: model-frame readiness reports preserve nested base source refs, validation records, and
  assumptions.
- Accepted: add regression tests for all review findings before changing production code.
- Accepted: second adversarial re-review found mixed trusted-record aggregates could still allow
  trusted claims; add a regression and validate source refs plus passed validation per trusted
  record.

Verification results:

- 2026-06-20: red step confirmed `tests\test_base_terrain_semantics.py` initially failed because
  `warhammer_companion.domain.semantics` did not exist.
- 2026-06-20: after consultant triage, split red step confirmed `tests\test_base_sizes.py` and
  `tests\test_terrain_semantics.py` failed because the new Phase 3 domain/application modules did
  not exist.
- 2026-06-20: focused `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q` passed: 12 passed.
- 2026-06-20: regression `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py tests\test_board_state.py tests\test_los_toolkit.py tests\test_los_geometry.py tests\test_rendering_svg.py tests\test_toolkit_contracts.py -q` passed: 68 passed.
- 2026-06-20: `.\.venv\Scripts\mypy.exe src` passed.
- 2026-06-20: initial Ruff format/check found new-file formatting/import issues; formatter and
  import-sort fix were applied.
- 2026-06-20: after formatting, `.\.venv\Scripts\python.exe -m ruff format --check src tests`
  passed: 89 files already formatted.
- 2026-06-20: after formatting, `.\.venv\Scripts\python.exe -m ruff check .` passed.
- 2026-06-20: after formatting, focused regression passed again: 68 passed.
- 2026-06-20: adversarial review requested finite dimension validation, trusted semantic gating,
  and nested base provenance propagation.
- 2026-06-20: review-fix red step failed as expected: 8 failed, 12 passed across
  `tests\test_base_sizes.py` and `tests\test_terrain_semantics.py`.
- 2026-06-20: after review fixes, focused `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q` passed: 20 passed.
- 2026-06-20: after review fixes, focused regression `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py tests\test_board_state.py tests\test_toolkit_contracts.py tests\test_los_toolkit.py tests\test_los_geometry.py tests\test_rendering_svg.py -q` passed: 76 passed.
- 2026-06-20: after review fixes, `.\.venv\Scripts\mypy.exe src` passed.
- 2026-06-20: after review fixes, `.\.venv\Scripts\python.exe -m ruff format --check src tests`
  and `.\.venv\Scripts\python.exe -m ruff check .` passed.
- 2026-06-20: full `.\.venv\Scripts\python.exe -m pytest` passed: 226 passed, 1 warning.
- 2026-06-20: `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets` passed for 45 official seed packets.
- 2026-06-20: `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test`
  passed with status `ok`, 45 official packets, page 9 selected, and viewer/LOS/heatmap/hidden
  coverage SVG checks true.
- 2026-06-20: protected-content scan over Phase 3 production/test files returned no matches.
- 2026-06-20: tracked-file raw artifact scan returned no tracked raw PDFs, roster archives,
  spreadsheets, SQLite/db files, or processed data paths.
- 2026-06-20: second adversarial re-review found a mixed trusted-record aggregate false-trust bug.
- 2026-06-20: mixed trusted-record red step failed as expected with `trusted` instead of
  `degraded`.
- 2026-06-20: after the reducer fix, mixed trusted-record regression passed.
- 2026-06-20: after the reducer fix, focused `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q` passed: 21 passed.
- 2026-06-20: after the reducer fix, `.\.venv\Scripts\python.exe -m ruff format --check src tests`,
  `.\.venv\Scripts\python.exe -m ruff check .`, and `.\.venv\Scripts\mypy.exe src` passed.
- 2026-06-20: after the reducer fix, focused regression `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py tests\test_board_state.py tests\test_toolkit_contracts.py tests\test_los_toolkit.py tests\test_los_geometry.py tests\test_rendering_svg.py -q` passed: 77 passed.
- 2026-06-20: final adversarial re-review `019ee6ae-95aa-72e2-8375-21c064be0db9` approved the
  per-record trusted gating fix with no critical or important findings.
- 2026-06-20: final full `.\.venv\Scripts\python.exe -m pytest` passed: 235 passed, 1 warning.
- 2026-06-20: final packet validation passed for all 45 official seed packets.
- 2026-06-20: final desktop smoke passed with status `ok`.
- 2026-06-20: final `git diff --check` passed with the normal CRLF warning for the work log.

Browser and Computer Use:

- 2026-06-20: built-in-browser manual QA is required for final Phase 3 closeout because the user
  requested it, even though Phase 3 changes no web route, template, static asset, generated SVG
  behavior, desktop widget, installer, OS interaction, or packaged UI behavior.
- 2026-06-20: main-thread Browser and Computer Use setup were blocked because `node_repl/js` failed
  before any app interaction with `Mcp error: -32602: js: codex/sandbox-state-meta: missing field
  sandboxPolicy`.
- 2026-06-20: browser-QA subagent `019ee6a8-eaec-7be0-9471-4b9dfa555daf` hit the same Browser
  runtime blocker, but confirmed `http://127.0.0.1:8000` returned HTTP 200 with title
  `Warhammer Tournament Companion`.

## 2026-06-21 - Browser And Computer Use Recovery Slice

Purpose:

- Restore the built-in Browser/Computer Use QA path required by the user before treating Phase 3
  as fully closed.
- Gather independent route/render evidence while the Codex MCP bridge remains unavailable.

Findings:

- Post-restart `node_repl/js` still failed before JavaScript execution with
  `Mcp error: -32602: js: codex/sandbox-state-meta: missing field sandboxPolicy`.
- Manual stdio probes showed the bundled
  `C:\Users\Conferences and AI\AppData\Local\OpenAI\Codex\runtimes\cua_node\a89897d3d9baa117\bin\node_repl.exe`
  can execute JavaScript when called directly.
- A manual malformed-metadata probe reproduced the exact `sandboxPolicy` rejection when
  `_meta["codex/sandbox-state-meta"]` was present without `sandboxPolicy`.
- A temporary metadata-sanitizing proxy was prototyped and verified to strip only the malformed
  sandbox-state subfield while preserving other `_meta` keys.
- Global Codex config was pointed at that proxy with backup
  `C:\Users\Conferences and AI\.codex\config.toml.bak-node-repl-proxy-20260621004038`.
- The current Codex MCP transport stayed closed after stale `node_repl.exe` helper processes were
  stopped; a Codex Desktop restart is still required before the proxy can be proven in the hosted
  tool path.

Independent QA evidence:

- `http://127.0.0.1:49231` was started with direct Uvicorn on a Browser-allowlisted origin.
- `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:49231` returned HTTP 200 with title
  `Warhammer Tournament Companion` and response length 18358.
- Headless Firefox with a throwaway `C:\tmp` profile captured
  `C:\tmp\w40k-phase3-home-49231.png`.
- Screenshot evidence: 1280x900 PNG, 104614 bytes, nonblank RGB extrema
  `((21, 255), (27, 255), (22, 255))`, SHA-256
  `02F1ABFBB8B5D4D9583E3E0E38561A49786C627132DC63CBD1B3EEBE42B32353`.
- The screenshot visibly renders the Map Viewer page for Layout A - Event Companion page 9.

Remaining blocker:

- Built-in Browser/Computer Use manual QA is not yet restored in the active Codex session.
- Retest after Codex Desktop reloads the proxy-backed `node_repl` config with:
  `nodeRepl.write("node-repl-ok")`.

## 2026-06-21 - Browser Control Restored After Codex Update

Purpose:

- Re-test built-in Browser after the Codex Desktop update and complete the pending Phase 3 manual
  QA gate.

Findings:

- Codex updated Browser/Computer tooling to `26.616.51431` and replaced the temporary proxy config
  with the bundled `cua_node\1b23c930bdf84ed6` runtime.
- `winget upgrade Codex -s msstore` returned `No available upgrade found`.
- `node_repl/js` now executes successfully and exposes complete turn metadata.
- Browser setup with `browser\26.616.51431\scripts\browser-client.mjs` succeeded.
- The temporary local proxy script was removed because it is no longer needed.

Built-in Browser QA evidence:

- Local web app was launched with Uvicorn on `http://127.0.0.1:49231`.
- `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:49231` returned HTTP 200 with title
  `Warhammer Tournament Companion`.
- Browser opened `http://127.0.0.1:49231/viewer` and confirmed:
  - title `Warhammer Tournament Companion`
  - heading `Map Viewer`
  - 3 selectors
  - 1 SVG map
  - all 16 terrain labels
  - no console errors
- Browser route sweep confirmed the main pages render without console errors:
  - `/viewer`: `Map Viewer`, 1 form, 3 selects, 1 SVG, 16 terrain labels.
  - `/heatmap`: `LOS Heatmap`, 1 form, 5 selects, 1 SVG, 1 embedded PNG.
  - `/los-checker`: `LOS Checker`, 1 form, 1 SVG, 1 embedded PNG.
  - `/hidden-coverage`: `Hidden Coverage`, 1 form, 4 selects, 1 SVG, 1 embedded PNG,
    16 terrain labels.
  - `/settings`: `Settings`, 2 forms, no console errors.
  - `/map-data`: `Map Data Management`, 46 forms, no console errors.
- Browser interaction checks passed:
  - Map Viewer submitted Layout B and rendered Event Companion page 10 with 1 SVG and 16 terrain
    labels.
  - LOS Heatmap submitted Layout B, defender zone, and full deployment zone source; rendered 1 SVG
    and 1 embedded PNG.
  - LOS Checker submitted x=30.5, y=24.0, base=1.57; rendered 1 SVG and 1 embedded PNG with
    clear/blocked result text.
  - Hidden Coverage submitted Layout B and Terrain 6; rendered 1 SVG, 1 embedded PNG, and 16
    terrain labels.
- Browser screenshot evidence from the final Hidden Coverage state:
  - URL:
    `http://127.0.0.1:49231/hidden-coverage?player_a=Take+and+Hold&player_b=Take+and+Hold&layout_variant=B&terrain_area_id=terrain-06&detection_range=15`
  - title `Warhammer Tournament Companion`
  - screenshot size 67101 bytes.

Final verification:

- 2026-06-21: `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed:
  89 files already formatted.
- 2026-06-21: `.\.venv\Scripts\python.exe -m ruff check .` passed.
- 2026-06-21: `.\.venv\Scripts\mypy.exe src` passed: no issues in 62 source files.
- 2026-06-21: focused Phase 3 tests passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q`
  returned 21 passed.
- 2026-06-21: full `.\.venv\Scripts\python.exe -m pytest` passed: 235 passed,
  1 known Starlette `TestClient` deprecation warning.
- 2026-06-21: packet validation passed for all 45 official seed packets.
- 2026-06-21: desktop smoke passed with status `ok`, 45 official packets, page 9 selected, and
  viewer/LOS/heatmap/hidden coverage SVG checks true.

## 2026-06-21 - Phase 3.5 - Semantics Identity Hardening

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Close provenance, identity, and unsupported-shape gaps in Phase 3 before Phase 4 introduces
  roster archives, XML, pasted text, and community-derived profile data.
- Keep this as a housekeeping hardening slice, not a roster/profile implementation slice.

Artifacts:

- `docs/superpowers/specs/2026-06-21-phase-3-5-semantics-identity-hardening.md`
- `docs/superpowers/plans/2026-06-21-phase-3-5-semantics-identity-hardening.md`
- `docs/superpowers/qa/2026-06-21-phase-3-5-semantics-identity-hardening-qa.md`
- `docs/superpowers/reviews/2026-06-21-phase-3-5-consultant-semantics-hardening.md`
- `docs/superpowers/reviews/2026-06-21-phase-3-5-adversarial-semantics-hardening.md`
- `src/warhammer_companion/application/base_sizes.py`
- `src/warhammer_companion/application/terrain_semantics.py`
- `src/warhammer_companion/domain/base_sizes.py`
- `tests/test_base_sizes.py`
- `tests/test_terrain_semantics.py`

Design decisions:

- Phase 4 implementation remains blocked until the Phase 4 fine-grain spec and QA path are written.
- Terrain semantics result hashes now include canonical source refs and source freshness.
- Manual model-frame result hashes now use canonical JSON over durable audit inputs instead of a
  partial delimited string.
- Empty manual unit footprints block with `missing-unit-models`.
- Manual unit footprints preserve footprint-level source refs in readiness reports.
- Hull/custom base shapes are explicitly unsupported until a future slice adds real footprint
  geometry or a source-backed measurement policy.
- No LOS, rendering, `MapPacket`, web, desktop, roster/profile, or protected-data behavior changed.

Consultant review triage:

- Consultant reviewer `019ee952-7e35-7283-aef6-be68652cf0ff` recommended going straight into the
  Phase 4 spec loop, but accepted that any forced housekeeping slice must stay narrow and avoid
  LOS/rendering/UI/packet changes.
- Final consultant reviewer `019ee95b-717b-78d1-8536-cf8b68370ba4` approved the Phase 3.5 working
  tree with no findings.

Adversarial review triage:

- Adversarial reviewer `019ee952-a817-7fe0-8698-a25dd8f3e7b7` blocked direct Phase 4 implementation
  until a Phase 4 spec/QA path exists and requested Phase 3.5 hardening first.
- Accepted: terrain semantics hashes must include provenance-sensitive source refs and freshness.
- Accepted: stale terrain source freshness must block.
- Accepted: empty manual footprints must not remain `estimated`.
- Accepted: hull/custom base shapes must not create exact-looking usable records without a footprint
  policy.
- Accepted: manual model-frame hashes must include labels, reason, and source refs in a structured
  canonical payload.
- Final adversarial reviewer `019ee96e-04e3-7fb3-a2ee-64cf4f6b8cb2` found one remaining P2:
  arbitrary runtime strings such as `triangle` could bypass the type hint and create a
  dimensionless `BaseGeometry`.
- Accepted: add a runtime shape whitelist and hostile-string regression before commit.

Verification results:

- 2026-06-21: red step failed as expected: targeted tests reported 7 failures covering unsupported
  hull/custom shapes, manual hash audit fields, empty footprint blocking, footprint source refs,
  and terrain source-freshness/source-ref identity.
- 2026-06-21: after implementation, targeted
  `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q`
  passed: 28 passed.
- 2026-06-21: adversarial runtime-shape red step failed as expected:
  `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py::test_base_geometry_rejects_unknown_runtime_shape -q`
  reported that `BaseGeometry(shape="triangle")` did not raise.
- 2026-06-21: after the runtime whitelist fix, the hostile-shape regression passed: 1 passed.
- 2026-06-21: after the runtime whitelist fix, targeted
  `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q`
  passed: 29 passed.
- 2026-06-21: focused regression passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py tests\test_board_state.py tests\test_toolkit_contracts.py tests\test_los_toolkit.py tests\test_los_geometry.py tests\test_rendering_svg.py -q`
  returned 84 passed.
- 2026-06-21: after the runtime whitelist fix, focused regression passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py tests\test_board_state.py tests\test_toolkit_contracts.py tests\test_los_toolkit.py tests\test_los_geometry.py tests\test_rendering_svg.py -q`
  returned 85 passed.
- 2026-06-21: `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed:
  89 files already formatted.
- 2026-06-21: `.\.venv\Scripts\python.exe -m ruff check .` passed.
- 2026-06-21: `.\.venv\Scripts\mypy.exe src` passed: no issues in 62 source files.
- 2026-06-21: after the runtime whitelist fix, `.\.venv\Scripts\python.exe -m ruff format --check
  src tests`, `.\.venv\Scripts\python.exe -m ruff check .`, and `.\.venv\Scripts\mypy.exe src`
  all passed again.
- 2026-06-21: adversarial re-review `019ee971-f6db-7fc1-84bb-15c7ffdcdd14` approved the runtime
  shape whitelist fix with no critical or important findings. The reviewer independently ran the
  targeted Phase 3.5 tests and `git diff --check`.
- 2026-06-21: final targeted
  `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q`
  passed: 29 passed.
- 2026-06-21: final focused regression passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py tests\test_board_state.py tests\test_toolkit_contracts.py tests\test_los_toolkit.py tests\test_los_geometry.py tests\test_rendering_svg.py -q`
  returned 85 passed.
- 2026-06-21: final `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed:
  89 files already formatted.
- 2026-06-21: final `.\.venv\Scripts\python.exe -m ruff check .` passed.
- 2026-06-21: final `.\.venv\Scripts\mypy.exe src` passed: no issues in 62 source files.
- 2026-06-21: final full pytest passed: 243 passed, 1 known Starlette `TestClient`
  deprecation warning.
- 2026-06-21: final packet validation passed for all 45 official seed packets.
- 2026-06-21: final desktop smoke passed with status `ok`.
- 2026-06-21: final `git diff --check` passed with normal LF-to-CRLF warnings for touched files.
- 2026-06-21: first full pytest run timed out at 120 seconds before reporting a failure.
- 2026-06-21: full pytest rerun with a longer timeout passed: 242 passed, 1 known Starlette
  `TestClient` deprecation warning.
- 2026-06-21: packet validation passed for all 45 official seed packets.
- 2026-06-21: desktop smoke passed with status `ok`, 45 official packets, page 9 selected, and
  viewer/LOS/heatmap/hidden coverage SVG checks true.
- 2026-06-21: `git diff --check` passed with normal LF-to-CRLF warnings for touched files.

Browser and Computer Use:

- 2026-06-21: local web app was launched on `http://127.0.0.1:49231`. `Start-Process` was blocked
  by a Windows duplicate `Path`/`PATH` environment issue, and `C:\tmp` was not writable in this
  session. A detached Python process launched through the Node-backed helper and HTTP returned 200
  with title `Warhammer Tournament Companion`.
- 2026-06-21: Browser route sweep confirmed:
  - `/viewer`: `Map Viewer`, 1 form, 3 selects, 1 SVG, 16 terrain labels, no console errors.
  - `/heatmap`: `LOS Heatmap`, 1 form, 5 selects, 1 SVG, 1 embedded PNG, 16 terrain labels, no
    console errors.
  - `/los-checker`: `LOS Checker`, 1 form, 3 selects, 1 SVG, 1 embedded PNG, 16 terrain labels, no
    console errors.
  - `/hidden-coverage`: `Hidden Coverage`, 1 form, 4 selects, 1 SVG, 1 embedded PNG, 16 terrain
    labels, no console errors.
  - `/settings`: `Settings`, 2 forms, no console errors.
  - `/map-data`: `Map Data Management`, 46 forms, no console errors.
- 2026-06-21: Browser GET-form path checks confirmed:
  - `/viewer?layout_variant=B` selected Layout B and rendered 1 SVG with 16 terrain labels.
  - `/heatmap?layout_variant=B&zone_id=defender&source=interior&offset_inches=0` selected Layout B,
    Defender, Full deployment zone and rendered 1 SVG with 1 embedded PNG.
  - `/los-checker?layout_variant=B&x=30.5&y=24.0&base=1.57` preserved the submitted coordinates and
    base, rendered 1 SVG with 1 embedded PNG, and showed clear/blocked result text.
  - `/hidden-coverage?layout_variant=B&terrain_area_id=terrain-06&detection_range=15` selected
    Layout B, Terrain 6, and detection range 15; rendered 1 SVG, 1 embedded PNG, 16 terrain labels,
    and a 67,101-byte screenshot.

Remaining gate:

- Atomic commit remains before Phase 3.5 closeout.

## 2026-06-21 - Phase 4A - Roster Import Safety And Source Records

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Add a safe hostile-input boundary for synthetic `.ros` and `.rosz` roster-like data.
- Record local roster source provenance, hashes, archive member metadata, XML safety status, and a
  shallow canonical army snapshot.
- Do not implement profile resolution, official points, legality, roster UI, persistence, movement,
  threat, damage, mission, analytics, or AI behavior.

Artifacts:

- `docs/superpowers/specs/2026-06-21-roster-import-safety-and-source-records-spec.md`
- `docs/superpowers/plans/2026-06-21-roster-import-safety-and-source-records.md`
- `docs/superpowers/qa/2026-06-21-roster-import-safety-and-source-records-qa.md`
- `docs/superpowers/reviews/2026-06-21-phase-4a-consultant-roster-import.md`
- `docs/superpowers/reviews/2026-06-21-phase-4a-adversarial-roster-import.md`
- `src/warhammer_companion/domain/rosters.py`
- `src/warhammer_companion/ingestion/roster_archives.py`
- `src/warhammer_companion/ingestion/roster_xml.py`
- `src/warhammer_companion/application/roster_import.py`
- `tests/test_roster_import_safety.py`

Design decisions:

- Phase 4 is split. Phase 4A is quarantine/admission and shallow source records only.
- `.ros` and `.rosz` are supported first because BSData documentation describes `.ros` as XML and
  `.rosz` as a zip archive containing XML; `.cat`, `.catz`, `.gst`, `.gstz`, `.bsr`, pasted text,
  and community-pack refresh are deferred.
- `defusedxml` is not currently installed in the project venv. Phase 4A therefore uses an explicit
  fail-closed XML gate: only UTF-8/ASCII XML bytes are admitted, unsafe DTD/entity/include/URL
  tokens are rejected before parsing, XML byte size is limited, and selection nesting depth is
  bounded before recursive extraction.
- Domain and ingestion modules do not import `application.toolkit`; roster block reasons live in
  `domain.rosters` and are adapted to toolkit block reasons in `application.roster_import`.
- Safe imports are `estimated` local evidence. Unsafe imports are `blocked`. No import result can
  claim list legality, resolved profiles, official points, recommendations, or tactical safety.

Consultant review triage:

- Consultant reviewer `019ee97a-4ac5-7ca1-9a0e-2700a5bb0df2` approved the Phase 4A direction:
  split Phase 4, start with safe `.ros`/`.rosz`, place domain records under `domain`, hostile
  admission helpers under `ingestion`, and a thin builder under `application`.
- Consultant final reviewer `019ee985-63f6-7d42-9933-1011bfa5b87a` blocked the first implementation
  on UTF-16 XML safety bypass, missing XML depth enforcement, architecture inversion through
  domain/ingestion importing application `BlockReason`, and missing `CanonicalArmy.source_ref_ids`.
- Accepted: reject non-UTF-8/BOM XML before token scanning/parsing.
- Accepted: reject NUL-containing XML bytes before token scanning/parsing.
- Accepted: enforce selection depth before recursive extraction.
- Accepted: move roster block reasons into `domain.rosters` and convert them at the application
  boundary.
- Accepted: add source refs to `CanonicalArmy`.

Adversarial review triage:

- Adversarial reviewer `019ee97a-7851-7022-8617-8c6ecdd8845b` approved only quarantine/admission
  and blocked direct roster/profile implementation.
- Accepted: no profile resolution, MFM points, pasted text, UI, persistence, BoardState adapter, or
  downstream solver integration in Phase 4A.
- Accepted: archive tests must include traversal, absolute paths, nested archive, encrypted member,
  unexpected extension, member count, size, and decompression ratio.
- Accepted: XML tests must include malformed XML, DOCTYPE, entity references, XInclude, URL
  references, non-UTF-8 encoding bypasses, and excessive depth.
- Adversarial final reviewer `019ee985-9f64-7c80-afec-f67ac382f36d` blocked the first
  implementation on XML depth crash and path normalization bypasses such as `safe/../evil.ros` and
  `C:../evil.ros`.
- Accepted: check raw archive path components and colons before normalization.
- Accepted: add regressions for embedded traversal and Windows drive-qualified paths.
- Accepted: add XML depth regression.

Verification results:

- 2026-06-21: initial red step failed because `warhammer_companion.application.roster_import` did
  not exist.
- 2026-06-21: after initial implementation, targeted Phase 4A tests failed on the synthetic
  encrypted-member fixture; fixed the fixture by patching ZIP header flags directly.
- 2026-06-21: targeted Phase 4A tests then passed: 17 passed.
- 2026-06-21: focused regression passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_roster_import_safety.py tests\test_toolkit_contracts.py tests\test_rules_sources.py tests\test_base_sizes.py tests\test_terrain_semantics.py -q`
  returned 63 passed.
- 2026-06-21: static checks initially found new-file formatting, Ruff B008/default issues, line
  length issues, and mypy narrowing issues; all were fixed.
- 2026-06-21: adversarial path/depth red step failed as expected for `safe/../evil.ros`,
  `C:../evil.ros`, `C:evil.ros`, and excessive selection depth.
- 2026-06-21: after path/depth fixes, those four regressions passed.
- 2026-06-21: consultant UTF-16 red step failed as expected because UTF-16 `DOCTYPE` XML returned
  `estimated`.
- 2026-06-21: after XML encoding/domain-boundary/source-ref fixes, adversarial regressions passed:
  5 passed.
- 2026-06-21: after reviewer fixes, targeted Phase 4A tests passed: 22 passed.
- 2026-06-21: after reviewer fixes, focused regression passed: 68 passed.
- 2026-06-21: after reviewer fixes, `.\.venv\Scripts\python.exe -m ruff format --check src tests`
  passed: 94 files already formatted.
- 2026-06-21: after reviewer fixes, `.\.venv\Scripts\python.exe -m ruff check .` passed with a
  nonblocking Ruff cache-write warning.
- 2026-06-21: after reviewer fixes, `.\.venv\Scripts\mypy.exe src` passed: no issues in 66 source
  files.
- 2026-06-21: re-review found a remaining P1: UTF-16LE/BE XML without BOM could bypass the raw
  token scan. Added explicit no-BOM UTF-16LE/BE regressions.
- 2026-06-21: no-BOM UTF-16 red step failed as expected before the NUL-byte encoding gate fix.
- 2026-06-21: after the NUL-byte encoding gate fix, no-BOM UTF-16 regressions passed: 2 passed.
- 2026-06-21: after the NUL-byte encoding gate fix, targeted Phase 4A tests passed: 24 passed.
- 2026-06-21: after the NUL-byte encoding gate fix, focused regression passed: 70 passed.
- 2026-06-21: after the NUL-byte encoding gate fix, `.\.venv\Scripts\python.exe -m ruff format
  --check src tests`, `.\.venv\Scripts\python.exe -m ruff check .`, and
  `.\.venv\Scripts\mypy.exe src` passed.
- 2026-06-21: full pytest before reviewer fixes passed: 260 passed, 1 known Starlette
  `TestClient` deprecation warning. Full pytest must be rerun after final reviewer fixes before
  commit.
- 2026-06-21: packet validation before reviewer fixes passed for all 45 official seed packets.
- 2026-06-21: desktop smoke before reviewer fixes passed with status `ok`.
- 2026-06-21: follow-up adversarial reviews hardened `.rosz` admission against forged central
  sizes, corrupt payloads, unsupported compression, local/central path mismatches, encryption flag
  mismatches, compression mismatches, data descriptor ambiguity, hidden trailing deflate bytes,
  unsafe or payload-bearing directory entries, local/central extra fields, archive/member comments,
  unreferenced leading local entries, trailing bytes after EOCD, excessive directory entries, and
  ZIP layout gaps.
- 2026-06-21: follow-up adversarial reviews hardened XML admission against encoded URL schemes in
  decoded attributes, namespaces, unused namespace declarations, comments, and processing
  instructions.
- 2026-06-21: final consultant reviewer `019ee99a-5ac5-7181-b9db-e96ef20076f9` approved Phase 4A
  scope and implementation after documentation closeout.
- 2026-06-21: final adversarial reviewer `019ee9ce-7261-7b23-8305-c58cf0beb084` approved Phase 4A
  with no open critical, important, or minor findings.
- 2026-06-21: final focused Phase 4A tests passed: 49 passed.
- 2026-06-21: final focused regression pack passed: 95 passed.
- 2026-06-21: final focused `ruff format --check src tests`, `ruff check .`, and `mypy src`
  passed.
- 2026-06-21: final full pytest passed: 292 passed, 1 known Starlette `TestClient`
  deprecation warning.
- 2026-06-21: final packet validation passed for all 45 bundled official seed packets.
- 2026-06-21: final desktop smoke passed with status `ok`, 45 packets, viewer SVG, LOS SVG,
  heatmap SVG, and hidden coverage SVG.
- 2026-06-21: final Browser route sweep passed for `/viewer`, `/heatmap`, `/los-checker`,
  `/hidden-coverage`, `/settings`, `/map-data`, and Layout B/query smoke routes. Map pages
  rendered expected SVGs, raster pages rendered embedded PNG overlays, and no browser console
  warnings or errors were captured.
- 2026-06-21: `git diff --check` passed with only the known LF-to-CRLF work-log warning.

Closeout:

- 2026-06-21: Phase 4A protected-artifact scan passed before staging.
- 2026-06-21: Phase 4A committed as `16a3884 Add roster import safety records`.
- 2026-06-21: `AGENTS.md` remained unstaged because it is a user-provided repository instruction
  file.

## 2026-06-21 - Phase 4B - Roster Canonical Index And Snapshot Profiles

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Add deterministic canonical roster indexes over accepted synthetic `.ros`/`.rosz` imports.
- Preserve embedded roster profiles, characteristics, and rules as local unresolved snapshot
  candidates for later profile resolution.
- Keep roster snapshot data `estimated` and explicitly non-authoritative.
- Do not implement profile resolution, official points, legality, UI, persistence, BoardState
  adapter, movement, threat, damage, mission, analytics, or AI companion behavior.

Artifacts:

- `docs/superpowers/specs/2026-06-21-roster-canonical-index-and-snapshot-profiles-spec.md`
- `docs/superpowers/plans/2026-06-21-roster-canonical-index-and-snapshot-profiles.md`
- `docs/superpowers/qa/2026-06-21-roster-canonical-index-and-snapshot-profiles-qa.md`
- `docs/superpowers/reviews/2026-06-21-phase-4b-consultant-roster-candidates.md`
- `docs/superpowers/reviews/2026-06-21-phase-4b-adversarial-roster-candidates.md`
- `src/warhammer_companion/domain/rosters.py`
- `src/warhammer_companion/ingestion/roster_xml.py`
- `src/warhammer_companion/application/roster_import.py`
- `tests/test_roster_snapshot_profiles.py`

Design decisions:

- Phase 4B remains an evidence/indexing slice, not a profile-resolution or points-authority slice.
- Snapshot rule descriptions are represented only by SHA-256 and length.
- Short characteristic values are retained as local evidence; long characteristic values are
  represented only by SHA-256 and length.
- Candidate records carry record-level `local_evidence`, `unresolved`, `not_official_points`, and
  `not_profile_resolution` markers.
- Stable roster selection keys include sibling ordinals so duplicate raw IDs do not collide.
- Multi-force and zero-force roster XML are explicitly blocked until force-aware indexing is
  designed, avoiding silent discard of later forces.
- XML admission now includes whole-document element/depth/attribute/text limits and
  profile/rule/characteristic count limits before snapshot extraction.

Consultant review triage:

- Consultant reviewer `019eeaad-e35e-7a20-9079-b5ed81f58a30` approved the Phase 4B direction if it
  stays evidence/indexing only.
- Accepted: write a fine-grain Phase 4B spec/plan/QA path before implementation.
- Accepted: add stable keys separate from raw BattleScribe IDs.
- Accepted: define extraction limits before implementation.
- Accepted: keep roster snapshot extraction out of base-size records, BoardState, UI, persistence,
  and solver code.

Adversarial review triage:

- Adversarial reviewer `019eeaae-0dbc-7ba1-94b1-e510635af8e0` initially failed the proposal until
  the Phase 4B contract and guardrails were tightened.
- Accepted: add Phase 4B docs before code.
- Accepted: block unsupported force counts instead of silently indexing only the first force.
- Accepted: minimize text-bearing snapshot records.
- Accepted: add whole-document structural XML limits.
- Accepted: add record-level no-authority markers.

Verification results:

- 2026-06-21: red step confirmed Phase 4B tests failed before implementation:
  `.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_profiles.py -q` returned
  10 failures for missing index/profile-pack fields and unsupported-shape/structure guards.
- 2026-06-21: after implementation, targeted Phase 4B tests passed: 10 passed.
- 2026-06-21: combined Phase 4A/4B roster tests passed: 59 passed.
- 2026-06-21: focused regression passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py tests\test_toolkit_contracts.py tests\test_rules_sources.py tests\test_base_sizes.py tests\test_terrain_semantics.py -q`
  returned 105 passed.
- 2026-06-21: `ruff format --check src tests`, `ruff check .`, and `mypy src` passed after an
  import-sort auto-fix.
- 2026-06-21: implementation adversarial review `019eeab9-9805-7c13-a4ca-a998cbd25d89` found
  aggregate `itertext()` could bypass the text cap and nested characteristics lacked source refs.
- 2026-06-21: review-fix red step failed as expected: targeted Phase 4B tests reported 2 failures
  for characteristic provenance and fragmented rule-description text.
- 2026-06-21: after review fixes, targeted Phase 4B tests passed: 11 passed.
- 2026-06-21: after review fixes, focused regression passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py tests\test_toolkit_contracts.py tests\test_rules_sources.py tests\test_base_sizes.py tests\test_terrain_semantics.py -q`
  returned 106 passed.
- 2026-06-21: after review fixes, `ruff format --check src tests`, `ruff check .`, and
  `mypy src` passed. One Ruff check attempt hit a transient sandbox ACL error and passed on rerun.
- 2026-06-21: final adversarial re-review `019eeabe-fc0d-7f22-b3e9-bf4fcab4d0a4` found the
  exposed `payload.army` tree still missed nested source refs.
- 2026-06-21: second review-fix red step failed as expected: targeted Phase 4B tests reported the
  missing source refs on `payload.army.selections[0].profiles[0]`.
- 2026-06-21: after the deep army-source-ref fix, targeted Phase 4B tests passed: 11 passed.
- 2026-06-21: after the deep army-source-ref fix, focused regression passed: 106 passed.
- 2026-06-21: after the deep army-source-ref fix, `ruff format --check src tests`,
  `ruff check .`, and `mypy src` passed.
- 2026-06-21: final approval reviewer `019eeac5-197c-7000-900c-784ebf63468e` requested two
  test-only gaps: fragmented aggregate characteristic text and nested child source-ref assertions.
- 2026-06-21: after adding those regressions, targeted Phase 4B tests passed: 12 passed.
- 2026-06-21: after adding those regressions, focused regression passed: 107 passed.
- 2026-06-21: after adding those regressions, `ruff format --check src tests`, `ruff check .`, and
  `mypy src` passed.
- 2026-06-21: final full pytest passed: 304 passed, 1 known Starlette `TestClient` deprecation
  warning.
- 2026-06-21: final packet validation passed for all 45 bundled official seed packets.
- 2026-06-21: final desktop smoke passed with status `ok`, 45 packets, viewer SVG, LOS SVG,
  heatmap SVG, and hidden coverage SVG.
- 2026-06-21: final `git diff --check` passed with only normal LF-to-CRLF warnings for touched
  files.
- 2026-06-21: Browser QA launched the local app through a detached Node child process because
  Windows PowerShell `Start-Process` failed on duplicated `Path`/`PATH` environment keys. Browser
  route sweep passed for `/viewer`, `/settings`, `/map-data`, `/heatmap`, `/los-checker`,
  `/hidden-coverage`, and Layout B/query smoke routes. Map pages rendered expected SVGs, raster
  pages rendered embedded PNG overlays, submitted query values were preserved, and no browser
  console warnings or errors were captured. The temporary server was stopped after QA.
- 2026-06-21: protected-artifact scan passed; no raw roster/archive/PDF/db/log/image/generated-data
  paths or protected profile/rule text were present in the Phase 4B staged candidate set.
- 2026-06-21: final adversarial reviewer `019eead0-337e-7732-8778-2124147c562b` approved Phase 4B
  with no open critical, important, or minor findings.

Closeout:

- 2026-06-21: Phase 4B committed as `c089240 Add roster snapshot profile candidates`.
- 2026-06-21: `AGENTS.md` remained unstaged because it is a user-provided repository instruction
  file.

## 2026-06-21 - Phase 4.5 - Roster Snapshot Housekeeping

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Keep the Phase 4 roster adapter foundation maintainable before Phase 5 movement reach work.
- Extract pure roster index/source-ref/snapshot profile-pack builders from the byte-admission
  service into a focused application module.
- Keep the slice behavior-preserving and avoid new roster authority, profile resolution, official
  points, UI, persistence, BoardState, movement, threat, damage, mission, analytics, or AI behavior.

Artifacts:

- `docs/superpowers/specs/2026-06-21-phase-4-5-roster-snapshot-housekeeping.md`
- `docs/superpowers/plans/2026-06-21-phase-4-5-roster-snapshot-housekeeping.md`
- `docs/superpowers/qa/2026-06-21-phase-4-5-roster-snapshot-housekeeping-qa.md`
- `docs/superpowers/reviews/2026-06-21-phase-4-5-consultant-roster-snapshot-housekeeping.md`
- `docs/superpowers/reviews/2026-06-21-phase-4-5-adversarial-roster-snapshot-housekeeping.md`
- `src/warhammer_companion/application/roster_snapshots.py`
- `src/warhammer_companion/application/roster_import.py`
- `tests/test_roster_snapshot_builders.py`

Design decisions:

- The extracted module lives under `application` because it assembles source-ready application
  payload projections and hashes rather than defining new durable domain records.
- `build_roster_import_result_from_bytes(...)` remains the only roster byte-admission entrypoint.
- `domain.rosters`, `ingestion.roster_xml`, and `ingestion.roster_archives` are intentionally
  unchanged.
- The public helper API is limited to canonical source-ref propagation, canonical roster index
  construction, and roster snapshot profile candidate pack construction.
- Phase 4B hash/key semantics and local-evidence authority markers must remain stable.

Consultant review triage:

- Consultant reviewer `019eebac-62b1-7983-adbd-0ac8ac4d44ee` approved the extraction as the right
  Phase 4.5 target before Phase 5.
- Accepted: keep `build_roster_import_result_from_bytes(...)` behavior and payload shape identical.
- Accepted: make the new module pure and avoid archive inspection, XML parsing, filesystem, UI,
  persistence, BoardState, profile resolution, official points, and solver imports.
- Accepted: direct tests must cover duplicate selection keys, parent/depth/source paths, deep
  source-ref propagation, snapshot hash sensitivity, and no retained rule-description text.

Adversarial review triage:

- Adversarial reviewer `019eebac-9415-7510-ae38-42e0e1b2767d` approved only as a narrow
  behavior-preserving extraction.
- Accepted: do not change selection-key, ordinal-path, duplicate-ID, source-ref normalization, or
  snapshot pack hash semantics.
- Accepted: preserve unresolved/local/non-authoritative candidate markers.
- Accepted: keep rule descriptions hash/length only and keep ingestion safety logic out of the new
  module.
- Accepted: run an import-boundary check proving `domain` and `ingestion` do not import
  `application.roster_snapshots`.

Verification results:

- 2026-06-21: red step confirmed Phase 4.5 direct builder tests failed before implementation
  because `warhammer_companion.application.roster_snapshots` did not exist.
- 2026-06-21: after extraction, direct builder tests passed: 4 passed.
- 2026-06-21: roster regression passed:
  `tests\test_roster_snapshot_builders.py tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py`
  returned 65 passed.
- 2026-06-21: broader focused regression passed:
  `tests\test_roster_snapshot_builders.py tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py tests\test_toolkit_contracts.py tests\test_rules_sources.py tests\test_base_sizes.py tests\test_terrain_semantics.py`
  returned 111 passed.
- 2026-06-21: import-boundary scan found no `domain` or `ingestion` imports of
  `application.roster_snapshots`.
- 2026-06-21: initial static checks found only Ruff formatting/import-order drift in
  `application.roster_import`; after formatting, `ruff format --check src tests`,
  `ruff check .`, and `mypy src` passed.
- 2026-06-21: implementation spec reviewer `019eebb1-ff3d-7742-8b76-2f7e64e35eb4` approved the
  extraction with no spec-compliance findings.
- 2026-06-21: implementation adversarial reviewer `019eebb2-3146-7530-9614-267372618b96` approved
  with no critical or important findings and one minor test-hardening suggestion.
- 2026-06-21: accepted the minor suggestion and added a direct test proving snapshot pack hashes
  normalize source refs while exposed `source_ref_ids` preserve the original tuple.
- 2026-06-21: after the test hardening, roster regression passed:
  `tests\test_roster_snapshot_builders.py tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py`
  returned 66 passed.
- 2026-06-21: after the test hardening, `ruff format --check src tests`, `ruff check .`,
  `mypy src`, and `git diff --check` passed. `git diff --check` reported only normal LF-to-CRLF
  warnings for touched files.
- 2026-06-21: final full pytest passed: 309 passed, 1 known Starlette `TestClient` deprecation
  warning.
- 2026-06-21: final packet validation passed for all 45 bundled official seed packets.
- 2026-06-21: final desktop smoke passed with status `ok`, 45 packets, viewer SVG, LOS SVG,
  heatmap SVG, and hidden coverage SVG.
- 2026-06-21: final `git diff --check` passed with only normal LF-to-CRLF warnings for touched
  files.
- 2026-06-21: Browser QA launched the local app on `http://127.0.0.1:8000`. The first Browser
  route sweep hit a navigation timeout, but the tab remained healthy and landed on the requested
  route. A recovered route sweep passed for `/viewer`, `/settings`, `/map-data`, `/heatmap`,
  `/los-checker`, `/hidden-coverage`, and Layout B/query smoke routes. Map pages rendered expected
  SVGs, raster pages rendered embedded PNG overlays, submitted query values were preserved, and no
  browser console warnings or errors were captured.
- 2026-06-21: protected-artifact path scan passed; no raw roster/archive/PDF/db/log/image/generated
  data paths were present in the Phase 4.5 candidate file set. `AGENTS.md` remained untracked and
  excluded.

Closeout:

- 2026-06-21: Phase 4.5 committed as `11bd4cd Housekeep roster snapshot builders`.
- 2026-06-21: `AGENTS.md` remained unstaged because it is a user-provided repository instruction
  file.

## 2026-06-21 - Phase 5 - Movement Reach Toolkit

Branch: `codex/assistant-companion-roadmap`

Purpose:

- Add the first deterministic player tool beyond LOS.
- Provide a manual single-model circular-base 2D movement reach diagnostic before roster/profile
  import is complete.
- Surface board-edge, dense-feature, and straight-line swept-base endpoint diagnostics without
  claiming exact rules-legal movement.

Artifacts:

- `docs/superpowers/specs/2026-06-21-movement-reach-toolkit-spec.md`
- `docs/superpowers/plans/2026-06-21-movement-reach-toolkit.md`
- `docs/superpowers/qa/2026-06-21-movement-reach-toolkit-qa.md`
- `docs/superpowers/reviews/2026-06-21-phase-5-consultant-movement-reach.md`
- `docs/superpowers/reviews/2026-06-21-phase-5-adversarial-movement-reach.md`

Design decisions:

- Phase 5 is manual-input first: start point, target point, base diameter, movement distance, and
  movement mode label.
- Results are single-model circular-base geometric estimates, not exact movement legality.
- Dense features are treated as 2D movement blockers in this estimate, matching the current MVP
  terrain assumption until source-backed movement traits exist.
- The movement-envelope overlay is an endpoint estimate. The selected endpoint diagnostic separately
  checks board edge, distance, and straight-line swept-base collision.
- Move modes are labels for the operator-entered distance in this slice. Dice, modifiers, rerolls,
  reserves, transports, vertical movement, and source-backed mode legality are deferred.
- Coherency, multi-model collision, enemy/friendly collision, non-round base orientation, objective
  and action markers, exposure summaries, and pathfinding around obstacles are explicitly deferred.
- Web and desktop surfaces should remain thin adapters over `WarhammerCompanionService`.

Consultant review triage:

- Geometry consultant `019eebbe-579b-7631-9786-69efc5050571` approved if the tool remains an
  estimated 2D movement reach diagnostic, not endpoint legality.
- UI consultant `019eebbe-8fb8-7050-bb2c-5a6c1867063e` approved adding web and desktop surfaces
  after the service/result layer, as thin adapters only.
- Accepted: use `los/movement.py`, a toolkit builder, service state, and thin web/desktop surfaces.
- Accepted: avoid legal, safe, recommended, optimal, likely, and guaranteed wording.

Adversarial review triage:

- Adversarial reviewer `019eebbe-bd44-7e60-b0a0-aa6a30cedc19` conditionally approved only after
  narrowing to a diagnostic single-model, manual, circular-base, 2D straight-corridor estimate.
- Accepted: cut coherency, multi-model collision, enemy/friendly collision, non-round base support,
  objective/action markers, exposure summaries, pathfinding around obstacles, and later-phase
  mechanics.
- Accepted: valid manual round-base results are `estimated`; invalid base/movement inputs are
  `blocked` with no overlays.

Review gates:

- Consultant reviewers must approve movement geometry/service scope and UI adapter scope.
- Adversarial reviewer must approve false-precision guardrails, source/readiness boundaries, and
  scope cuts before implementation.

TDD and implementation results:

- Red step: focused movement geometry/toolkit tests failed on missing
  `warhammer_companion.los.movement` and `warhammer_companion.application.movement_reach`.
- Green step: movement geometry/toolkit tests passed after adding typed movement domain records,
  geometry helpers, and the `movement_reach` toolkit result builder.
- Integration step: service, rendering, web, and desktop adapter tests failed first on missing
  state/route/rendering/smoke contracts, then passed after adding shared service state, SVG
  projection, server-rendered web controls, and a PySide6 desktop screen.

Implementation review results:

- Spec-compliance reviewer `019eebcf-f3ca-79f0-b9c0-79bd8928978c` found no movement-code or
  overclaim-language blocker, then blocked on this stale log section.
- Adversarial implementation reviewer `019eebd0-76c3-72c1-9309-4259ece613b8` initially blocked on
  Ruff, mypy, and broad "geometric blocker" wording. The fixes were applied and the reviewer
  approved the current diff.

Verification completed:

- `.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_movement_reach_toolkit.py -q`
  passed: 9 tests.
- `.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_movement_reach_toolkit.py tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q`
  passed: 53 tests, with the existing Starlette `httpx` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- `.\.venv\Scripts\python.exe -m pytest` passed: 323 tests, with the existing Starlette `httpx`
  deprecation warning.
- `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets`
  passed: all 45 bundled official seed packets valid.
- `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test` passed with
  `movement_reach_svg: true`.
- `git diff --check` reported no whitespace errors; Git printed line-ending normalization warnings.
- Protected changed-path scan found no blocked generated/raw artifact paths; `AGENTS.md` remains
  untracked and unstaged.
- Built-in Browser QA passed for `/movement-reach`, the Layout B query path, `/viewer`,
  `/heatmap`, `/los-checker`, `/hidden-coverage`, `/settings`, and `/map-data`, with no console
  warnings or errors. The movement page rendered one map SVG and one movement-envelope raster,
  preserved manual query inputs, showed "Estimated 2D geometry" wording, and avoided legal, safe,
  recommended, optimal, likely, and guaranteed wording.

Remaining blocker status:

- No validation blocker remains at commit preparation time. Atomic commit follows this log entry.

## 2026-06-21 - Phase 5.5 - Movement Reach Housekeeping

Branch: `codex/assistant-companion-roadmap`

Commit: pending

Goal:

- Run a behavior-preserving housekeeping slice after Movement Reach and before Phase 6 Threat
  Range.
- Reduce helper duplication without changing movement reach, LOS, web, desktop, renderer semantics,
  route parameters, or source authority.

Artifacts:

- `docs/superpowers/specs/2026-06-21-phase-5-5-movement-housekeeping.md`
- `docs/superpowers/plans/2026-06-21-phase-5-5-movement-housekeeping.md`
- `docs/superpowers/qa/2026-06-21-phase-5-5-movement-housekeeping-qa.md`
- `docs/superpowers/reviews/2026-06-21-phase-5-5-consultant-movement-housekeeping.md`
- `docs/superpowers/reviews/2026-06-21-phase-5-5-adversarial-movement-housekeeping.md`

Changes:

- Added `double_spin_box(...)` in `desktop/screens/common.py`.
- Replaced the duplicate private `_spin_box(...)` helpers in LOS Checker and Movement Reach desktop
  screens.
- Made `_render_coverage_raster(...)` delegate to the existing binary `_render_geometry_raster(...)`
  helper with the same `coverage-image` CSS class and `(42, 140, 158, 118)` RGBA value.
- Added decoded PNG tests that lock representative raster semantics for `coverage-image`,
  `movement-envelope-image`, `hidden-coverage-image`, and `heatmap-image`.

Review results:

- Consultant reviewer `019eebe6-ce37-7130-9723-f8389d72930a` approved the narrow helper/raster
  cleanup and rejected broader `render_map_svg(...)` API redesign before Phase 6.
- Adversarial scope reviewer `019eebe6-f9c7-7e33-8da3-fe5a5bc4133e` approved with constraints:
  share raster plumbing only, preserve overlay-specific semantics/classes/order, keep legacy cell
  fallbacks, and avoid web/desktop behavior changes.
- Adversarial implementation reviewer `019eebf1-b1c5-7ca0-a222-f171e39777b0` found no code blocker
  and blocked only on this missing work-log entry.

TDD and verification:

- Red step: `.\.venv\Scripts\python.exe -m pytest tests\test_desktop_screen_helpers.py -q`
  failed because `double_spin_box` did not exist.
- Raster semantic-lock tests in `tests/test_rendering_svg.py` passed before the raster refactor,
  proving they captured existing behavior.
- After implementation, `.\.venv\Scripts\python.exe -m pytest tests\test_desktop_screen_helpers.py tests\test_desktop_app.py -q`
  passed: 12 tests.
- `.\.venv\Scripts\python.exe -m pytest tests\test_rendering_svg.py -q` passed after the refactor.
- Targeted regression passed: `.\.venv\Scripts\python.exe -m pytest tests\test_rendering_svg.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py tests\test_desktop_screen_helpers.py tests\test_los_geometry.py tests\test_movement_reach_geometry.py -q`
  returned 88 passed with the existing Starlette `httpx` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed.
- `.\.venv\Scripts\python.exe -m ruff check .` passed after import sorting.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 328 tests, with the existing Starlette
  `httpx` deprecation warning.
- `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test` passed with
  `los_svg: true`, `movement_reach_svg: true`, and `viewer_svg: true`.
- `git diff --check` reported no whitespace errors; Git printed line-ending normalization warnings.
- Protected changed-path scan found no blocked generated/raw artifact paths; `AGENTS.md` remains
  untracked and unstaged.

Browser QA:

- Built-in Browser verified `/viewer`, `/heatmap`, `/los-checker`, `/hidden-coverage`,
  `/movement-reach`, `/movement-reach?layout_variant=B&start_x=12&start_y=12&target_x=18&target_y=18&base=1.57&move=6&mode=normal`,
  and `/heatmap?player_a=Priority%20Assets&player_b=Priority%20Assets&layout_variant=B`.
- All checked pages rendered one SVG map where applicable, contained no script tags, and produced no
  console warnings or errors.
- Overlay-specific image classes remained present: `heatmap-image`, `coverage-image`,
  `hidden-coverage-image`, and `movement-envelope-image`.
- The default `/heatmap` navigation surfaced the known Browser navigation-timeout quirk, but the
  page state after recovery showed `LOS Heatmap`, one SVG map, and one `heatmap-image`.

Remaining blocker status:

- Awaiting implementation reviewer re-check after this log update, then atomic commit.

## 2026-06-22 - Phase 6 - Threat Range Toolkit

Branch: `codex/assistant-companion-roadmap`

Commit: pending

Purpose:

- Add the first manual threat-range diagnostic slice before source-backed rules mechanics, roster
  profiles, damage, mission analytics, and AI companion behavior are implemented.
- Provide deterministic exact D6/2D6 probability-band geometry for one circular source base using
  manual move/range inputs.
- Keep results explicitly `estimated` and non-recommending.

Artifacts:

- `docs/superpowers/specs/2026-06-21-threat-range-toolkit-spec.md`
- `docs/superpowers/plans/2026-06-21-threat-range-toolkit.md`
- `docs/superpowers/qa/2026-06-21-threat-range-toolkit-qa.md`
- `docs/superpowers/reviews/2026-06-21-phase-6-consultant-threat-range.md`
- `docs/superpowers/reviews/2026-06-21-phase-6-adversarial-threat-range.md`
- `src/warhammer_companion/domain/threat.py`
- `src/warhammer_companion/los/threat.py`
- `src/warhammer_companion/application/threat_range.py`
- service, renderer, web, desktop, and test adapter updates for `/threat-range`.

Design decisions:

- Phase 6 is rosterless and manual-input only.
- Measurement convention is `source-base-edge-to-target-point`. The source base radius is included
  in reach budgets and rendered geometry; target base radius and official engagement/targeting
  semantics are not modeled.
- Movement-enabled threat modes reuse Phase 5 `movement_envelope(...)` behavior and then buffer the
  reachable source-center region by source base radius plus threat range.
- `raw-range` is current source center buffered by source base radius plus threat range.
- Movement distance and threat range may be zero; base diameter must be positive. Non-finite values
  and negative move/threat values block the result with no overlays.
- Dice modes are exact enumerations: D6 outcomes `1..6`, 2D6 outcomes `2..12`, no rerolls,
  modifiers, CP, stratagems, transports, reserves, actions, target-base logic, LOS, or damage.
- The SVG renderer accumulates probability-weighted threat regions into one embedded PNG raster.
  Deterministic modes are binary; dice modes produce probability bands.
- Web and desktop surfaces remain thin adapters over `WarhammerCompanionService`; no custom
  frontend JavaScript was added.

Consultant and adversarial triage:

- Phase 6 design consultant approved the manual probability-band slice and recommended exact dice
  enumeration, target-point diagnostics, and raster probability bands.
- Phase 6 adversarial design reviewer conditionally approved only if the slice stayed estimated,
  deterministic, manual, and non-recommending.
- Implementation consultant initially blocked on stale desktop wiring, measurement/spec mismatch,
  warning visibility, zero-value validation drift, shallow renderer coverage, missing POST coverage,
  and missing QA evidence.
- Accepted fixes: desktop screen/nav/smoke wiring, spec alignment to
  `source-base-edge-to-target-point`, visible source-backed/no-recommendation warnings, nonnegative
  move/threat contract, decoded raster dimension/alpha coverage, POST redirect test coverage, and
  this QA evidence record.
- Final adversarial implementation reviewer found four blockers: zero fixed-move threat paths
  crashed via `movement_envelope(...)`; source bases could overhang the board; invalid modes shared
  the same input hash as valid `raw-range`; and desktop omitted warning text.
- Accepted fixes: stationary fixed-move threat paths now render as source-stationary regions,
  toolkit validation blocks overhanging source bases, input identity hashes the submitted mode
  string, and desktop status includes the toolkit warning details.

TDD and implementation results:

- Red step: threat geometry/toolkit tests initially failed on missing
  `warhammer_companion.los.threat` and `warhammer_companion.application.threat_range`.
- Green step: geometry/toolkit tests passed after adding typed threat domain records, exact dice
  distributions, threat-region geometry helpers, threshold/target probability helpers, and the
  `threat_range` toolkit result builder.
- Integration red step: service/rendering/web/desktop tests failed on missing renderer arguments,
  `/threat-range` route/template, and desktop `Threat Range` screen/smoke summary.
- Green step: those tests passed after adding shared service state, SVG threat probability raster,
  server-rendered web controls/table/warnings, and a PySide6 desktop screen.
- Review-fix red step: warning and POST-preservation tests failed before warning plumbing and route
  coverage were added, then passed after fixes.
- Adversarial-fix red step: tests for zero fixed movement, source-base overhang, invalid-mode hash
  collision, and desktop warning visibility failed first and then passed after fixes.

Verification completed:

- Focused warning/POST/raster regression passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_toolkit.py::test_threat_range_toolkit_result_is_estimated_and_non_recommending tests\test_web_server.py::test_threat_range_route_uses_manual_probability_controls_and_cautious_language tests\test_web_server.py::test_threat_range_post_redirect_preserves_manual_values tests\test_rendering_svg.py::test_threat_projection_renders_probability_raster_and_markers -q`
  returned 4 passed.
- Phase 6 target suite passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py tests\test_threat_range_toolkit.py tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 65 passed with the existing Starlette `TestClient` deprecation warning after the final
  adversarial fixes.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 110 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 342 passed with the existing Starlette
  `TestClient` deprecation warning before the final adversarial fixes; after those fixes, full
  pytest passed again with 345 passed and the same warning.
- Packet validation passed for all 45 bundled official seed packets.
- Desktop smoke passed with `status: ok`, 45 packets, and `threat_range_svg: true`.
- `git diff --check` passed; Git printed only normal LF-to-CRLF warnings for touched files.
- Restricted protected-path scan over the Phase 6 candidate file set passed: no blocked
  generated/raw/binary paths and no credential-pattern hits. `AGENTS.md` remained untracked and
  excluded from staging.

Browser QA:

- `Start-Process` background launch hit the known Windows `Path`/`PATH` duplication issue, so the
  local app was launched through a detached child process on `http://127.0.0.1:8000`.
- Built-in Browser route sweep passed for `/threat-range`, the 2D6 query path,
  `/movement-reach`, `/los-checker`, `/viewer`, `/heatmap`, `/hidden-coverage`, `/settings`, and
  `/map-data`.
- Default `/threat-range` rendered one SVG map, one `threat-projection-image`, source and target
  markers, no `<script>` tags, visible estimated/caution warnings, and no console warnings/errors.
- The 2D6 query path preserved source, target, base, move, threat, mode, and Layout B values. It
  rendered all 2D6 rows and showed `100.0%` target point probability for the selected coordinates.
- Existing smoke routes rendered their expected SVG/raster surfaces with no console warnings/errors.
- After final adversarial fixes, Browser QA was rerun. `/threat-range`, the 2D6 query path,
  `/movement-reach`, `/los-checker`, `/viewer`, `/hidden-coverage`, `/settings`, and `/map-data`
  had no navigation errors, missing text, scripts, forbidden estimated-result wording, or console
  warnings/errors. `/heatmap` repeated the known Browser navigation timeout, but the resulting tab
  state reached `/heatmap`, rendered one SVG and one `heatmap-image`, and had no warning/error logs.
- The temporary QA process was terminated after Browser QA.

Remaining blocker status:

- Final Phase 6 consultant and adversarial implementation reviewers approved before staging and
  atomic commit.

## Phase 6.5 - Threat Board Geometry Housekeeping

Purpose:

- Keep momentum between Phase 6 and Phase 7 with a behavior-preserving cleanup slice.
- Remove duplicated circular-base board-fit geometry between movement reach and threat range.
- Preserve movement envelopes, threat projections, web routes, desktop screens, source/readiness
  wording, and generated data exactly.

Artifacts:

- `docs/superpowers/specs/2026-06-22-phase-6-5-threat-housekeeping.md`
- `docs/superpowers/plans/2026-06-22-phase-6-5-threat-housekeeping.md`
- `docs/superpowers/qa/2026-06-22-phase-6-5-threat-housekeeping-qa.md`
- `docs/superpowers/reviews/2026-06-22-phase-6-5-consultant-threat-housekeeping.md`
- `docs/superpowers/reviews/2026-06-22-phase-6-5-adversarial-threat-housekeeping.md`
- `src/warhammer_companion/los/movement.py`
- `src/warhammer_companion/application/threat_range.py`
- `tests/test_movement_reach_geometry.py`

Design decisions:

- The shared helper is `base_center_region(packet, base_radius)` in `los/movement.py`, because it
  is reusable LOS/movement geometry rather than application policy.
- Threat range validation remains in `application/threat_range.py`; it now asks the shared helper
  whether the source center can keep the circular base inside the board and turns that geometry fact
  into `source-base-outside-board` when needed.
- Oversized-base behavior is intentionally unchanged: if a base radius exceeds the board half-size,
  the center region collapses to the board center under the existing helper math.
- No route, template, CSS, desktop, rendering, source-ingestion, roster, damage, mission, analytics,
  or recommendation behavior changed.

TDD and review:

- Red step: `tests/test_movement_reach_geometry.py` imported `base_center_region(...)` before the
  helper existed and failed with the expected import error.
- Consultant review approved the scope and requested a direct negative-radius guard test; that test
  was added before production code.
- Green step: `_board_center_region(...)` was renamed to `base_center_region(...)`, movement callers
  were updated, and threat validation reused the shared helper instead of local `box(...)` math.
- Initial adversarial review requested changes because `threat_range.py` import order failed Ruff.
  The import order was fixed and the adversarial reviewer re-approved.

Verification completed:

- Focused red/green suite passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_threat_range_toolkit.py -q`
  returned 13 passed.
- Broader app/web/desktop batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_threat_range_geometry.py tests\test_desktop_app.py tests\test_web_server.py -q`
  returned 45 passed with the existing Starlette `TestClient` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 110 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 348 passed with the existing Starlette
  `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok`, `movement_reach_svg: true`, and `threat_range_svg: true`.
- `git diff --check` passed; Git printed only normal LF-to-CRLF warnings for touched files.

Browser QA:

- Even though Phase 6.5 touched only shared helper/application validation code, the local app was
  launched on `http://127.0.0.1:8000` and the built-in Browser inspected `/movement-reach` and
  `/threat-range`.
- `/movement-reach` rendered one SVG, one `movement-envelope-image`, one form, zero `<script>` tags,
  no traceback/error text, and no warning/error console logs.
- `/threat-range` rendered one SVG, one `threat-projection-image`, one form, zero `<script>` tags,
  no traceback/error text, and no warning/error console logs.
- The temporary QA server process was terminated after Browser QA.

Remaining blocker status:

- Phase 6.5 consultant and adversarial reviewers approved. No blockers remain.

## Phase 7 - Deployment Exposure Toolkit

Purpose:

- Add the first deployment-position diagnostic slice without building a placement optimizer or
  source-backed legal placement planner.
- Let a player enter one friendly circular base, one enemy source base, enemy threat assumptions,
  a deployment zone, and an exposure mode.
- Render candidate staging centers, enemy threat, enemy LOS, the friendly base, and the enemy source
  base through the shared service layer for both web and desktop surfaces.

Artifacts:

- `docs/superpowers/specs/2026-06-22-deployment-exposure-toolkit-spec.md`
- `docs/superpowers/plans/2026-06-22-deployment-exposure-toolkit.md`
- `docs/superpowers/qa/2026-06-22-deployment-exposure-toolkit-qa.md`
- `docs/superpowers/reviews/2026-06-22-phase-7-consultant-deployment-exposure.md`
- `docs/superpowers/reviews/2026-06-22-phase-7-adversarial-deployment-exposure.md`
- `src/warhammer_companion/domain/exposure.py`
- `src/warhammer_companion/los/exposure.py`
- `src/warhammer_companion/application/deployment_exposure.py`
- `src/warhammer_companion/web/templates/deployment_exposure.html`
- `src/warhammer_companion/desktop/screens/deployment_exposure.py`

Design decisions:

- Product-facing naming is "Deployment Exposure" rather than a safe or legal placement planner.
- Readiness remains `estimated` for valid manual assumptions and `blocked` for invalid manual
  inputs.
- Candidate staging centers are deployment-center diagnostics constrained by smoothed deployment
  geometry, board fit, dense-feature collision estimates, and selected threat/LOS risk.
- Visible copy avoids `legal`, `safe`, `recommended`, `optimal`, `likely`, and `guaranteed`; the
  existing SVG class `safe-zone-outline` remains only a renderer implementation class.
- Web and desktop adapters call `WarhammerCompanionService`; no custom frontend JavaScript was
  added.

TDD and implementation results:

- Red step: toolkit tests failed on the missing `warhammer_companion.application.deployment_exposure`
  module and missing typed exposure payloads.
- Green step: `domain/exposure.py`, `los/exposure.py`, and `application/deployment_exposure.py`
  added the deterministic payload, candidate-center geometry, selected risk modes, and
  `ToolkitResult` builder.
- Integration red step: service/rendering/web/desktop tests failed on missing state, SVG overlay
  arguments, `/deployment-exposure`, navigation, and desktop smoke wiring.
- Green step: shared service state, server-rendered route/template, desktop screen, and smoke
  summary were added.
- Adversarial review then found two blockers. Regression tests were added first for curved
  deployment-zone consistency and all four exposure modes. The fix changed placement diagnostics to
  use the same smoothed/eroded candidate-center basis and separated selected exposure from LOS/threat
  component facts.

Verification completed:

- Initial focused Phase 7 toolkit suite passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py -q`
  returned 4 passed.
- Initial app/rendering batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_rendering_svg.py -q`
  returned 29 passed.
- Initial web suite passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_web_server.py -q`
  returned 18 passed with the existing Starlette `TestClient` deprecation warning.
- Initial desktop suite passed after extending timeout:
  `.\.venv\Scripts\python.exe -m pytest tests\test_desktop_app.py -q`
  returned 13 passed.
- After adversarial fixes, `tests/test_deployment_exposure_toolkit.py -q` returned 6 passed.
- After adversarial fixes, the broader Phase 7 batch
  `.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 60 passed with the existing Starlette `TestClient` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 115 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed after the final fixes: 360 passed with the
  existing Starlette `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok` and `deployment_exposure_svg: true`.
- `git diff --check` passed; Git printed only normal LF-to-CRLF warnings for touched files.

Browser QA:

- `Start-Process` hit the known Windows `Path`/`PATH` duplication issue, so the local app was
  launched through a detached Node child process on `http://127.0.0.1:8000`.
- Built-in Browser QA passed for `/deployment-exposure`, a manual threat-and-LOS query route, the
  mandatory page 9 route, and the mandatory page 52 route.
- Each route rendered one SVG map, one form, zero `<script>` tags, at least one
  `safe-zone-outline`, one `threat-projection-image`, one `coverage-image`, one friendly
  `model-base`, one `threat-source-base`, estimated/not-planner warning copy, no traceback text, no
  forbidden visible claim wording, and no warning/error console logs.
- Interactive Browser QA filled friendly X/Y, submitted the form, preserved values in the redirect,
  and rendered expected overlays with no console warning/error logs.
- Browser QA was rerun after adversarial fixes with the same passing result. The temporary QA server
  process was terminated after each run.

Review and blocker status:

- Consultant design review approved after scoping the phase to Deployment Exposure Diagnostics.
- Adversarial design review approved after page 9 and page 52 Browser regression routes were added.
- Consultant implementation review approved. CodeRabbit review was unavailable because `coderabbit`
  was not found in PowerShell or WSL and a WSL install attempt timed out.
- Adversarial implementation review initially required changes for curved deployment-zone geometry
  and selected-vs-component exposure wording. Both were fixed with failing tests first; adversarial
  re-review approved.
- Protected-path scan passed: no generated/raw/binary/credential paths and no secret-pattern hits.
  `AGENTS.md` remained untracked and excluded from staging.

## Phase 7.5 - Exposure Mode Housekeeping

Purpose:

- Run a behavior-preserving housekeeping slice after Deployment Exposure and before Phase 8.
- Remove duplicated exposure-mode component predicate logic from the application builder and service
  adapter.
- Keep Deployment Exposure route, desktop screen, rendering, geometry, user-facing copy, and
  selected-risk semantics unchanged.

Artifacts:

- `docs/superpowers/specs/2026-06-22-phase-7-5-exposure-mode-housekeeping.md`
- `docs/superpowers/plans/2026-06-22-phase-7-5-exposure-mode-housekeeping.md`
- `docs/superpowers/qa/2026-06-22-phase-7-5-exposure-mode-housekeeping-qa.md`
- `docs/superpowers/reviews/2026-06-22-phase-7-5-consultant-exposure-mode-housekeeping.md`
- `docs/superpowers/reviews/2026-06-22-phase-7-5-adversarial-exposure-mode-housekeeping.md`
- `src/warhammer_companion/domain/exposure.py`
- `src/warhammer_companion/application/deployment_exposure.py`
- `src/warhammer_companion/application/services.py`
- `tests/test_deployment_exposure_toolkit.py`
- `tests/test_application_service.py`

Design decisions:

- `domain/exposure.py` now owns exposure-mode component predicate semantics because it already owns
  `ExposureMode`, `EXPOSURE_MODES`, payload records, and `coerce_exposure_mode(...)`.
- The shared helpers are `exposure_mode_includes_los(...)` and
  `exposure_mode_includes_threat(...)`.
- The helpers mean component diagnostic/overlay inclusion only. They do not define selected-risk
  geometry. `threat-and-los` still includes both component overlays while selected risk remains the
  intersection handled by `los/exposure.py`.
- Unsupported raw exposure modes still block through the result builder with
  `invalid-exposure-mode`; this slice does not make unsupported strings valid.

TDD and implementation results:

- Red step: `tests/test_deployment_exposure_toolkit.py` imported the new domain helpers before they
  existed and failed with the expected import error.
- Green step: `domain/exposure.py` added the two helper predicates with component-semantics
  docstrings; the helper truth-table test passed.
- Guardrail step: unsupported raw mode blocking and all-four-mode service rendering tests were added
  and passed before refactoring, proving current behavior.
- Refactor step: `application/deployment_exposure.py` and `application/services.py` now import the
  shared helpers; private duplicate predicate functions were removed. `_placement_diagnostic(...)`
  now takes an `ExposureMode`.

Verification completed:

- Helper red/green command passed after implementation:
  `.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py::test_exposure_mode_helpers_cover_all_supported_component_modes -q`
  returned 1 passed.
- Guardrail behavior command passed before refactor:
  `.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py::test_deployment_exposure_blocks_unsupported_raw_exposure_mode tests\test_application_service.py::test_deployment_exposure_state_renders_component_overlays_by_mode -q`
  returned 5 passed.
- Focused Phase 7.5 batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 72 passed with the existing Starlette `TestClient` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 115 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 366 passed with the existing Starlette
  `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok` and `deployment_exposure_svg: true`.
- `git diff --check` passed; Git printed only normal LF-to-CRLF warnings for touched files.

Browser QA:

- The local app was launched through a detached Node child process on `http://127.0.0.1:8000`.
- Built-in Browser QA passed for `/deployment-exposure`, the mandatory page 9 Deployment Exposure
  route, and the mandatory page 52 Deployment Exposure route.
- Each route rendered one SVG map, one form, zero `<script>` tags, at least one
  `safe-zone-outline`, one `threat-projection-image`, one `coverage-image`, one friendly
  `model-base`, one `threat-source-base`, estimated/not-planner warning copy, no traceback text, no
  forbidden visible claim wording, and no warning/error console logs.
- The temporary QA server process was terminated after Browser QA.

Review and blocker status:

- Consultant reviewer approved this as a narrow Phase 7.5 housekeeping slice and recommended keeping
  selected-risk behavior tests separate from the helper truth table.
- Adversarial reviewer first required stronger QA for all four service-rendering modes, unsupported
  raw mode blocking, component-vs-risk semantics, correct service test construction, and
  `ExposureMode` typing. The spec/plan/QA were updated before source edits.
- Implementation re-review found no Python blockers, but initially blocked commit because this
  Phase 7.5 work-log entry was missing.
- Protected-path scan passed: no generated/raw/binary/credential paths and no secret-pattern hits.
  `AGENTS.md` remained untracked and excluded from staging.

## Phase 8A - Manual Damage Estimate

Purpose:

- Start Phase 8 without overclaiming roster-aware Damage And Survivability Profiles before
  source/profile resolution authority exists.
- Add a deterministic manual damage math toolkit for one fixed attack profile into one homogeneous
  target profile.
- Keep valid outputs `estimated`, invalid outputs `blocked`, and no outputs `trusted`.

Artifacts:

- `docs/superpowers/specs/2026-06-22-phase-8a-manual-damage-estimate.md`
- `docs/superpowers/plans/2026-06-22-phase-8a-manual-damage-estimate.md`
- `docs/superpowers/qa/2026-06-22-phase-8a-manual-damage-estimate-qa.md`
- `docs/superpowers/reviews/2026-06-22-phase-8a-consultant-manual-damage-estimate.md`
- `docs/superpowers/reviews/2026-06-22-phase-8a-adversarial-manual-damage-estimate.md`
- `src/warhammer_companion/domain/damage.py`
- `src/warhammer_companion/application/damage_profile.py`
- `src/warhammer_companion/application/services.py`
- `src/warhammer_companion/application/view_models.py`
- `src/warhammer_companion/web/server.py`
- `src/warhammer_companion/web/templates/damage_profile.html`
- `src/warhammer_companion/desktop/screens/damage_profile.py`
- `tests/test_damage_profile_toolkit.py`
- `tests/test_application_service.py`
- `tests/test_web_server.py`
- `tests/test_desktop_app.py`

Design decisions:

- This slice is named Phase 8A Manual Damage Estimate, not full Phase 8 completion.
- Inputs are manual only: fixed integer attacks, hit/wound/effective save targets from 2+ through
  6+, flat non-negative damage, finite positive integer wounds/model, and finite positive integer
  model count.
- Effective save is supplied by the user after unmodeled AP, cover, and invulnerable decisions.
- Unsaved-wound PMFs use exact binomial math and preserve a common denominator for readability.
- Model destruction lets damage from separate unsaved wounds accumulate on the active model, but
  excess damage from an attack after a model is destroyed is discarded.
- No roster snapshot, profile, official rule text, AP/cover resolver, modifier, reroll, ability,
  Feel No Pain, damage reduction, mission warning, target priority, or unit matrix behavior is
  implemented in this slice.

TDD and implementation results:

- Red step: the new toolkit and route tests failed with expected missing-module and missing-state
  import errors before implementation.
- Initial green step found one PMF presentation mismatch: 14/64 was being reduced to 7/32. The
  builder now preserves common binomial denominators and grouped model-destroyed denominators.
- Adversarial implementation review found that a `+ 1e-9` kill-threshold tolerance could overkill
  fractional damage just below a target wound threshold. The tolerance was removed and a regression
  covers 3 unsaved wounds at 0.333333333 damage into a 1-wound target.
- The web route `/damage-profile` is server-rendered with one form, no custom JavaScript, caution
  copy, summary values, unsaved-wound PMF, model-destroyed PMF, and blocked invalid-input reasons.
- The desktop screen `Damage Profile` is a thin PySide6 adapter over `damage_profile_state(...)`.
- Desktop smoke now reports `damage_profile_estimate: true`.

Verification completed:

- Red check before implementation failed as expected:
  `.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q`
  reported missing `warhammer_companion.application.damage_profile` and missing
  `DamageProfileState`.
- Focused toolkit command passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py -q`
  returned 21 passed after the fractional-damage regression was added.
- Focused Phase 8A batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 74 passed with the existing Starlette `TestClient` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 119 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 393 passed with the existing Starlette
  `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok`, official packet count 45, and
  `damage_profile_estimate: true`.

Browser QA:

- The local app was launched through a detached Node child process on `http://127.0.0.1:8000`.
- Built-in Browser QA passed for `/damage-profile`, the valid sample query
  `/damage-profile?attacks=2&hit=4&wound=4&save=4&damage=2&wounds=2&models=3`, and the blocked
  invalid query `/damage-profile?attacks=0&hit=4&wound=4&save=4&damage=2&wounds=2&models=3`.
- Each route rendered heading `Damage Profile`, exactly one form, zero `<script>` tags, all manual
  inputs, required manual-estimate/effective-save/unsupported-effects warning copy, no traceback or
  internal-error text, no forbidden positive claim wording, and no localhost warning/error console
  logs.
- Valid routes showed expected damage `0.50` and distribution rows `49/64`, `14/64`, and `1/64`.
- The invalid route showed blocked status and attack-count block reason text.
- The temporary QA tab and server process were closed after Browser QA.

Review and blocker status:

- Consultant reviewer approved the narrowed Phase 8A spec, plan, and QA pathway.
- Adversarial reviewer initially required stricter finite-positive-integer target semantics and
  explicit invalid-input fixtures. The docs were patched and re-review approved the scope.
- Adversarial implementation review required a fractional-damage threshold fix; the fix and
  regression were applied before final re-review.

## Phase 8.5 - Damage Profile Defaults Housekeeping

Purpose:

- Run a behavior-preserving housekeeping slice after Phase 8A.
- Centralize the manual Damage Profile default input values used by service, web, and desktop
  adapters.
- Keep math, readiness, warning copy, route names, form/query field names, and desktop labels
  unchanged.

Artifacts:

- `docs/superpowers/specs/2026-06-22-phase-8-5-damage-defaults-housekeeping.md`
- `docs/superpowers/plans/2026-06-22-phase-8-5-damage-defaults-housekeeping.md`
- `docs/superpowers/qa/2026-06-22-phase-8-5-damage-defaults-housekeeping-qa.md`
- `docs/superpowers/reviews/2026-06-22-phase-8-5-consultant-damage-defaults.md`
- `docs/superpowers/reviews/2026-06-22-phase-8-5-adversarial-damage-defaults.md`
- `src/warhammer_companion/domain/damage.py`
- `src/warhammer_companion/application/services.py`
- `src/warhammer_companion/web/server.py`
- `src/warhammer_companion/desktop/screens/damage_profile.py`
- `tests/test_damage_profile_toolkit.py`
- `tests/test_application_service.py`
- `tests/test_desktop_app.py`

Design decisions:

- Canonical defaults live in `domain/damage.py` as `DEFAULT_DAMAGE_PROFILE_INPUT` and
  `DEFAULT_TARGET_PROFILE_INPUT` because they are typed manual damage profile records, not web
  form metadata.
- Web query/form field names remain adapter-owned and are not centralized in the domain layer.
- The default values remain attacks 2, hit 4+, wound 4+, effective save 4+, damage 2, 2
  wounds/model, and 3 target models.
- No roster/profile/rules authority, new mechanic, or recommendation behavior was added.

TDD and implementation results:

- Red step: new guardrail tests imported `DEFAULT_DAMAGE_PROFILE_INPUT` and
  `DEFAULT_TARGET_PROFILE_INPUT` before they existed and failed with expected import errors.
- Green step: defaults were added in `domain/damage.py` and wired into service default parameters,
  GET `/damage-profile` defaults, and desktop `DamageProfileScreen` initial controls.
- Guardrail tests now assert the constants, service default summary, and desktop initial controls.

Verification completed:

- Red check before implementation failed as expected:
  `.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py tests\test_application_service.py tests\test_desktop_app.py -q`
  reported missing default constants.
- Focused Phase 8.5 batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py tests\test_application_service.py tests\test_desktop_app.py -q`
  returned 56 passed.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 119 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 395 passed with the existing Starlette
  `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok` and `damage_profile_estimate: true`.

Browser QA:

- The local app was launched through a detached Node child process on `http://127.0.0.1:8000`.
- Built-in Browser QA passed for `/damage-profile`.
- The default route rendered heading `Damage Profile`, exactly one form, zero `<script>` tags,
  expected damage `0.50`, distribution rows `49/64`, `14/64`, and `1/64`, required
  manual-estimate/effective-save/unsupported-effects warning copy, no traceback/internal-error text,
  and no localhost warning/error console logs.
- The temporary QA tab and server process were closed after Browser QA.

Review and blocker status:

- Consultant reviewer approved the Phase 8.5 spec, plan, and QA pathway.
- Adversarial reviewer approved the Phase 8.5 spec, plan, and QA pathway with no blockers.
- Consultant and adversarial implementation re-review approved the final diff with no blockers.
- Protected-path scan passed: no generated/raw/binary/credential paths and no high-confidence
  secret-pattern hits. `AGENTS.md` remained untracked and excluded from staging.

## Phase 9 - Mission Pack Skeleton

Purpose:

- Start Phase 9 without overclaiming mission scoring, objective-control analytics, or captain-level
  matchup estimates.
- Add source-safe mission-pack records and a Mission Pack product surface.
- Derive primary mission labels only from existing layout metadata and record the public Google
  Sheet as untrusted candidate provenance without fetching or parsing it.

Artifacts:

- `docs/superpowers/specs/2026-06-22-phase-9-mission-pack-skeleton.md`
- `docs/superpowers/plans/2026-06-22-phase-9-mission-pack-skeleton.md`
- `docs/superpowers/qa/2026-06-22-phase-9-mission-pack-skeleton-qa.md`
- `docs/superpowers/reviews/2026-06-22-phase-9-consultant-mission-pack-skeleton.md`
- `docs/superpowers/reviews/2026-06-22-phase-9-adversarial-mission-pack-skeleton.md`
- `src/warhammer_companion/domain/missions.py`
- `src/warhammer_companion/application/mission_pack.py`
- `src/warhammer_companion/application/services.py`
- `src/warhammer_companion/application/view_models.py`
- `src/warhammer_companion/web/server.py`
- `src/warhammer_companion/web/templates/base.html`
- `src/warhammer_companion/web/templates/mission_pack.html`
- `src/warhammer_companion/desktop/app.py`
- `src/warhammer_companion/desktop/main_window.py`
- `src/warhammer_companion/desktop/screens/mission_pack.py`
- `tests/test_mission_pack_toolkit.py`
- `tests/test_application_service.py`
- `tests/test_web_server.py`
- `tests/test_desktop_app.py`
- `README.md`
- `docs/qa-scenarios.md`
- `docs/work-log/player-toolkit-implementation.md`

Design decisions:

- This slice is a mission-pack skeleton only. Primary/secondary scoring formulas, action timing,
  objective control, contest math, denial/flip potential, and team-pairing analytics remain out of
  scope.
- `domain/missions.py` owns typed mission source refs, source anchors, mission records, pack
  records, and payload records.
- `application/mission_pack.py` builds deterministic `ToolkitResult` payloads from
  `OFFICIAL_LAYOUT_PAGE_METADATA` only.
- Mission records use readiness `estimated`, mechanics readiness `source-pending`, stable ids such
  as `primary-battlefield-dominance`, and Event Companion page anchors.
- The supplied public Google Sheet URL is stored only as source metadata: URL, sheet id, gid
  `1565185881`, retrieval status `not_fetched`, trust `untrusted_candidate`, and no content hash
  because no fetch occurs.
- No mission-card images, Google Sheet exports, screenshots, full card text, external-sheet
  payloads, or raw protected source documents are stored.
- The web route `/mission-pack` is server-rendered with no custom JavaScript.
- The desktop `Mission Pack` screen is a thin PySide6 adapter over `mission_pack_state(...)`.
- Desktop smoke now reports `mission_pack_estimate: true`.

TDD and implementation results:

- Red step: `tests/test_mission_pack_toolkit.py` failed with the expected missing
  `warhammer_companion.application.mission_pack` module before implementation.
- Green step: mission domain records and the deterministic builder were added; the focused mission
  toolkit tests passed.
- Integration red step: the service/web/desktop tests failed on missing `MissionPackState`, route,
  desktop screen, and smoke-summary key.
- Green step: shared service state, server-rendered route/template, desktop screen/navigation, and
  smoke summary were added.
- The initial combined targeted command timed out at 180 seconds because the desktop suite exceeded
  that timeout; split suite runs passed and the exact combined command passed when rerun with a
  longer timeout.

Verification completed:

- Red check before implementation failed as expected:
  `.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py -q`
  reported missing `warhammer_companion.application.mission_pack`.
- Focused builder command passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py -q`
  returned 5 passed.
- Targeted split checks passed after the initial timeout:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py tests\test_application_service.py -q`
    returned 26 passed.
  - `.\.venv\Scripts\python.exe -m pytest tests\test_web_server.py -q` returned 22 passed with
    the existing Starlette `TestClient` deprecation warning.
  - `.\.venv\Scripts\python.exe -m pytest tests\test_desktop_app.py -q` returned 15 passed in
    208.51 seconds.
- Exact focused Phase 9 batch passed after raising timeout:
  `.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 63 passed with the existing Starlette `TestClient` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 123 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 403 passed with the existing Starlette
  `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok`, 45 official packets, and `mission_pack_estimate: true`.

Browser QA:

- The local app was launched through a detached child process on `http://127.0.0.1:8000`.
- Built-in Browser QA passed for `/mission-pack`.
- The route rendered heading `Mission Pack`, primary mission records including `Battlefield
  Dominance` and `Sabotage`, the public sheet source row with sheet id and gid `1565185881`,
  source-pending/not-fetched/not-ingested warning copy, zero forms, zero `<script>` tags, no
  traceback/internal-error text, no legal/optimal/recommended/likely/pairing-score claim wording,
  and no localhost warning/error console logs.
- The temporary QA tab and server process were closed after Browser QA.

Review and blocker status:

- Consultant reviewer initially required the public Google Sheet candidate metadata to specify the
  exact URL, sheet id, gid, retrieval status, trust value, and no-content-hash behavior.
- The spec, plan, QA, and review notes were patched; consultant re-review approved.
- Adversarial reviewer approved the skeleton-only scope with no blockers.
- Consultant implementation reviewer approved after checking the Phase 9 acceptance criteria:
  source refs, warnings, primary mission records, stable ids, page anchors, public-sheet
  metadata-only handling, web/desktop surfaces, tests, docs, and work-log evidence.
- Adversarial implementation reviewer approved the diff with no blockers and noted that sheet
  handling, architecture boundaries, no-JS web behavior, and tests were safe to commit.
- Protected-path scan passed for the Phase 9 candidate files: no generated/raw/cache/log/build/dist
  paths, raw PDFs, database/archive files, images, screenshots, Google Sheet exports, or fetched
  sheet payloads are in the candidate set.
- A narrowed network-fetch scan over Phase 9 candidate files returned no fetch/HTTP/client library
  matches.
- A broad secret-pattern scan hit an existing `data/codex-home` fixture line outside the Phase 9
  diff; the Phase 9 diff itself adds no credential or secret material.
- `AGENTS.md` remains user-owned and must stay untracked unless explicitly requested.

## Phase 9.5 - Mission Source Metadata Housekeeping

Purpose:

- Run a behavior-preserving cleanup after the Phase 9 Mission Pack skeleton.
- Centralize mission-pack source refs and warning text inside the application builder.
- Remove public-sheet metadata duplication between the `MissionSourceRef` and input-hash payload.

Artifacts:

- `docs/superpowers/specs/2026-06-22-phase-9-5-mission-source-metadata-housekeeping.md`
- `docs/superpowers/plans/2026-06-22-phase-9-5-mission-source-metadata-housekeeping.md`
- `docs/superpowers/qa/2026-06-22-phase-9-5-mission-source-metadata-housekeeping-qa.md`
- `docs/superpowers/reviews/2026-06-22-phase-9-5-consultant-mission-source-metadata.md`
- `docs/superpowers/reviews/2026-06-22-phase-9-5-adversarial-mission-source-metadata.md`
- `src/warhammer_companion/application/mission_pack.py`
- `tests/test_mission_pack_toolkit.py`
- `docs/work-log/player-toolkit-implementation.md`

Design decisions:

- Keep the public `build_mission_pack_toolkit_result(...)` signature unchanged.
- Keep test injection private to `_mission_pack_hash(...)`.
- Preserve the Phase 9 default `input_hash`
  `sha256:01f1430011d73eec7f009f95dc8a4e5671b581dcdf7ecfdd0097020a5eefd2bc`.
- Preserve the Phase 9 default `result_id` `estimated:mission-pack:01f1430011d7`.
- Keep source metadata in `application/mission_pack.py`; do not move public-source constants into
  the generic domain model module.
- No fetching, parsing, scoring, objective/action analytics, image storage, sheet export, or card
  text behavior was added.

TDD and implementation results:

- Red step: `tests/test_mission_pack_toolkit.py` failed with expected missing private helper
  `_mission_source_refs`.
- Green step: `MISSION_PACK_WARNINGS`, `_mission_source_refs()`, and private source-ref injection
  for `_mission_pack_hash(...)` were added.
- The input hash now derives public-sheet hash fields from the canonical source-ref object instead
  of duplicating URL, sheet id, gid, trust, and retrieval status literals.
- Guardrail tests prove default identity preservation, public builder signature preservation,
  canonical warning sharing, source-ref metadata preservation, and private hash sensitivity.

Verification completed:

- Red check before implementation failed as expected:
  `.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py -q` reported missing
  private helper `_mission_source_refs`.
- Focused Phase 9.5 command passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py -q` returned
  8 passed.
- Focused app batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 66 passed with the existing Starlette `TestClient` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 123 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 406 passed with the existing Starlette
  `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok`, 45 official packets, and `mission_pack_estimate: true`.

Browser QA:

- The local app was launched through a detached child process on `http://127.0.0.1:8000`.
- Built-in Browser QA passed for `/mission-pack`.
- The route rendered heading `Mission Pack`, primary mission records including `Battlefield
  Dominance` and `Sabotage`, the public sheet source row with sheet id and gid `1565185881`,
  source-pending/not-fetched/not-ingested warning copy, zero forms, zero `<script>` tags, no
  traceback/internal-error text, no legal/optimal/recommended/likely/pairing-score claim wording,
  and no localhost warning/error console logs.
- The temporary QA tab and server process were closed after Browser QA.
- Protected-path scan passed for the Phase 9.5 candidate files: no generated/raw/cache/log/build/
  dist paths, raw PDFs, database/archive files, images, screenshots, Google Sheet exports, `.codex`,
  `.agents`, `data/codex-home*`, auth/session files, or other Codex/OpenAI state paths are in the
  candidate set.
- A narrowed network-fetch scan over Phase 9.5 candidate files returned no fetch/HTTP/client
  library matches.
- A broad secret-pattern scan self-matched the new protected-path checklist text and one older
  historical `.codex` work-log line outside the Phase 9.5 diff; the Phase 9.5 code/test diff adds
  no credential or secret material.

Review and blocker status:

- Consultant reviewer initially required default `input_hash`/`result_id` and canonical warning
  text guards. The plan and QA pathway were patched; consultant re-review approved.
- Adversarial reviewer initially required public signature immutability, private-helper-only test
  injection, default identity guards, and broader Codex/OpenAI state wording in the protected-path
  checklist. The docs were patched; adversarial re-review approved.
- Consultant implementation reviewer approved the staged Phase 9.5 diff with no required changes.
- Adversarial implementation reviewer initially required moving Phase 9.5 scan evidence into the
  Phase 9.5 section and staging the Phase 9.5 docs listed as artifacts. Both were fixed;
  adversarial re-review approved.

## Phase 10A - Manual Deployment Scorecard

Purpose:

- Start Phase 10 Mission-Aware Deployment Toolkit with a modest manual scorecard slice.
- Reuse the existing deployment exposure geometry and Mission Pack skeleton instead of introducing
  a parallel deployment solver.
- Add explicit going-first/going-second context and source-pending mission readiness warnings.

Artifacts:

- `docs/superpowers/specs/2026-06-22-phase-10a-manual-deployment-scorecard.md`
- `docs/superpowers/plans/2026-06-22-phase-10a-manual-deployment-scorecard.md`
- `docs/superpowers/qa/2026-06-22-phase-10a-manual-deployment-scorecard-qa.md`
- `docs/superpowers/reviews/2026-06-22-phase-10a-consultant-deployment-scorecard.md`
- `docs/superpowers/reviews/2026-06-22-phase-10a-adversarial-deployment-scorecard.md`
- `src/warhammer_companion/domain/deployment_scorecard.py`
- `src/warhammer_companion/application/deployment_scorecard.py`
- `src/warhammer_companion/application/services.py`
- `src/warhammer_companion/application/view_models.py`
- `src/warhammer_companion/web/templates/deployment_scorecard.html`
- `src/warhammer_companion/desktop/screens/deployment_scorecard.py`
- `tests/test_deployment_scorecard_toolkit.py`

Design decisions:

- Treat the scorecard as a deterministic diagnostic, not a placement planner, optimizer, or mission
  scoring engine.
- Use battlefield inches for all coordinates, base diameters, movement distances, and threat
  ranges.
- Return `estimated` only when both deployment exposure validation and turn-order validation pass.
- Return `blocked` with no tactical overlays when either deployment exposure validation or
  turn-order validation fails.
- Keep scorecard components constrained to deployment fit, selected exposure, mission readiness,
  and turn-order assumption.
- Do not emit aggregate scores, ranks, grades, best labels, placement recommendations, or
  captain-level matchup guidance.
- Keep public mission-sheet context metadata-only; no public sheet fetch, mission-card/rules text,
  copied source images, screenshots, exports, or card payloads were added.

TDD and implementation results:

- Red step: `tests/test_deployment_scorecard_toolkit.py` failed with missing module
  `warhammer_companion.application.deployment_scorecard`.
- Green step: added typed domain components/payload, application builder, shared service state,
  server-rendered web route, PySide6 desktop screen, desktop smoke key, and focused tests.
- The builder composes `build_deployment_exposure_toolkit_result(...)` and
  `build_mission_pack_toolkit_result(...)`; it does not duplicate geometry or mission ingestion.

Verification completed:

- Red check before implementation failed as expected:
  `.\.venv\Scripts\python.exe -m pytest tests\test_deployment_scorecard_toolkit.py -q`
  reported missing `warhammer_companion.application.deployment_scorecard`.
- Focused Phase 10A command passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_deployment_scorecard_toolkit.py -q`
  returned 5 passed.
- Focused app batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_deployment_scorecard_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 69 passed with the existing Starlette `TestClient` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 127 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 417 passed with the existing Starlette
  `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok`, 45 official packets, and
  `deployment_scorecard_estimate: true`.

Browser QA:

- The local app was launched through a detached child process on `http://127.0.0.1:8000`.
- Built-in Browser QA passed for `/deployment-scorecard`, valid going-first and going-second page
  9 routes, invalid base route, invalid turn-order route, valid form submission, and invalid base
  form submission.
- The route rendered heading `Deployment Scorecard`, one form, zero `<script>` tags, no
  traceback/internal-error text, no forbidden visible claims, and no console warning/error logs on
  routed checks.
- Valid outputs rendered the expected selected threat/LOS exposure overlays according to mode.
- Blocked base and blocked turn-order outputs rendered `blocked` state, user-facing blocker text,
  and no coverage/threat/candidate overlay classes.
- The temporary QA server process was closed after Browser QA.

Review and blocker status:

- Consultant reviewer initially required exact Browser QA URLs, synced forbidden-claim checks,
  page 9/page 52 rationale, and desktop verification beyond smoke. The docs were patched;
  consultant re-review approved.
- Adversarial reviewer initially required first-class invalid-turn-order blocking, exact component
  semantics, canonical visible-text claim checks, stronger Browser form QA, and explicit
  public-source/IP assertions. The docs were patched.
- Focused adversarial design re-review required explicit inch units, corrected readiness logic,
  all-blocked-output overlay behavior, and a mechanical Browser overlay assertion. The docs were
  patched and focused design re-review approved.
- Consultant implementation review required replacing the ineffective `[data-toolkit-overlay]`
  Browser assertion with concrete overlay-class absence checks and removing duplicated
  `invalid-turn-order` user-facing text. Both were fixed.
- Adversarial implementation review required the desktop blocker assertion to check the intended
  blocker/status surface and warned that work-log verification should only be finalized after the
  red desktop QA was fixed. The desktop test was corrected and rerun.
- Post-review reruns passed: exact failed desktop test 1 passed, focused Phase 10A app batch
  69 passed, Ruff format/check passed, Ruff check passed, mypy passed, full pytest 417 passed, and
  desktop smoke reported `deployment_scorecard_estimate: true`.

## 2026-06-22 - Phase 10.5 Deployment Map Rendering Housekeeping

Scope:

- Centralized Deployment Exposure and Deployment Scorecard map SVG projection through one private
  service-layer helper.
- Preserved existing behavior by keeping geometry, renderer inputs, overlay gating, web routes,
  templates, and desktop copy unchanged.
- Added characterization coverage for official event companion page 9 and page 52 deployment maps.

Design decisions:

- Treat this as a behavior-preserving cleanup only; do not change scorecard semantics, overlay
  classes, tactical calculations, mission context, or user-facing route behavior.
- Keep the helper in `WarhammerCompanionService` because both affected product states already live
  there and should not move rendering orchestration into web or desktop adapters.
- Lock page 9 and page 52 output by SHA-256 hashes so future rendering changes must be deliberate.

Implementation results:

- Added a private `_deployment_exposure_map_svg(...)` helper that renders either a bare packet map
  for blocked states or the same candidate, LOS, threat, friendly-base, and enemy-source overlays
  for valid states.
- Reused the helper from both `deployment_exposure_state(...)` and
  `deployment_scorecard_state(...)`.
- Added service tests proving scorecard/exposure SVG equality for matching valid inputs, page 9
  and page 52 characterized hashes, required overlay classes, and blocked scorecard overlay
  absence.
- Extended desktop scorecard coverage to assert a valid map pixmap is rendered and an invalid
  turn-order scorecard state omits tactical overlay classes.

Verification completed:

- Pre-refactor characterization initially failed on an incorrect test assumption about the SVG root
  class, then passed after correcting the assertion to the current `map-svg` output.
- Post-refactor focused command passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py::test_deployment_scorecard_and_exposure_maps_match_characterized_official_layouts tests\test_application_service.py::test_deployment_exposure_state_renders_candidate_threat_los_and_base_overlays tests\test_application_service.py::test_deployment_scorecard_state_blocks_invalid_turn_order_without_tactical_overlays tests\test_desktop_app.py::test_desktop_deployment_scorecard_screen_reports_components_and_blockers -q`
  returned 4 passed.
- Focused app batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 65 passed with the existing Starlette `TestClient` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 127 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 418 passed with the existing Starlette
  `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok`, 45 official packets, and
  `deployment_scorecard_estimate: true`.

Manual QA:

- The built-in Browser binding was unavailable in this resumed continuation with
  `browser is not defined`; `tool_search` found Browser plugin metadata but no callable Browser
  control tool, and Computer/Firefox control was not exposed.
- Fallback local HTTP QA against the running app passed for the valid page 9 Deployment Exposure
  route, valid page 9 Deployment Scorecard route, valid page 52 Deployment Scorecard route, and
  invalid-base Deployment Scorecard route.
- The fallback checks verified expected headings, zero `<script>` tags, no traceback/internal-error
  text, overlay presence on valid routes, and overlay absence on the blocked invalid-base route.
- The temporary QA server process was closed after the fallback route checks.

Review status:

- Consultant design review approved the narrow service-layer helper scope.
- Adversarial design review required stronger preservation evidence, page 52 coverage, exact
  Browser/manual QA URLs, and desktop overlay assertions; the spec, plan, QA pathway, and review
  notes were patched.
- Focused adversarial re-review approved the hardened Phase 10.5 plan before implementation.

## 2026-06-22 - Phase 11A Team Pairing Matrix

Scope:

- Added the first Phase 11 matchup analytics slice as a labels-only Team Pairing Matrix dossier.
- Aggregated existing deterministic toolkit outputs into component cards: manual damage profile,
  mission pack skeleton, deployment scorecard, and explicit unsupported-data cards.
- Kept the result degraded by design; no recommendations, pairing scores, expected points, win
  probabilities, confidence bands, rankings, best/worst labels, or calibration claims were added.

Design decisions:

- Treat each matrix cell as labels-only and shared-scenario based until roster-specific and
  opponent-specific source results exist.
- Store only sanitized scalar dossier fields: labels, selected packet id/label, result ids, input
  hashes, readiness, source ref ids, warnings, blockers, and raw deterministic metrics.
- Do not retain `MapPacket`, source payloads, Shapely geometry, SVG/images, source URLs, Google
  Sheet id/gid, mission-card text, or official rules text in the pairing payload.
- Force valid Phase 11A output to `degraded`, even if future source components become `trusted`.
- Block empty labels, too many labels, duplicate normalized labels, and labels longer than 80
  characters.
- Normalize labels by comma/newline splitting, whitespace collapse, control-character removal,
  empty-fragment dropping, and order preservation.

Design review:

- Consultant gap-analysis recommended a deterministic component dossier and explicitly deferred
  expected tournament points, win rates, confidence bands, priors, weights, and captain automation.
- Consultant design review required `not_available` to remain an assessment, forced degraded
  readiness, label overflow blocking, and source URL/sheet id/gid leak checks.
- Adversarial design review required labels-only wording, sanitized payload boundaries, no visible
  forbidden terms, desktop parity, label-safety details, source blocker propagation, and no-network
  QA.
- Focused re-review approved after the QA route was patched to exercise internal whitespace
  collapse and empty-fragment dropping.

TDD and implementation results:

- Red builder test:
  `.\.venv\Scripts\python.exe -m pytest tests\test_matchup_matrix_toolkit.py -q`
  failed with missing `warhammer_companion.application.matchup_matrix`.
- Added `domain/matchups.py` and `application/matchup_matrix.py`; focused builder tests then
  passed with 15 passed.
- Red service tests failed because `WarhammerCompanionService` had no
  `team_pairing_matrix_toolkit_result(...)` or `team_pairing_matrix_state(...)`.
- Added shared service/view state and desktop smoke key.
- Red web tests failed with `/team-pairing` 404 and missing POST redirect.
- Added server-rendered `/team-pairing`, POST redirect, navigation, and `team_pairing.html`; web
  route tests passed.
- Red desktop test failed because `Team Pairing` was missing from navigation.
- Added a thin PySide6 `TeamPairingScreen`; desktop parity test passed.

Verification completed:

- Focused Phase 11A app batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_matchup_matrix_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 87 passed with the existing Starlette `TestClient` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests` passed: 131 files already
  formatted.
- `.\.venv\Scripts\python.exe -m ruff check .` passed.
- `.\.venv\Scripts\mypy.exe src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 440 passed with the existing Starlette
  `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok`, 45 official packets, and
  `team_pairing_matrix_degraded: true`.

Manual QA:

- Built-in Browser control was unavailable in the resumed continuation:
  `typeof browser=undefined`.
- `tool_search` exposed Browser/Computer plugin metadata but no callable Browser or Computer
  control tool.
- Detached localhost server attempts exited before binding to port 8000, although a foreground
  startup probe reached uvicorn startup and blocked normally.
- Fallback in-process FastAPI route QA passed for `/team-pairing`, a valid label query,
  normalization query, script-shaped label query, overflow-label query, and empty-friendly-label
  blocked query.
- The fallback checks verified heading/readiness text, zero `<script>` tags, no traceback/internal
  error text, matrix-cell presence/absence, forbidden authority phrase absence, source leak
  absence, normalized labels, escaped script-shaped label text, and expected blocker ids.

## 2026-06-22 - Phase 11.5 Pairing Label Normalization Housekeeping

Scope:

- Extracted Team Pairing Matrix label normalization from `application/matchup_matrix.py` into
  `application/pairing_labels.py`.
- Kept the slice behavior-preserving: no route changes, no desktop workflow changes, no readiness
  changes, no component assembly changes, and no source/privacy boundary changes.
- Added characterization tests for valid and blocked label identities before relying on the
  extraction.

Design decisions:

- Keep the helper in `warhammer_companion.application` because it normalizes UI/service input for a
  toolkit result and should remain reusable by web and desktop adapters.
- Preserve the existing `LabelInput = str | Sequence[str]` contract and side-specific blocker ids.
- Preserve comma/newline splitting, whitespace collapse, control-character removal, empty-fragment
  dropping, duplicate detection, max-count blocking, max-length blocking, ordering, and generated
  list ids.

Review status:

- Consultant design review required blocked-case hash/result-id characterization in addition to the
  valid default identity case.
- Adversarial design review required script-shaped and overflow route QA in the manual path.
- Consultant implementation review initially required a formatter fix, then approved after the
  strict format gate passed.
- Adversarial implementation review found no behavior drift, but required final acceptance evidence
  and this work-log artifact before commit.

Verification completed:

- Pre-refactor characterization locked valid, missing, overflow, duplicate, and overlong
  `input_hash`/`result_id` values plus blocker ids.
- Post-refactor focused matchup tests passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_matchup_matrix_toolkit.py -q`
  returned 17 passed.
- Focused app batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_matchup_matrix_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 89 passed with the existing Starlette `TestClient` deprecation warning.
- `.\.venv\Scripts\python.exe -m ruff format --check src tests --no-cache` passed: 132 files
  already formatted.
- `.\.venv\Scripts\python.exe -m ruff check . --no-cache` passed.
- `.\.venv\Scripts\mypy.exe --no-incremental src` passed.
- Full `.\.venv\Scripts\python.exe -m pytest` passed: 442 passed with the existing Starlette
  `TestClient` deprecation warning.
- Desktop smoke passed with `status: ok`, 45 official packets, and
  `team_pairing_matrix_degraded: true`.

Manual QA:

- Built-in Browser/Computer controls were not callable in this resumed session:
  `typeof browser=undefined`, `typeof computer=undefined`, and `typeof playwright=undefined`.
- `tool_search` exposed thread/app and subagent tools, but no callable Browser or Computer control
  tool.
- Fallback in-process FastAPI route QA passed for the default Team Pairing route, a script-shaped
  label route, and an overflow-label blocked route.
- The fallback checks verified expected page text, matrix-cell presence for valid routes, matrix-cell
  absence for overflow, escaped script-shaped label text, absence of unescaped script text, absence
  of public Google Sheet ids/URLs, and absence of `win probability` claims.

## 2026-06-22 - Mobile/Fly Movement Routing Repair

Scope:

- Repaired the movement engine so Movement Reach, Threat Range, Deployment Exposure, and Deployment
  Scorecard distinguish selected movement assumptions.
- Added profiles for ground non-mobile, ground mobile / infantry, Fly Take to the Skies, and
  Hover/no-cost Take to the Skies.
- Replaced endpoint Euclidean-only checks with estimated route distance around dense feature
  traversal blockers for non-mobile ground movement.
- Preserved dense feature endpoint occupancy blocking for all initial profiles.
- Added web and desktop movement-profile controls and effective movement summaries.

Design decisions:

- Dense terrain feature polygons, not broad terrain areas, control traversal blocking.
- Ground mobile / infantry, Fly Take to the Skies, and Hover/no-cost Take to the Skies ignore dense
  traversal blockers in this 2D estimate.
- Fly Take to the Skies applies a 2 inch movement penalty; Hover/no-cost Take to the Skies does not.
- Route-aware movement uses a deterministic inch-grid route estimate for non-mobile dense traversal
  blockers and records routing metadata in payloads and input hashes.
- `raw-range` Threat Range remains profile-invariant.
- Browser/desktop copy uses selected-assumption and route-connected wording rather than legal,
  safe, optimal, recommendation, guarantee, or charge-legality claims.

Plan and review:

- Plan artifact: `docs/superpowers/plans/2026-06-22-mobile-fly-movement-routing.md`.
- Consultant plan review initially required phase gates, page 9/page 52 performance checks, grid
  tolerance semantics, explicit desktop downstream handling, earlier review gates, full hash
  metadata, threat performance smoke coverage, prohibited wording, and protected-artifact scope.
- Adversarial plan review initially required Browser QA to prove geometry/probability changes, a
  deterministic dense-blocker fixture, feature-vs-area tests, point-threat assertions, visible
  downstream output changes, desktop behavior assertions, and visible Hover/no-cost Fly behavior.
- Final consultant and adversarial plan re-reviews approved after hardening.

TDD and implementation results:

- Red tests confirmed missing `movement_profile_id` arguments in movement and threat geometry.
- Added geometry coverage for non-mobile route-around success/failure, mobile dense traversal,
  dense endpoint occupancy blocking, Fly penalty, Hover/no-cost movement, terrain-area-vs-feature
  traversal, raw-range invariance, point-threat probability changes, and effective movement in
  threat distributions.
- Implemented typed movement profile records, routing metadata, route diagnostics, route-path
  rendering, movement-profile-aware threat projection, and downstream enemy movement profile
  propagation.
- Added small route/envelope caches to avoid repeated identical route-field work during desktop
  smoke and integration tests.
- Adversarial implementation review found two route-core blockers after initial implementation:
  Dijkstra edges could cross a dense traversal blocker between unblocked nodes, and route-grid node
  budget overflow could escape as an uncaught exception.
- Fixed route edges by rejecting neighbor segments intersecting traversal blockers.
- Added user-facing blocked results for route-grid overflow in Movement Reach, Threat Range, and
  Deployment Exposure; Deployment Scorecard inherits the exposure blocker.

Verification completed so far:

- Focused movement/threat geometry passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_threat_range_geometry.py -q`
  returned 23 passed.
- Focused geometry/toolkit batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_threat_range_geometry.py tests\test_movement_reach_toolkit.py tests\test_threat_range_toolkit.py tests\test_deployment_exposure_toolkit.py -q`
  returned 40 passed.
- Focused application/web/desktop batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 72 passed with the existing Starlette `TestClient` deprecation warning.
- The focused application/web/desktop batch currently takes about 4m54s because the desktop tests
  instantiate full windows and render official-packet maps repeatedly.
- Full pytest passed:
  `.\.venv\Scripts\python.exe -m pytest` returned 451 passed with the existing Starlette
  `TestClient` deprecation warning.
- Final full pytest after reviewer fixes passed:
  `.\.venv\Scripts\python.exe -m pytest` returned 461 passed with the existing Starlette
  `TestClient` deprecation warning.
- Static gates passed:
  `.\.venv\Scripts\python.exe -m ruff format --check src tests`,
  `.\.venv\Scripts\python.exe -m ruff check .`, and `.\.venv\Scripts\mypy.exe src`.
- Packet validation passed for all 45 packaged official Event Companion packets:
  `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets`.
- The exact Phase 7 page smoke selector now has executable tests and passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_threat_range_geometry.py -q -k "page_9 or page_52"`
  returned 2 passed, 24 deselected.
- Desktop smoke passed:
  `.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test` returned
  `status: ok` with movement reach, threat range, deployment exposure, and deployment scorecard
  surfaces present.
- `git diff --check` passed.
- Desktop profile-sensitive tests passed as part of full pytest and directly:
  `.\.venv\Scripts\python.exe -m pytest tests\test_desktop_app.py -q` returned 20 passed.
- Reviewer re-checks approved:
  implementation review approved route-edge filtering and node-budget handling after
  `40 passed`; QA review approved the desktop profile assertions, scorecard identity coverage, and
  executable page 9/page 52 smoke gate.
- Server-rendered fallback QA used page 9 Dense 12 with start/source `(14.0, 32.75)`,
  target/friendly `(22.5, 32.75)`, base `1.57`, move `9.0`, and threat `0.5`.
- Movement Reach rendered `Ground non-mobile` as not route-connected, `Ground mobile / infantry`
  as route-connected, `Fly: Take to the Skies` as not route-connected with effective movement
  `7.00 in`, and `Fly: Hover / no-cost Take to the Skies` as route-connected with effective
  movement `9.00 in`.
- Threat Range rendered target probability `0.0%` for `Ground non-mobile`, `100.0%` for
  `Ground mobile / infantry`, `0.0%` for `Fly: Take to the Skies`, and `100.0%` for
  `Fly: Hover / no-cost Take to the Skies`.
- Deployment Exposure and Deployment Scorecard rendered the same enemy movement profile selector
  and 0%/100% threat-probability split for the same page 9 scenario.
- `raw-range` Threat Range kept the same rendered result hash across all four movement profiles in
  fallback QA.

Manual QA status:

- Built-in Browser control was available at the start of this goal and reproduced the original bug:
  `/movement-reach` and `/threat-range` did not expose movement-profile controls.
- Full post-fix Browser QA is blocked in the current Codex app session. The in-app Browser runtime
  reports single-tab mode with no attached tab, and fresh visible-tab attempts time out while
  waiting for the Browser webview to attach.
- Computer Use with Firefox was attempted as the documented fallback and was stopped by the
  automation runtime because URL-policy enforcement is not supported for the current Windows
  browser.
- Until Browser or Computer Use is restored, the authoritative fallback evidence is the FastAPI
  route rendering above plus automated web, service, geometry, and desktop smoke tests.

## 2026-06-22 - LOS Analysis And Deployment Threat Source

Scope:

- Merged the separate LOS Heatmap and LOS Checker player surfaces into one switchable Line of Sight
  surface with canonical web route `/los`.
- Kept old `/heatmap` and `/los-checker` URLs as compatibility redirects to `/los` with the
  appropriate mode and preserved values.
- Added deployment-zone source mode to Threat Range so the source can be inferred from valid
  deployment-zone center geometry instead of only a point source.
- Added source-region movement and threat projection primitives that reuse the existing mobile,
  non-mobile, Fly, and Hover/no-cost movement assumptions.

Design decisions:

- The LOS merge is a thin application/UI facade over existing heatmap and checker engines rather
  than a rewrite of LOS geometry.
- Threat Range deployment-zone source mode uses an eroded deployment-zone source-center region
  cleared of dense endpoint occupancy; it blocks if that region is empty.
- Point source coordinates are deliberately ignored in deployment-zone source mode and remain
  validated only in point mode.
- Deployment Exposure and Deployment Scorecard were not changed in this slice because they still
  combine enemy threat with point-source enemy LOS.

Plan and review:

- Spec artifact:
  `docs/superpowers/specs/2026-06-22-los-analysis-and-deployment-threat-source.md`.
- QA artifact:
  `docs/superpowers/qa/2026-06-22-los-analysis-and-deployment-threat-source-qa.md`.
- Plan artifact:
  `docs/superpowers/plans/2026-06-22-los-analysis-and-deployment-threat-source.md`.
- Consultant review recommended a thin LOS facade and a true source-region threat primitive.
- Adversarial spec review initially required stronger web nav consolidation tests, deployment-zone
  source validation, empty source-region blocking, page 9/page 52 smoke coverage, and no-JS web
  coverage; the hardened spec was approved after those gaps were closed.

TDD and implementation results:

- Red tests covered source-region movement, source-region threat projection, deployment-zone source
  identity, invalid source blockers, empty source-region blockers, raw-range invariance, source
  marker rendering, web POST without point source fields, and desktop source-mode controls.
- Added `LosAnalysisState`, canonical `/los` GET/POST behavior, `los_analysis.html`, and a desktop
  `Line of Sight` screen.
- Added `movement_envelope_from_region(...)` with multi-source routing for non-mobile profiles and
  deterministic source-region cache keys.
- Added `threat_projection_regions_from_source_region(...)` and threaded source mode, source zone,
  source region, and source label through domain payloads, services, rendering, web, and desktop.
- Rendering now shows a deployment threat source-region indicator instead of a point source base
  marker when deployment-zone source mode is selected.

Verification completed so far:

- LOS implementation commit `95d9f11` passed the focused LOS tests and the affected
  application/web/desktop batch: 81 passed with the existing Starlette `TestClient` deprecation
  warning.
- Focused threat deployment-source tests passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py tests\test_threat_range_toolkit.py tests\test_rendering_svg.py::test_threat_source_region_renders_without_point_source_marker tests\test_application_service.py::test_threat_range_state_supports_deployment_zone_source_without_point_marker tests\test_web_server.py::test_threat_range_route_renders_deployment_zone_source_without_javascript tests\test_web_server.py::test_threat_range_post_deployment_zone_source_does_not_require_point_fields tests\test_desktop_app.py::test_desktop_threat_range_screen_supports_deployment_zone_source -q`
  returned 34 passed.
- Affected application/rendering/web/desktop/threat batch passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_threat_range_geometry.py tests\test_threat_range_toolkit.py tests\test_rendering_svg.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q`
  returned 131 passed with the existing Starlette `TestClient` deprecation warning.

Remaining before closeout:

- Run protected-artifact scan, adversarial implementation review, and final commit.

Final validation:

- Static gates passed:
  `.\.venv\Scripts\python.exe -m ruff format --check src tests`,
  `.\.venv\Scripts\python.exe -m ruff check .`, and `.\.venv\Scripts\mypy.exe src`.
- Full pytest passed:
  `.\.venv\Scripts\python.exe -m pytest` returned 484 passed with the existing Starlette
  `TestClient` deprecation warning.
- Packet validation passed for all 45 packaged official Event Companion packets:
  `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets`.
- Desktop smoke passed with `status: ok`, 45 bundled seed packets, `los_svg: true`,
  `heatmap_svg: true`, and `threat_range_svg: true`.
- `git diff --check` passed with the normal CRLF warnings for touched files.

Adversarial implementation review:

- Initial implementation review returned `CHANGES_REQUIRED` for three acceptance failures:
  inactive `/los` fields were parsed too early by FastAPI, deployment-zone Threat Range still
  parsed malformed point fields too early, and desktop Threat Range showed point and zone source
  controls at the same time.
- Fixed web route parsing so `/los` and `/threat-range` parse only active mode/source fields.
  Active malformed numeric fields remain rejected; inactive stale fields are ignored.
- Fixed desktop Threat Range controls so deployment-zone mode shows the zone selector and hides
  point Source X/Y controls, while point mode does the inverse.
- Added regression tests for malformed inactive `/los` GET/POST fields, malformed ignored point
  fields in deployment-zone Threat Range GET/POST, and desktop source-control visibility.
- Post-fix focused regressions passed: 5 passed.
- Post-fix affected suite passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_web_server.py tests\test_desktop_app.py tests\test_threat_range_toolkit.py tests\test_threat_range_geometry.py tests\test_application_service.py tests\test_rendering_svg.py -q`
  returned 135 passed with the existing Starlette `TestClient` deprecation warning.
- Post-fix static checks passed:
  `.\.venv\Scripts\python.exe -m ruff format --check src tests`,
  `.\.venv\Scripts\python.exe -m ruff check .`, and `.\.venv\Scripts\mypy.exe src`.
- Adversarial re-review approved the fixes. The reviewer independently confirmed inactive malformed
  fields return rendered pages, active malformed fields still return 422, and desktop source
  controls hide/show by source mode.
- Final full pytest after the reviewer fixes passed:
  `.\.venv\Scripts\python.exe -m pytest` returned 488 passed with the existing Starlette
  `TestClient` deprecation warning.
- Final packet validation, desktop smoke, and `git diff --check` passed after the reviewer fixes.

Manual QA status:

- The current app version was launched successfully on `http://127.0.0.1:8056` because port 8000
  was already occupied by an older Python process serving a stale app version where `/los` returned
  404.
- Built-in Browser setup succeeded, but both background and visible tab attempts failed with
  `Timed out waiting for the Browser webview to attach for this browser-use page`.
- Browser troubleshooting guidance did not expose another recovery path beyond confirming the
  selected Browser workflow was attempted.
- Computer Use setup succeeded and Firefox was discoverable, but launching Firefox stopped
  immediately because browser URL-policy enforcement is not supported for the current Windows
  browser.
- Fallback FastAPI rendered-route QA passed for:
  - `/los`, `/los?mode=checker...`, and `/los?mode=heatmap...` with no script tags;
  - old `/heatmap` and `/los-checker` redirects to canonical `/los` with preserved values;
  - web navigation containing exactly one `/los` `Line of Sight` link and no old LOS nav entries;
  - Threat Range point source mode rendering `threat-source-base` and no source region;
  - Threat Range deployment-zone source mode rendering `threat-source-region`, no
    `threat-source-base`, deployment source labels, selected source-zone controls, and
    `threat-projection-image`;
  - page 9 and page 52 deployment-zone threat source smoke routes;
  - POSTing deployment-zone source mode without `source_x`/`source_y`, with the redirect preserving
    source mode and zone while omitting point-source fields.
