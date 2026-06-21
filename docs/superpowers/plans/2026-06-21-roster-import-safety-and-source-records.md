# Roster Import Safety And Source Records Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a hostile-input-safe `.ros`/`.rosz` admission layer that records roster source provenance and creates a shallow canonical roster snapshot without profile resolution or tactical claims.

**Architecture:** Keep persistent data contracts in `domain.rosters`, hostile archive/XML admission helpers in `ingestion`, and the `ToolkitResult` builder in `application.roster_import`. Tests generate synthetic bytes in memory and never commit real roster/community data.

**Tech Stack:** Python 3.12, dataclasses, `zipfile`, `xml.etree.ElementTree` behind a fail-closed pre-screen gate, pytest, Ruff, mypy.

---

## File Structure

- Create: `src/warhammer_companion/domain/rosters.py`
  - Roster import source, archive member, cost, selection, canonical army, and payload records.
- Create: `src/warhammer_companion/ingestion/roster_archives.py`
  - In-memory `.rosz` inspection and archive safety validation.
- Create: `src/warhammer_companion/ingestion/roster_xml.py`
  - XML pre-screen gate and shallow roster/selection/cost extraction.
- Create: `src/warhammer_companion/application/roster_import.py`
  - `ToolkitResult` builder for `.ros` and `.rosz` bytes.
- Create: `tests/test_roster_import_safety.py`
  - Safe and malicious `.ros`/`.rosz` tests.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Record Phase 4A decisions, review triage, verification, and blockers.
- Create: `docs/superpowers/qa/2026-06-21-roster-import-safety-and-source-records-qa.md`
  - Autonomous QA pathway.
- Create: `docs/superpowers/reviews/2026-06-21-phase-4a-consultant-roster-import.md`
  - Consultant findings and final approval.
- Create: `docs/superpowers/reviews/2026-06-21-phase-4a-adversarial-roster-import.md`
  - Adversarial findings, triage, and final approval.

### Task 1: Write Failing Tests

- [ ] **Step 1: Add safe import tests**

In `tests/test_roster_import_safety.py`, add synthetic XML/ZIP tests proving:

- `.ros` bytes produce an estimated `ToolkitResult`.
- `.rosz` bytes with one safe `.ros` member produce an estimated `ToolkitResult`.
- The source record includes filename, source kind, byte size, SHA-256, selected member path, selected
  XML SHA-256, parser version, and schema version.
- The canonical army preserves roster ID/name/game-system ID/catalogue name, nested selections,
  raw selection IDs/names/types/source paths, and costs as presented.
- Import hashes change with filename, source kind, and source bytes.

- [ ] **Step 2: Add malicious archive/XML tests**

Add tests proving blocked results for:

- `.rosz` path traversal.
- `.rosz` absolute path.
- `.rosz` nested archive.
- `.rosz` encrypted member flag.
- `.rosz` unexpected extension.
- `.rosz` excessive member count.
- `.rosz` oversized uncompressed member.
- `.rosz` excessive decompression ratio.
- XML with malformed content, `DOCTYPE`, entity declaration/reference, XInclude, and HTTP URL.

Blocked results must contain block reasons, no canonical army, no overlays, and no recommendation
language.

- [ ] **Step 3: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_import_safety.py -q
```

Expected: FAIL because the Phase 4A modules do not exist.

### Task 2: Implement Domain And Ingestion Contracts

- [ ] **Step 1: Add domain records**

Create `src/warhammer_companion/domain/rosters.py` with immutable dataclasses:

- `RosterArchiveMember`
- `RosterImportSource`
- `RosterCost`
- `RosterSelection`
- `CanonicalArmy`
- `RosterImportPayload`

Keep records short and source/provenance-focused.

- [ ] **Step 2: Add archive inspection**

Create `src/warhammer_companion/ingestion/roster_archives.py` with:

- Safe extension allowlist for Phase 4A: `.ros` XML inside `.rosz`.
- `RosterArchiveLimits`.
- `inspect_roster_archive(...)` returning selected XML bytes plus member metadata or block reasons.
- Rejection of traversal, absolute paths, nested archives, encrypted members, unexpected
  extensions, too many members, oversized compressed/uncompressed bytes, and high ratio.

- [ ] **Step 3: Add XML pre-screen and shallow parser**

Create `src/warhammer_companion/ingestion/roster_xml.py` with:

- `RosterXmlLimits`.
- `parse_roster_xml(...)`.
- Pre-screen rejection for disallowed XML tokens and URLs.
- Shallow extraction of roster attributes, first force catalogue name, nested selections, and costs.

- [ ] **Step 4: Add application builder**

Create `src/warhammer_companion/application/roster_import.py` with:

- `build_roster_import_result_from_bytes(...)`
- Stable canonical JSON input hashing.
- `blocked` result on unsafe input.
- `estimated` result on safe shallow import.

- [ ] **Step 5: Verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_import_safety.py -q
```

Expected: PASS.

### Task 3: Review, QA, And Commit

- [ ] **Step 1: Run focused regression**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_import_safety.py tests\test_toolkit_contracts.py tests\test_rules_sources.py tests\test_base_sizes.py tests\test_terrain_semantics.py -q
```

Expected: PASS.

- [ ] **Step 2: Run static checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
```

Expected: all pass.

- [ ] **Step 3: Run adversarial review**

Reviewer must inspect:

- Archive validation is fail-closed.
- XML pre-screen blocks hostile constructs before parsing.
- Results cannot imply roster legality, profile resolution, official points, recommendations, or
  tactical safety.
- No real roster/community/official data or protected text is committed.

- [ ] **Step 4: Run full validation and Browser QA**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Then run the established Browser route sweep against the local web app.

- [ ] **Step 5: Commit Phase 4A**

Stage only Phase 4A files and not user-owned `AGENTS.md`.

Commit message:

```text
Add roster import safety records
```
