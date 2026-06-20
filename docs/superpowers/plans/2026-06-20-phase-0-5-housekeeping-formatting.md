# Phase 0.5 Housekeeping Formatting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the known Ruff formatter drift in `src/warhammer_companion/los/geometry.py` and prove the cleanup is behavior-preserving before Phase 1.

**Architecture:** This is a housekeeping slice, not feature development. The only source change is Ruff formatter output in the LOS geometry module; documentation records the phase scope, QA, review evidence, and work-log outcomes.

**Tech Stack:** Python 3.12, Ruff, mypy, pytest, PowerShell, Git.

---

### Task 1: Confirm Housekeeping Scope

**Files:**
- Read: `AGENTS.md`
- Read: `docs/work-log/player-toolkit-implementation.md`
- Read: `docs/superpowers/specs/2026-06-20-phase-0-5-housekeeping-formatting-design.md`

- [ ] **Step 1: Inspect branch and visible changes**

Run:

```powershell
git status --short --branch --untracked-files=all
git log -1 --oneline
```

Expected: branch is `codex/assistant-companion-roadmap`; latest commit is the Phase 0 checkpoint;
only user-owned untracked `AGENTS.md` may be visible before Phase 0.5 edits.

- [ ] **Step 2: Confirm formatter drift**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Expected: command reports that `src\warhammer_companion\los\geometry.py` would be reformatted.

### Task 2: Create Phase 0.5 Documentation

**Files:**
- Create: `docs/superpowers/specs/2026-06-20-phase-0-5-housekeeping-formatting-design.md`
- Create: `docs/superpowers/plans/2026-06-20-phase-0-5-housekeeping-formatting.md`
- Create: `docs/superpowers/qa/2026-06-20-phase-0-5-housekeeping-formatting-qa.md`
- Create: `docs/superpowers/reviews/2026-06-20-phase-0-5-consultant-housekeeping.md`
- Create: `docs/superpowers/reviews/2026-06-20-phase-0-5-adversarial-housekeeping.md`
- Modify: `docs/work-log/player-toolkit-implementation.md`

- [ ] **Step 1: Add documentation artifacts**

Create the spec, this plan, QA pathway, review records, and work-log entry. The documents must state
that Phase 0.5 is formatter-only and behavior-preserving.

- [ ] **Step 2: Verify artifacts exist**

Run:

```powershell
$paths = @(
  'docs\superpowers\specs\2026-06-20-phase-0-5-housekeeping-formatting-design.md',
  'docs\superpowers\plans\2026-06-20-phase-0-5-housekeeping-formatting.md',
  'docs\superpowers\qa\2026-06-20-phase-0-5-housekeeping-formatting-qa.md',
  'docs\superpowers\reviews\2026-06-20-phase-0-5-consultant-housekeeping.md',
  'docs\superpowers\reviews\2026-06-20-phase-0-5-adversarial-housekeeping.md',
  'docs\work-log\player-toolkit-implementation.md'
)
foreach ($path in $paths) {
  if (-not (Test-Path $path)) { throw "Missing Phase 0.5 artifact: $path" }
}
```

Expected: command exits with no error.

### Task 3: Apply Ruff Formatting

**Files:**
- Modify: `src/warhammer_companion/los/geometry.py`

- [ ] **Step 1: Run Ruff formatter on the affected file**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format src\warhammer_companion\los\geometry.py
```

Expected: Ruff reformats `src\warhammer_companion\los\geometry.py`.

- [ ] **Step 2: Inspect source diff**

Run:

```powershell
git diff -- src\warhammer_companion\los\geometry.py
```

Expected: diff contains only formatter-owned layout changes. No identifiers, constants, function
calls, branching, calculations, imports, or behavior are changed.

### Task 4: Verify Behavior Preservation

**Files:**
- Verify all Phase 0.5 changes.

- [ ] **Step 1: Run formatting check**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Expected: all files are already formatted.

- [ ] **Step 2: Run static and test checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
```

Expected: all commands pass.

- [ ] **Step 3: Run packet and desktop smoke checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Expected: all 45 official seed packets validate and desktop smoke returns status `ok`.

- [ ] **Step 4: Verify diff scope**

Run:

```powershell
git diff --check
git status --short --branch --untracked-files=all
```

Expected: no whitespace errors. Visible changes are only Phase 0.5 docs, the formatted geometry
file, and user-owned untracked `AGENTS.md`.

### Task 5: Review And Commit

**Files:**
- Review all Phase 0.5 changed files.

- [ ] **Step 1: Dispatch consultant and adversarial review**

Ask consultant and adversarial subagents to approve the scope, diff, QA pathway, and verification
evidence. Reviewers must return `APPROVED` or `CHANGES_REQUIRED`.

Expected: reviewers approve or list blocking edits.

- [ ] **Step 2: Patch and re-review until approved**

Apply accepted reviewer fixes and re-run affected QA checks.

Expected: all reviewers return `APPROVED`.

- [ ] **Step 3: Stage exact Phase 0.5 files**

Run:

```powershell
git add docs\superpowers\specs\2026-06-20-phase-0-5-housekeeping-formatting-design.md docs\superpowers\plans\2026-06-20-phase-0-5-housekeeping-formatting.md docs\superpowers\qa\2026-06-20-phase-0-5-housekeeping-formatting-qa.md docs\superpowers\reviews\2026-06-20-phase-0-5-consultant-housekeeping.md docs\superpowers\reviews\2026-06-20-phase-0-5-adversarial-housekeeping.md docs\work-log\player-toolkit-implementation.md src\warhammer_companion\los\geometry.py
```

Expected: only Phase 0.5 files are staged; `AGENTS.md` is not staged.

- [ ] **Step 4: Commit**

Run:

```powershell
git commit -m "Housekeep phase 0.5 formatting baseline"
```

Expected: commit succeeds.

- [ ] **Step 5: Verify post-commit state**

Run:

```powershell
git log -1 --oneline
git status --short --branch --untracked-files=all
```

Expected: latest commit is `Housekeep phase 0.5 formatting baseline`; no staged files remain; the
only visible untracked file may be user-owned `AGENTS.md`.
