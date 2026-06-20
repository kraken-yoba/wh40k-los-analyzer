# Phase 0 Implementation Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the preparatory documentation, QA pathway, review records, work log, and review gates needed before implementing Phase 1 of the player-toolkit roadmap.

**Architecture:** Phase 0 is behavior-preserving documentation scaffolding. It adds a phase-specific design spec, this execution plan, an autonomous QA pathway, durable review records, a program work log, and a roadmap QA note while leaving Python runtime code, web UI, desktop UI, generated data, and packaging behavior unchanged.

**Tech Stack:** Markdown documentation, Git, PowerShell, existing Python verification commands where needed.

---

### Task 1: Confirm Phase 0 Scope

**Files:**
- Read: `AGENTS.md`
- Read: `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`
- Read: `docs/qa-scenarios.md`
- Read: `docs/work-log/official-ingestion.md`
- Read: `docs/work-log/desktop-app.md`

- [ ] **Step 1: Inspect current state**

Run:

```powershell
git status --short --branch
```

Expected: current branch is visible. Any untracked user-owned files are noted and not staged unless explicitly part of Phase 0.

- [ ] **Step 2: Read repo instructions**

Run:

```powershell
Get-Content -LiteralPath AGENTS.md
```

Expected: instructions confirm Python-first architecture, no custom frontend JavaScript, no committed official PDFs, and service-layer boundaries.

- [ ] **Step 3: Read the parent roadmap**

Run:

```powershell
Get-Content -LiteralPath docs\superpowers\specs\2026-06-19-player-toolkit-assistant-roadmap-design.md
```

Expected: parent roadmap lists Phase 1 as `source-pack-registry-and-rulespack-current-spec.md` and requires implementation not to begin until the first fine-grain spec is approved.

### Task 2: Add Phase 0 Design Spec

**Files:**
- Create: `docs/superpowers/specs/2026-06-19-phase-0-implementation-readiness-design.md`

- [ ] **Step 1: Create the design file**

Add a design spec that states Phase 0 is documentation scaffolding only, lists required artifacts, defines the phase execution protocol, defines `.5` housekeeping loops, records design decisions, and sets Phase 0 acceptance criteria.

- [ ] **Step 2: Verify the design exists**

Run:

```powershell
Test-Path docs\superpowers\specs\2026-06-19-phase-0-implementation-readiness-design.md
```

Expected: `True`.

### Task 3: Add Phase 0 Plan

**Files:**
- Create: `docs/superpowers/plans/2026-06-19-phase-0-implementation-readiness.md`

- [ ] **Step 1: Create the plan file**

Add a Superpowers-compatible plan with the required header, concrete tasks, exact file paths, commands, expected results, review gates, QA execution, work-log update, and commit steps.

- [ ] **Step 2: Verify the plan header**

Run:

```powershell
Select-String -Path docs\superpowers\plans\2026-06-19-phase-0-implementation-readiness.md -Pattern 'REQUIRED SUB-SKILL|Goal:|Architecture:|Tech Stack:'
```

Expected: all required header fields appear.

### Task 4: Add Autonomous QA Pathway

**Files:**
- Create: `docs/superpowers/qa/2026-06-19-phase-0-implementation-readiness-qa.md`
- Modify: `docs/qa-scenarios.md`

- [ ] **Step 1: Create the QA file**

Add an autonomous QA pathway with preconditions, exact checks, expected evidence, browser/computer-use applicability, reviewer approval checks, and a reusable template for later phases.

- [ ] **Step 2: Verify autonomous commands are present**

Run:

```powershell
Select-String -Path docs\superpowers\qa\2026-06-19-phase-0-implementation-readiness-qa.md -Pattern 'git status --short --branch|git diff --check|Select-String|Browser|Computer Use'
```

Expected: the QA pathway includes Git, draft-marker, diff, and browser/computer-use decision checks.

- [ ] **Step 3: Add roadmap phase QA expectations**

Update `docs/qa-scenarios.md` with a Roadmap Phase QA section that requires phase-specific specs, plans, QA pathways, consultant review, adversarial review, work-log evidence, freshness/source-refresh checks for mutable external data, browser/computer-use checks when behavior changes, and page 9/page 52 regression checks when map overlays are affected.

