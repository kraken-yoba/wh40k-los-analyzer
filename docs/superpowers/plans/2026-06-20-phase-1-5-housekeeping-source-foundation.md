# Phase 1.5 Housekeeping Source Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Phase 1 remote-verifier test helper contract explicit without changing behavior.

**Architecture:** This housekeeping slice touches only tests and documentation. It imports the existing `RemoteGet` protocol and uses it as the return type for `_fake_get_factory()`.

**Tech Stack:** Python 3.12, pytest, Ruff, mypy.

---

### Task 1: Apply Test Helper Typing Cleanup

**Files:**
- Modify: `tests/test_rules_sources.py`

- [ ] **Step 1: Import `RemoteGet`**

Add `RemoteGet` to the existing import from `warhammer_companion.ingestion.rules_sources`.

- [ ] **Step 2: Type the fake getter factory**

Change `_fake_get_factory(response: _FakeResponse) -> object` to
`_fake_get_factory(response: _FakeResponse) -> RemoteGet`.

- [ ] **Step 3: Run targeted verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rules_sources.py -q
.\.venv\Scripts\mypy.exe tests\test_rules_sources.py
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
```

Expected: all commands pass.

### Task 2: Review And Commit

**Files:**
- Create: `docs/superpowers/specs/2026-06-20-phase-1-5-housekeeping-source-foundation.md`
- Create: `docs/superpowers/plans/2026-06-20-phase-1-5-housekeeping-source-foundation.md`
- Create: `docs/superpowers/qa/2026-06-20-phase-1-5-housekeeping-source-foundation-qa.md`
- Create: `docs/superpowers/reviews/2026-06-20-phase-1-5-consultant-source-foundation.md`
- Create: `docs/superpowers/reviews/2026-06-20-phase-1-5-adversarial-source-foundation.md`
- Modify: `docs/work-log/player-toolkit-implementation.md`
- Modify: `tests/test_rules_sources.py`

- [ ] **Step 1: Record review approvals**

Consultant and adversarial reviewers must return `APPROVED` or `CHANGES_REQUIRED`.

- [ ] **Step 2: Stage exact files**

Run:

```powershell
git add tests\test_rules_sources.py docs\superpowers\specs\2026-06-20-phase-1-5-housekeeping-source-foundation.md docs\superpowers\plans\2026-06-20-phase-1-5-housekeeping-source-foundation.md docs\superpowers\qa\2026-06-20-phase-1-5-housekeeping-source-foundation-qa.md docs\superpowers\reviews\2026-06-20-phase-1-5-consultant-source-foundation.md docs\superpowers\reviews\2026-06-20-phase-1-5-adversarial-source-foundation.md docs\work-log\player-toolkit-implementation.md
```

Expected: only Phase 1.5 files are staged; `AGENTS.md` is not staged.

- [ ] **Step 3: Commit**

Run:

```powershell
git commit -m "Housekeep phase 1.5 source foundation tests"
```

Expected: commit succeeds.
