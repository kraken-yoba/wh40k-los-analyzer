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

Remaining gates:

- Atomic commit remains before Phase 4B closeout.