- [ ] **Step 4: Verify the shared QA section exists**

Run:

```powershell
Select-String -Path docs\qa-scenarios.md -Pattern 'Roadmap Phase QA|phase-specific QA pathway|adversarial review|page 9|page 52'
```

Expected: the roadmap phase QA section is found.

### Task 5: Add Program Work Log

**Files:**
- Create or modify: `docs/work-log/player-toolkit-implementation.md`

- [ ] **Step 1: Create the work log**

Add a factual entry for Phase 0 with branch, purpose, artifacts, design decisions, consultant/adversarial review requirements, verification commands, and known nonblocking notes.

- [ ] **Step 2: Verify work-log entry exists**

Run:

```powershell
Select-String -Path docs\work-log\player-toolkit-implementation.md -Pattern 'Phase 0 - Implementation Readiness|Artifacts|Verification'
```

Expected: the Phase 0 entry is found.

### Task 6: Consultant And Adversarial Review

**Files:**
- Review: `docs/superpowers/specs/2026-06-19-phase-0-implementation-readiness-design.md`
- Review: `docs/superpowers/plans/2026-06-19-phase-0-implementation-readiness.md`
- Review: `docs/superpowers/qa/2026-06-19-phase-0-implementation-readiness-qa.md`
- Review: `docs/qa-scenarios.md`
- Review: `docs/work-log/player-toolkit-implementation.md`
- Create: `docs/superpowers/reviews/2026-06-19-phase-0-consultant-readiness.md`
- Create: `docs/superpowers/reviews/2026-06-19-phase-0-adversarial-readiness.md`

- [ ] **Step 1: Dispatch consultant review**

Ask a consultant subagent to review whether the Phase 0 artifacts are sufficient to start Phase 1 without hidden process gaps.

Expected: reviewer returns `APPROVED` or `CHANGES_REQUIRED`.

- [ ] **Step 2: Record consultant review**

Write consultant findings, accepted changes, and final status to:

```text
docs/superpowers/reviews/2026-06-19-phase-0-consultant-readiness.md
```

- [ ] **Step 3: Dispatch adversarial review**

Ask an adversarial subagent to review whether Phase 0 accidentally starts Phase 1, lacks proof gates, misses security/source-trust issues, or leaves QA non-executable.

Expected: reviewer returns `APPROVED` or `CHANGES_REQUIRED`.

- [ ] **Step 4: Triage and patch**

For each `CHANGES_REQUIRED` item, verify it against the artifacts, patch accepted fixes, and document any reasoned pushback in the work log.

Expected: all reviewers eventually return `APPROVED`.

- [ ] **Step 5: Record adversarial review**

Write adversarial findings, accepted changes, and final status to:

```text
docs/superpowers/reviews/2026-06-19-phase-0-adversarial-readiness.md
```

### Task 7: Local Verification

**Files:**
- Verify all Phase 0 artifacts.

- [ ] **Step 1: Draft-marker scan**

Run:

```powershell
$pattern = ('TB' + 'D|TO' + 'DO|FIX' + 'ME|\?\?')
Select-String -Path docs\superpowers\specs\2026-06-19-phase-0-implementation-readiness-design.md,docs\superpowers\plans\2026-06-19-phase-0-implementation-readiness.md,docs\superpowers\qa\2026-06-19-phase-0-implementation-readiness-qa.md,docs\superpowers\reviews\2026-06-19-phase-0-consultant-readiness.md,docs\superpowers\reviews\2026-06-19-phase-0-adversarial-readiness.md,docs\work-log\player-toolkit-implementation.md,docs\qa-scenarios.md -Pattern $pattern
```

Expected: no matches.

- [ ] **Step 2: ASCII scan**

Run:

