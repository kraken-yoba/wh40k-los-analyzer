# Toolkit Result And Board State QA Pathway

Date: 2026-06-20

## Goal

Prove Phase 2 adds shared toolkit result and board-state primitives without changing existing LOS,
rendering, web, desktop, ingestion, or packet behavior.

## Preconditions

- Working directory resolves to the repository root.
- Branch is `codex/assistant-companion-roadmap`.
- `AGENTS.md` may be untracked and must not be staged unless the user explicitly asks.
- The local virtual environment exists at `.\.venv`.

## Required Evidence

1. Phase 2 docs exist:
   - `docs/superpowers/specs/2026-06-20-toolkit-result-and-board-state-spec.md`
   - `docs/superpowers/plans/2026-06-20-toolkit-result-and-board-state.md`
   - `docs/superpowers/qa/2026-06-20-toolkit-result-and-board-state-qa.md`
   - `docs/superpowers/reviews/2026-06-20-phase-2-consultant-toolkit-foundation.md`
   - `docs/superpowers/reviews/2026-06-20-phase-2-adversarial-toolkit-foundation.md`
2. New domain/application modules exist:
   - `src/warhammer_companion/domain/board_state.py`
   - `src/warhammer_companion/domain/overlays.py`
   - `src/warhammer_companion/application/toolkit.py`
3. New tests exist:
   - `tests/test_toolkit_contracts.py`
   - `tests/test_board_state.py`
4. Application service test records the LOS toolkit result before SVG projection:
   - `tests/test_application_service.py`
5. Work log records decisions, review triage, verification, and browser/desktop QA waiver.

## Commands

Run from repository root.

```powershell
git status --short --branch
```

Expected:

- Branch is `codex/assistant-companion-roadmap`.
- `AGENTS.md` may appear as untracked.
- No unrelated modified files are present.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_toolkit_contracts.py tests\test_board_state.py tests\test_application_service.py -q
```

Expected: all Phase 2 unit tests pass.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_toolkit_contracts.py tests\test_board_state.py tests\test_application_service.py tests\test_los_geometry.py tests\test_rendering_svg.py -q
```

Expected: toolkit, LOS, and SVG rendering regression tests pass.

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
```

Expected: all style and type checks exit 0.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Expected: full test suite passes.

```powershell
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
```

Expected: all official seed packets validate.

```powershell
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Expected: desktop smoke status is `ok`.

```powershell
git diff --check
git diff --cached --check
```

Expected: no whitespace errors.

## Contract Checks

Inspect `tests/test_toolkit_contracts.py`, `tests/test_board_state.py`, and
`tests/test_application_service.py` and confirm coverage for:

- `ToolkitResult` readiness semantics and recommendation-language gate.
- `blocked` result with block reasons.
- `blocked` result rejection when block reasons are absent or overlays are present.
- `estimated` result with assumptions.
- `trusted` result with validation metadata.
- `trusted` result rejection when source refs or passed validation are absent.
- overlay readiness cannot exceed parent result readiness.
- `MapOverlayLayer` as Shapely geometry, not SVG or UI markup.
- `BoardState.from_packet()` preserving the exact `MapPacket` object.
- `BoardState.from_packet()` preserving `packet.model_dump()`.
- Missing model position and base size warnings.
- Units with empty model tuples producing explicit missing-model warnings.
- Full model data still remaining `estimated` until mechanics are source-backed.
- Existing LOS geometry equality before and after wrapping the packet in `BoardState`.
- `WarhammerCompanionService.los_checker_toolkit_result()` returns `ToolkitResult` before SVG
  projection.
- `WarhammerCompanionService.los_checker_toolkit_result()` includes packet content digest in its
  identity and does not mutate `MapPacket`.
- `WarhammerCompanionService.los_checker_state()` matches the legacy direct LOS render path.

## Browser And Computer Use

Not required for Phase 2 because no web route, template, static asset, generated SVG behavior,
desktop widget, installer, OS interaction, or packaged UI behavior changes. If any UI file changes
unexpectedly, this waiver is invalid and browser/desktop checks from `docs/qa-scenarios.md` must be
run for page 9 and page 52.

## Protected Content Scan

Run:

```powershell
rg -n "Games Workshop Limited|Copyright|datasheet|mission card|stratagem" src/warhammer_companion/application/toolkit.py src/warhammer_companion/domain/board_state.py src/warhammer_companion/domain/overlays.py src/warhammer_companion/application/services.py tests/test_toolkit_contracts.py tests/test_board_state.py tests/test_application_service.py docs/superpowers/specs/2026-06-20-toolkit-result-and-board-state-spec.md docs/superpowers/plans/2026-06-20-toolkit-result-and-board-state.md docs/superpowers/reviews/2026-06-20-phase-2-consultant-toolkit-foundation.md docs/superpowers/reviews/2026-06-20-phase-2-adversarial-toolkit-foundation.md docs/work-log/player-toolkit-implementation.md
```

Expected: no Phase 2 source or test file embeds protected source text. Incidental roadmap prose in
older docs is not a blocker unless new Phase 2 files contain copied protected text.

## Review Gates

Phase 2 is not complete until:

- Consultant review file says `Approved`.
- Adversarial review file says `Approved`.
- Any accepted reviewer issue has a corresponding code, test, or doc fix.
- The work log records final verification evidence.

## Commit Gate

Before commit:

```powershell
git diff --name-only
git diff --cached --name-only
```

Expected staged files are limited to:

- `docs/superpowers/specs/2026-06-20-toolkit-result-and-board-state-spec.md`
- `docs/superpowers/plans/2026-06-20-toolkit-result-and-board-state.md`
- `docs/superpowers/qa/2026-06-20-toolkit-result-and-board-state-qa.md`
- `docs/superpowers/reviews/2026-06-20-phase-2-consultant-toolkit-foundation.md`
- `docs/superpowers/reviews/2026-06-20-phase-2-adversarial-toolkit-foundation.md`
- `docs/work-log/player-toolkit-implementation.md`
- `src/warhammer_companion/domain/board_state.py`
- `src/warhammer_companion/domain/overlays.py`
- `src/warhammer_companion/application/toolkit.py`
- `src/warhammer_companion/application/services.py`
- `tests/test_toolkit_contracts.py`
- `tests/test_board_state.py`
- `tests/test_application_service.py`

`AGENTS.md` must remain unstaged unless the user explicitly requests otherwise.
