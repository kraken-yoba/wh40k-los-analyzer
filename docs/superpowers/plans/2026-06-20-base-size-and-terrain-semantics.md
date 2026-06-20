# Base Size And Terrain Semantics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build source-aware manual base-size/model-frame and terrain semantics contracts that
later movement, threat, and exposure tools can consume without roster import.

**Architecture:** Keep durable records in domain modules and expose thin application builders that
return `ToolkitResult`. `MapPacket` remains layout geometry only; terrain semantics are keyed over
packet ID, packet digest, element kind, and element ID.

**Tech Stack:** Python 3.12, dataclasses, Shapely geometry, pytest, Ruff, mypy.

---

## File Structure

- Create: `src/warhammer_companion/domain/semantics.py`
  - Shared field-source refs, semantic validation records, semantic block reasons, and readiness
    reducer.
- Create: `src/warhammer_companion/domain/base_sizes.py`
  - Base geometry, base-size records, manual provenance, model-frame records, and manual unit
    footprints.
- Create: `src/warhammer_companion/domain/terrain_semantics.py`
  - `MapPacket` terrain adapter records and packet-level terrain semantics index.
- Create: `src/warhammer_companion/application/base_sizes.py`
  - Builds manual model-frame `ToolkitResult` payloads.
- Create: `src/warhammer_companion/application/terrain_semantics.py`
  - Builds terrain semantics `ToolkitResult` payloads.
- Create: `tests/test_base_sizes.py`
  - Manual base/frame provenance, readiness, blocking, non-round representation, and hash tests.
- Create: `tests/test_terrain_semantics.py`
  - Packet adapter, packet digest, blocker preservation, source-compatibility, and hash tests.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Records decisions, review triage, red-green evidence, and verification.
- Modify: `docs/superpowers/reviews/2026-06-20-phase-3-consultant-base-terrain.md`
  - Records consultant findings and triage.
- Modify: `docs/superpowers/reviews/2026-06-20-phase-3-adversarial-base-terrain.md`
  - Records adversarial findings and final approval.

### Task 1: Write Failing Contract Tests

- [ ] **Step 1: Add base-size tests**

Create `tests/test_base_sizes.py` with tests that prove:

- Manual round bases normalize millimeters to inches and remain `estimated`.
- Manual provenance includes local operator marker, timestamp, reason, reviewed fields, units,
  source refs, field-level source refs, freshness, compatibility, warnings, and assumptions.
- Unknown bases are `blocked` and cannot allow trusted claims.
- Invalid dimensions produce a blocked `ToolkitResult` without overlays.
- Manual source refs do not allow trusted recommendation language.
- Input hashes change when manual base size changes.
- Non-round frame records can be represented without touching LOS behavior.
- Manual unit footprints block when a model base is missing.

- [ ] **Step 2: Add terrain-semantics tests**

Create `tests/test_terrain_semantics.py` with tests that prove:

- The adapter creates records for terrain areas, dense features, and light features.
- The index includes `packet_digest`.
- The adapter does not mutate `MapPacket`.
- `packet.blockers()` geometry is unchanged before and after adaptation.
- Dense-feature `blocks_los_2d` mirrors the existing packet flag.
- Unknown terrain traits and vertical assumptions prevent trusted claims.
- Incompatible source packs return a blocked `ToolkitResult` without overlays.
- Input hashes change when packet digest or source-pack version changes.

- [ ] **Step 3: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q
```

Expected: FAIL because `warhammer_companion.domain.base_sizes`,
`warhammer_companion.domain.terrain_semantics`, `warhammer_companion.application.base_sizes`, and
`warhammer_companion.application.terrain_semantics` do not exist.

### Task 2: Implement Domain And Application Contracts

- [ ] **Step 1: Add shared semantic readiness primitives**

Create `src/warhammer_companion/domain/semantics.py` with:

- `FieldSourceRef`
- `SemanticsValidationRecord`
- `SemanticsBlockReason`
- `SemanticsReadinessReport`
- `report_semantics_readiness(...)`

The reducer must return the minimum readiness across records, block incompatible or stale source
packs, add terrain and vertical source-pending warnings, and permit trusted claims only when the
aggregate readiness is `trusted` and no block reasons exist.

- [ ] **Step 2: Add base-size records**

Create `src/warhammer_companion/domain/base_sizes.py` with:

- `BaseGeometry.round()` and `BaseGeometry.oval()`, with positive-dimension validation.
- `BaseSizeRecord.manual_round_mm()` and `BaseSizeRecord.manual_oval_mm()`.
- `BaseSizeRecord.unknown()`.
- `ModelFrameRecord.readiness_report()`.
- `ManualUnitFootprint.readiness_report()`.

Manual records must be `estimated`, not trusted, even with source refs.

- [ ] **Step 3: Add terrain semantics records**

Create `src/warhammer_companion/domain/terrain_semantics.py` with:

- `TerrainSemanticsRecord`
- `TerrainSemanticsIndex.from_packet(...)`
- `TerrainSemanticsIndex.records()`
- `TerrainSemanticsIndex.readiness_report(...)`

The adapter must preserve existing Shapely geometry and LOS blocker flags without mutating the
packet.

- [ ] **Step 4: Add thin application builders**

Create:

- `src/warhammer_companion/application/base_sizes.py`
- `src/warhammer_companion/application/terrain_semantics.py`

Builders must return `ToolkitResult` payloads, include deterministic input hashes, convert semantic
block reasons into application `BlockReason`s, and produce no tactical overlays for blocked
results.

- [ ] **Step 5: Verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q
```

Expected: PASS.

### Task 3: Regression, Review, And Commit

- [ ] **Step 1: Run focused regression**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py tests\test_board_state.py tests\test_toolkit_contracts.py tests\test_los_toolkit.py tests\test_los_geometry.py tests\test_rendering_svg.py -q
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

- [ ] **Step 3: Request adversarial review**

Reviewer must inspect the diff for:

- Manual fallback accidentally becoming trusted.
- Terrain labels or LOS flags being treated as official mechanics.
- Non-trusted user-facing claim wording.
- `MapPacket` mutation or LOS/rendering changes.
- Protected source data or raw imports added to the repo.
- Missing hash/source-compatibility tests.

- [ ] **Step 4: Run full validation**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected: all pass. Browser and Computer Use checks are not required unless the diff changes web,
desktop, renderer, package, or runtime UI behavior.

- [ ] **Step 5: Commit Phase 3**

Stage only Phase 3 files and not user-owned `AGENTS.md`.

Commit message:

```text
Add phase 3 base and terrain semantics
```
