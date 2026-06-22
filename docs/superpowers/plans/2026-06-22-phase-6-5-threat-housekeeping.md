# Phase 6.5 Threat Housekeeping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove duplicated circular-base board-fit geometry introduced by Phase 6 while preserving
movement reach, threat range, web, desktop, rendering, and toolkit behavior.

**Architecture:** Keep the shared geometry helper in `warhammer_companion.los.movement` because it
is geometry logic consumed by movement and threat tools. Keep application-layer threat validation as
the caller that turns geometry facts into `BlockReason` records.

**Tech Stack:** Python 3.12, Shapely, pytest, Ruff, mypy.

---

## File Map

- Modify: `src/warhammer_companion/los/movement.py`
- Modify: `src/warhammer_companion/application/threat_range.py`
- Modify: `tests/test_movement_reach_geometry.py`
- Modify: `tests/test_threat_range_toolkit.py` only if a behavior lock needs tightening
- Create/update: Phase 6.5 review and QA docs
- Modify: `docs/work-log/player-toolkit-implementation.md`

## Task 1: Shared Base-Center Region Helper

- [ ] Add a failing test in `tests/test_movement_reach_geometry.py` importing
  `base_center_region(...)` and proving:
  - a 2-inch base on a 10 x 10 board produces bounds `(1, 1, 9, 9)`;
  - the region covers `(1, 1)` but not `(0.99, 5)`;
  - an oversized base collapses to the board center under the existing private-helper behavior.
- [ ] Run the focused test and confirm it fails because `base_center_region` is not public.
- [ ] Rename private `_board_center_region(...)` to public `base_center_region(...)`.
- [ ] Update `movement_envelope(...)` and `movement_endpoint_diagnostic(...)` to use the public
  helper.
- [ ] Keep the existing nonnegative radius validation and oversized-base behavior.

## Task 2: Threat Validation Reuse

- [ ] Update `application/threat_range.py` to import `base_center_region(...)` instead of
  recomputing the board-center region locally.
- [ ] Remove the duplicate private `_source_base_within_board(...)` helper and now-unused Shapely
  imports.
- [ ] Run focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_threat_range_toolkit.py -q
```

Expected: movement and threat validation behavior is unchanged.

## Task 3: Review, QA, And Commit

- [ ] Record consultant and adversarial review outcomes.
- [ ] Run validation:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_threat_range_toolkit.py tests\test_application_service.py -q
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

- [ ] Run Browser QA for `/movement-reach` and `/threat-range` if implementation touches runtime
  behavior; otherwise record why Browser QA is not required for a pure helper refactor.
- [ ] Protected-path scan confirms no generated/raw/Codex/credential artifacts and `AGENTS.md`
  unstaged.
- [ ] Commit with:

```powershell
git commit -m "Housekeep threat board geometry"
```