```powershell
$paths = @(
  'docs\superpowers\specs\2026-06-19-phase-0-implementation-readiness-design.md',
  'docs\superpowers\plans\2026-06-19-phase-0-implementation-readiness.md',
  'docs\superpowers\qa\2026-06-19-phase-0-implementation-readiness-qa.md',
  'docs\superpowers\reviews\2026-06-19-phase-0-consultant-readiness.md',
  'docs\superpowers\reviews\2026-06-19-phase-0-adversarial-readiness.md',
  'docs\work-log\player-toolkit-implementation.md',
  'docs\qa-scenarios.md'
)
foreach ($path in $paths) {
  $content = Get-Content -LiteralPath $path -Raw
  $matches = [regex]::Matches($content, '[^\x00-\x7F]')
  if ($matches.Count -gt 0) { "$path has non-ASCII" }
}
```

Expected: no output.

- [ ] **Step 3: Diff check**

Run:

```powershell
git diff --check
```

Expected: no whitespace errors.

- [ ] **Step 4: Behavior-change check**

Run:

```powershell
$allowedPhase0 = @(
  'docs/qa-scenarios.md',
  'docs/superpowers/plans/2026-06-19-phase-0-implementation-readiness.md',
  'docs/superpowers/qa/2026-06-19-phase-0-implementation-readiness-qa.md',
  'docs/superpowers/reviews/2026-06-19-phase-0-adversarial-readiness.md',
  'docs/superpowers/reviews/2026-06-19-phase-0-consultant-readiness.md',
  'docs/superpowers/specs/2026-06-19-phase-0-implementation-readiness-design.md',
  'docs/work-log/player-toolkit-implementation.md'
)
$allowedUserOwnedUntracked = @('AGENTS.md')
$modified = @(git diff --name-only)
$staged = @(git diff --cached --name-only)
$untracked = @(git ls-files --others --exclude-standard)
$allVisible = @($modified + $staged + $untracked) |
  Where-Object { $_ } |
  Sort-Object -Unique
$unexpected = $allVisible | Where-Object {
  ($_ -notin $allowedPhase0) -and ($_ -notin $allowedUserOwnedUntracked)
}
if ($unexpected) { throw "Unexpected changed/untracked files: $($unexpected -join ', ')" }
if ($staged -contains 'AGENTS.md') { throw 'AGENTS.md is user-owned and must not be staged' }
```

Expected: only Phase 0 documentation files are listed or staged. `AGENTS.md` may remain untracked
and user-owned, but it must not be staged.

- [ ] **Step 5: Optional baseline guard**

If `.venv\Scripts\python.exe` exists, run the optional baseline commands listed in the Phase 0 QA
pathway. Record pass/fail output in the work log. Do not auto-fix source files inside Phase 0 if a
baseline command fails against untouched runtime files; defer that to a later `.5` housekeeping
loop unless reviewers decide it blocks readiness.

### Task 8: Commit Phase 0 Checkpoint

**Files:**
- Stage only Phase 0 artifacts.

- [ ] **Step 1: Stage Phase 0 files**

Run:

```powershell
git add docs\superpowers\specs\2026-06-19-phase-0-implementation-readiness-design.md docs\superpowers\plans\2026-06-19-phase-0-implementation-readiness.md docs\superpowers\qa\2026-06-19-phase-0-implementation-readiness-qa.md docs\superpowers\reviews\2026-06-19-phase-0-consultant-readiness.md docs\superpowers\reviews\2026-06-19-phase-0-adversarial-readiness.md docs\work-log\player-toolkit-implementation.md docs\qa-scenarios.md
```

Expected: only Phase 0 artifacts are staged.

- [ ] **Step 2: Verify staged files**

Run:

```powershell
git diff --cached --name-only
```

Expected:

The staged file set is exactly the seven Phase 0 artifacts above, in any order. `AGENTS.md` must
not be staged.

- [ ] **Step 3: Commit**

Run:

```powershell
git commit -m "Add phase 0 implementation readiness"
```

Expected: commit succeeds with the Phase 0 documentation artifacts.

- [ ] **Step 4: Verify post-commit state**

Run:

```powershell
git log -1 --oneline
git status --short --branch --untracked-files=all
```

Expected: the latest commit is `Add phase 0 implementation readiness`. There are no staged files.
The only remaining visible untracked file may be user-owned `AGENTS.md`.
