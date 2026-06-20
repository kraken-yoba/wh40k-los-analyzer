# Phase 2.5 LOS Toolkit Housekeeping QA Pathway

Date: 2026-06-20

## Goal

Prove the LOS toolkit extraction is behavior-preserving and keeps service/rendering behavior
unchanged.

## Commands

```powershell
git status --short --branch
```

Expected: branch is `codex/assistant-companion-roadmap`; `AGENTS.md` may be untracked and must not
be staged.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_los_toolkit.py tests\test_application_service.py tests\test_toolkit_contracts.py tests\test_board_state.py -q
```

Expected: extracted builder and existing Phase 2 contracts pass.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_los_toolkit.py tests\test_application_service.py tests\test_los_geometry.py tests\test_rendering_svg.py -q
```

Expected: LOS service, LOS geometry, and SVG rendering regressions pass.

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
git diff --check
git diff --cached --check
```

Expected: all checks pass.

## Review Gates

- Consultant review confirms the extraction is warranted and appropriately scoped.
- Adversarial review confirms no behavior change, dependency inversion, identity regression, or
  test gap remains.

## Browser And Computer Use

Not required. This housekeeping slice changes no web route, template, static asset, generated SVG
behavior, desktop widget, installer, OS interaction, or packaged UI behavior. Existing service and
rendering tests prove behavior preservation.

## Commit Gate

Staged files must be limited to:

- `docs/superpowers/specs/2026-06-20-phase-2-5-housekeeping-los-toolkit.md`
- `docs/superpowers/plans/2026-06-20-phase-2-5-housekeeping-los-toolkit.md`
- `docs/superpowers/qa/2026-06-20-phase-2-5-housekeeping-los-toolkit-qa.md`
- `docs/superpowers/reviews/2026-06-20-phase-2-5-consultant-los-toolkit.md`
- `docs/superpowers/reviews/2026-06-20-phase-2-5-adversarial-los-toolkit.md`
- `docs/work-log/player-toolkit-implementation.md`
- `src/warhammer_companion/application/los_toolkit.py`
- `src/warhammer_companion/application/services.py`
- `tests/test_los_toolkit.py`

`AGENTS.md` must remain unstaged unless the user explicitly requests otherwise.
