# Phase 4.5 Roster Snapshot Housekeeping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract Phase 4B roster snapshot/index builders into a focused application module without
changing roster import behavior.

**Architecture:** Keep durable roster records in `domain.rosters`, hostile byte/XML admission in
`ingestion`, and toolkit payload assembly in `application.roster_import`. Move pure application
builder functions to `application.roster_snapshots` so Phase 5 movement work can depend on a cleaner
roster boundary.

**Tech Stack:** Python 3.12, dataclasses, pytest, Ruff, mypy.

---

## File Structure

- Create: `src/warhammer_companion/application/roster_snapshots.py`
  - Own pure builder APIs for canonical army source refs, roster indexes, selection keys, snapshot
    profile packs, and snapshot pack hashes.
- Modify: `src/warhammer_companion/application/roster_import.py`
  - Replace private helper definitions with imports from `application.roster_snapshots`.
- Create: `tests/test_roster_snapshot_builders.py`
  - Direct contract tests for the extracted builder module.
- Create: `docs/superpowers/specs/2026-06-21-phase-4-5-roster-snapshot-housekeeping.md`
  - Phase spec and non-goals.
- Create: `docs/superpowers/qa/2026-06-21-phase-4-5-roster-snapshot-housekeeping-qa.md`
  - Autonomous QA path.
- Create: `docs/superpowers/reviews/2026-06-21-phase-4-5-consultant-roster-snapshot-housekeeping.md`
  - Consultant review record.
- Create: `docs/superpowers/reviews/2026-06-21-phase-4-5-adversarial-roster-snapshot-housekeeping.md`
  - Adversarial review record.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Record decisions, review triage, verification, and closeout.

## Task 1: Write Failing Direct Builder Tests

**Files:**

- Create: `tests/test_roster_snapshot_builders.py`

- [ ] **Step 1: Add the direct builder contract test**

Create `tests/test_roster_snapshot_builders.py` with a synthetic `CanonicalArmy` fixture that uses
only local test strings. Import:

```python
from warhammer_companion.application.roster_snapshots import (
    build_canonical_roster_index,
    build_roster_snapshot_profile_candidate_pack,
    canonical_army_with_source_refs,
)
```

Test behaviors:

- deep source-ref propagation reaches nested profiles, characteristics, rules, and child selections;
- roster index entries preserve depth, parent key, profile/rule/cost counts, and unresolved local
  candidate markers;
- snapshot profile pack hash is deterministic for identical inputs;
- snapshot profile pack hash changes when source refs change.

- [ ] **Step 2: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_builders.py -q
```

Expected: FAIL because `warhammer_companion.application.roster_snapshots` does not exist.

## Task 2: Extract Roster Snapshot Builders

**Files:**

- Create: `src/warhammer_companion/application/roster_snapshots.py`
- Modify: `src/warhammer_companion/application/roster_import.py`

- [ ] **Step 1: Create the builder module**

Move these behaviors from `application.roster_import` into
`application.roster_snapshots`:

- `_army_with_source_refs` as public `canonical_army_with_source_refs`;
- `_canonical_roster_index` as public `build_canonical_roster_index`;
- `_snapshot_profile_candidate_pack` as public `build_roster_snapshot_profile_candidate_pack`;
- `_profile_with_source_refs`, `_selection_with_source_refs`, `_selection_key`, and
  `_snapshot_pack_hash` as private helpers.

- [ ] **Step 2: Update roster import**

Update `build_roster_import_result_from_bytes(...)` to call the public builder functions. Keep the
same payload fields, readiness, warnings, block reasons, hashes, and result ids.

- [ ] **Step 3: Verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_builders.py -q
```

Expected: PASS.

## Task 3: Regression, Reviews, And Commit

**Files:**

- Modify: `docs/superpowers/reviews/2026-06-21-phase-4-5-consultant-roster-snapshot-housekeeping.md`
- Modify: `docs/superpowers/reviews/2026-06-21-phase-4-5-adversarial-roster-snapshot-housekeeping.md`
- Modify: `docs/work-log/player-toolkit-implementation.md`

- [ ] **Step 1: Run focused roster regressions**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_builders.py tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py -q
```

Expected: PASS.

- [ ] **Step 2: Run broader focused regressions**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_builders.py tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py tests\test_toolkit_contracts.py tests\test_rules_sources.py tests\test_base_sizes.py tests\test_terrain_semantics.py -q
```

Expected: PASS.

- [ ] **Step 3: Run static checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
```

Expected: all pass.

- [ ] **Step 4: Run consultant and adversarial implementation reviews**

Reviewers must check:

- the extraction is behavior preserving;
- no source-trust, roster authority, or readiness semantics changed;
- no UI, persistence, BoardState, movement, threat, damage, mission, analytics, or AI scope was
  added;
- direct builder tests are meaningful and not duplicate-only.

- [ ] **Step 5: Run full validation and manual QA**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Then run the established Browser route sweep against the local web app. If Browser fails, try
Computer Use with Firefox and record the exact blocker.

- [ ] **Step 6: Protected-artifact scan and commit**

Confirm no raw roster/profile/community/official data, logs, screenshots, generated databases,
Codex state, or `AGENTS.md` are staged.

Commit message:

```text
Housekeep roster snapshot builders
```
