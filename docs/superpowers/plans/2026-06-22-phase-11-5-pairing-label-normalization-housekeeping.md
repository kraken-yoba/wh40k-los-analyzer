# Phase 11.5 Pairing Label Normalization Housekeeping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract Team Pairing label normalization into a reusable helper without changing Phase 11A
behavior.

**Architecture:** Add a small application helper and keep the matrix builder responsible for matrix
assembly. Characterization tests lock normalized labels, blocker ids, and input hashes before the
refactor.

**Tech Stack:** Python 3.12, dataclasses, pytest, Ruff, mypy.

---

## Task 1: Characterization Tests

**Files:**

- Modify: `tests/test_matchup_matrix_toolkit.py`

- [ ] Add a test that locks the current valid default input hash and result id for:
  - friendly labels `("Alpha", "Beta")`;
  - opponent labels `("Gamma", "Delta")`;
  - current default damage, mission, and deployment source results.
- [ ] Add a test that locks current blocked input hashes and result ids for:
  - missing friendly labels;
  - too many friendly labels;
  - duplicate friendly labels;
  - overlong friendly label.
- [ ] Add a test that locks normalized label outputs for:
  - `"Alpha  Prime,,  Beta\nControl\x07Name"`;
  - `"Gamma,, Delta"`.
- [ ] Add a test that locks blocker ids for missing labels, overflow labels, duplicate labels, and
  overlong labels.
- [ ] Run the focused new/changed tests before refactor and confirm they pass against current
  behavior.

## Task 2: Extract Helper

**Files:**

- Create: `src/warhammer_companion/application/pairing_labels.py`
- Modify: `src/warhammer_companion/application/matchup_matrix.py`

- [ ] Create `PairingLabelNormalizationResult` with:
  - `entries: tuple[PairingListEntry, ...]`;
  - `block_reasons: tuple[BlockReason, ...]`.
- [ ] Move constants `MAX_PAIRING_LABELS_PER_SIDE` and `MAX_PAIRING_LABEL_LENGTH` into the helper.
- [ ] Move the label parsing/normalization functions into the helper.
- [ ] Replace `_normalize_list_entries(...)` calls in `matchup_matrix.py` with
  `normalize_pairing_list_entries(...)`.
- [ ] Remove now-private label parsing functions from `matchup_matrix.py`.
- [ ] Do not change warning/detail copy, blocker ids, input hash payload, result id format,
  readiness, component assembly, or UI surfaces.

## Task 3: Verification And Review

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_matchup_matrix_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

- [ ] Run manual route QA for `/team-pairing` and blocked/normalization routes. Use Browser if
  available; otherwise document the blocker and use the Phase 11A TestClient fallback.
- [ ] Run consultant/spec-compliance and adversarial implementation review.
- [ ] Run protected-path and new-content source/credential scans.
- [ ] Update `docs/work-log/player-toolkit-implementation.md`.
- [ ] Stage only intended Phase 11.5 files and leave `AGENTS.md` untracked.
- [ ] Commit as one atomic Phase 11.5 housekeeping commit.
