# Source Pack Registry And Current RulesPack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add metadata-only source-pack and rules-pack foundation objects that later toolkit solvers can query before making rules-sensitive claims.

**Architecture:** Implement pure dataclass models and a deterministic builder under `warhammer_companion.ingestion`. The default builder does not perform network calls. A separately invoked, injectable remote verifier may stream bytes and compute hashes for future refresh workflows; no raw PDFs, copied rules text, UI changes, or generated packs are introduced in this slice.

**Tech Stack:** Python 3.12 dataclasses, Ruff, mypy strict mode, pytest.

---

### Task 1: Add Source/Rules Foundation Tests

**Files:**
- Create: `tests/test_rules_sources.py`

- [ ] **Step 1: Add tests for the current source/rules foundation**

Create tests that import `build_current_rules_foundation`, inspect source refs, check MFM
freshness metadata, prove concepts are source-pending, and enforce legacy assumption blockers.

- [ ] **Step 2: Run tests and verify they fail before implementation**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rules_sources.py -q
```

Expected before implementation: import failure or missing object failure.

### Task 2: Implement Source/Rules Foundation Models

**Files:**
- Create: `src/warhammer_companion/ingestion/rules_sources.py`

- [ ] **Step 1: Add typed dataclasses and literals**

Implement `SourceRef`, `SourcePackEntry`, `SourcePackRegistry`, `RulesConcept`, `RulesPack`, and
`SourceRulesFoundation`. Add `verify_remote_http_source()` as an explicitly invoked verifier that
streams remote content, computes SHA-256, records byte size/content type/final URL, and fails closed
on unsafe source kinds or non-200 responses.

- [ ] **Step 2: Add current foundation builder**

Implement `build_current_rules_foundation()` with current metadata:

- MFM version `v1.0`
- MFM updated date `2026-06-17`
- core rules PDF source URL
- Warhammer downloads page source URL
- New Recruit and BSData community references
- source-pending concept IDs
- legacy assumption blacklist keys

- [ ] **Step 3: Run targeted tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rules_sources.py -q
```

Expected: tests pass.

### Task 3: Add Documentation And QA Artifacts

**Files:**
- Create: `docs/superpowers/specs/2026-06-20-source-pack-registry-and-rulespack-current-spec.md`
- Create: `docs/superpowers/plans/2026-06-20-source-pack-registry-and-rulespack-current.md`
- Create: `docs/superpowers/qa/2026-06-20-source-pack-registry-and-rulespack-current-qa.md`
- Create: `docs/superpowers/reviews/2026-06-20-phase-1-consultant-source-foundation.md`
- Create: `docs/superpowers/reviews/2026-06-20-phase-1-adversarial-source-foundation.md`
- Modify: `docs/work-log/player-toolkit-implementation.md`

- [ ] **Step 1: Record scope and verification**

The docs must say this slice is metadata-only, not rules ingestion or source redistribution.

- [ ] **Step 2: Verify artifacts exist**

Run:

```powershell
$paths = @(
  'docs\superpowers\specs\2026-06-20-source-pack-registry-and-rulespack-current-spec.md',
  'docs\superpowers\plans\2026-06-20-source-pack-registry-and-rulespack-current.md',
  'docs\superpowers\qa\2026-06-20-source-pack-registry-and-rulespack-current-qa.md',
  'docs\superpowers\reviews\2026-06-20-phase-1-consultant-source-foundation.md',
  'docs\superpowers\reviews\2026-06-20-phase-1-adversarial-source-foundation.md',
  'docs\work-log\player-toolkit-implementation.md'
)
foreach ($path in $paths) {
  if (-not (Test-Path $path)) { throw "Missing Phase 1 artifact: $path" }
}
```

Expected: command exits with no error.

### Task 4: Review And Verify

**Files:**
- Review all Phase 1 changed files.

- [ ] **Step 1: Dispatch consultant and adversarial reviews**

Ask consultant and adversarial subagents to review source freshness, source-trust/IP/security scope,
architecture placement, tests, and QA executability.

Expected: reviewers return `APPROVED` or `CHANGES_REQUIRED`.

- [ ] **Step 2: Patch and re-review until approved**

Apply accepted reviewer fixes and rerun affected checks.

Expected: all reviewers return `APPROVED`.

- [ ] **Step 3: Run verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Expected: all commands pass.

### Task 5: Commit Phase 1 Checkpoint

**Files:**
- Stage only Phase 1 artifacts and implementation files.

- [ ] **Step 1: Stage exact files**

Run:

```powershell
git add src\warhammer_companion\ingestion\rules_sources.py tests\test_rules_sources.py docs\superpowers\specs\2026-06-20-source-pack-registry-and-rulespack-current-spec.md docs\superpowers\plans\2026-06-20-source-pack-registry-and-rulespack-current.md docs\superpowers\qa\2026-06-20-source-pack-registry-and-rulespack-current-qa.md docs\superpowers\reviews\2026-06-20-phase-1-consultant-source-foundation.md docs\superpowers\reviews\2026-06-20-phase-1-adversarial-source-foundation.md docs\work-log\player-toolkit-implementation.md
```

Expected: only Phase 1 files are staged; `AGENTS.md` remains unstaged.

- [ ] **Step 2: Commit**

Run:

```powershell
git commit -m "Add phase 1 source rules foundation"
```

Expected: commit succeeds.

- [ ] **Step 3: Verify post-commit state**

Run:

```powershell
git log -1 --oneline
git status --short --branch --untracked-files=all
```

Expected: latest commit is `Add phase 1 source rules foundation`; only user-owned untracked
`AGENTS.md` may remain visible.
