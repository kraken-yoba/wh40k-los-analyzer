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
