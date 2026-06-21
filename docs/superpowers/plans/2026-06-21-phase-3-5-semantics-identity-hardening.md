# Phase 3.5 Semantics Identity Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden Phase 3 semantics identity and manual footprint edge cases before hostile roster/profile inputs are introduced.

**Architecture:** Keep changes inside the existing Phase 3 domain/application modules. Tests prove stricter identity, blocking, and unsupported-shape behavior without changing LOS geometry, rendering, web, or desktop adapters.

**Tech Stack:** Python 3.12, dataclasses, pytest, Ruff, mypy, built-in Browser for final smoke QA.

---

## File Structure

- Modify: `tests/test_base_sizes.py`
  - Add failing tests for structured manual-model-frame hashes, non-finite blocked hashing,
    empty footprint blocking, footprint source refs, and unsupported hull/custom base shapes.
- Modify: `tests/test_terrain_semantics.py`
  - Add failing tests for terrain source-ref/source-freshness hash identity and stale freshness
    blocking.
- Modify: `src/warhammer_companion/application/base_sizes.py`
  - Replace partial delimited hashing with a canonical structured input hash that includes all
    durable manual model-frame inputs.
- Modify: `src/warhammer_companion/application/terrain_semantics.py`
  - Add `source_freshness` to the builder, readiness report, and hash input.
  - Include canonical source refs in the terrain semantics input hash.
- Modify: `src/warhammer_companion/domain/base_sizes.py`
  - Block empty manual footprints.
  - Preserve footprint-level source refs.
  - Reject unsupported hull/custom base geometry explicitly.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Record Phase 3.5 decisions, review triage, and verification.
- Create: `docs/superpowers/qa/2026-06-21-phase-3-5-semantics-identity-hardening-qa.md`
  - Autonomous QA pathway for automated and Browser checks.
- Modify:
  `docs/superpowers/reviews/2026-06-21-phase-3-5-consultant-semantics-hardening.md`
  - Record consultant sequencing findings and triage.
- Modify:
  `docs/superpowers/reviews/2026-06-21-phase-3-5-adversarial-semantics-hardening.md`
  - Record adversarial findings, fixes, and final approval.

### Task 1: Write Failing Tests

- [ ] **Step 1: Add base-size hardening tests**

Add tests proving:

- `build_manual_model_frame_result(...)` hash changes when `model_label`, `base_label`, `reason`,
  or `source_ref_ids` changes.
- Non-finite manual dimensions still return blocked toolkit results.
- `ManualUnitFootprint(..., models=())` blocks with `missing-unit-models`.
- Non-empty manual footprints preserve footprint-level `source_ref_ids`.
- `BaseGeometry(shape="hull")` and `BaseGeometry(shape="custom")` raise an explicit unsupported
  shape error.

- [ ] **Step 2: Add terrain semantics hardening tests**

Add tests proving:

- `build_terrain_semantics_result(...)` hash changes when `source_ref_ids` changes.
- `build_terrain_semantics_result(...)` hash changes when source freshness changes.
- Stale source freshness blocks terrain semantics results and produces no overlays.

- [ ] **Step 3: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q
```

Expected: FAIL because the existing implementation omits these Phase 3.5 hardening behaviors.

### Task 2: Implement Identity And Footprint Hardening

- [ ] **Step 1: Implement canonical manual model-frame hashing**

In `src/warhammer_companion/application/base_sizes.py`, replace the delimited payload string with
a canonical JSON payload that includes:

- schema version
- tool id
- model id and label
- base record id and label
- diameter value encoded as a stable string, including non-finite values
- operator id
- entered-at ISO timestamp
- reason
- sorted unique source refs

- [ ] **Step 2: Implement terrain provenance hashing**

In `src/warhammer_companion/application/terrain_semantics.py`:

- Add a `source_freshness` keyword with default `"unknown"`.
- Pass `source_freshness` into `index.readiness_report(...)`.
- Include sorted unique `source_ref_ids` and `source_freshness` in `_terrain_semantics_hash(...)`.

- [ ] **Step 3: Implement empty footprint and unsupported shape blocking**

In `src/warhammer_companion/domain/base_sizes.py`:

- Reject `shape in {"hull", "custom"}` in `BaseGeometry.__post_init__` with an unsupported-shape
  `ValueError`.
- Make empty `ManualUnitFootprint` reports blocked with a `missing-unit-models` block reason and
  warning.
- Add footprint-level `source_ref_ids` to non-empty readiness reports.

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_base_sizes.py tests\test_terrain_semantics.py -q
```

Expected: PASS.

### Task 3: Review, QA, And Commit

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

- [ ] **Step 3: Run adversarial review**

Reviewer must inspect:

- Whether provenance-affecting fields still collide in toolkit hashes.
- Whether empty footprint or unsupported shape records can look usable.
- Whether stale or incompatible source state still blocks.
- Whether any UI, rendering, LOS, packet, protected-data, or raw-artifact behavior changed.

- [ ] **Step 4: Run full validation and Browser QA**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Then launch the local web app and use built-in Browser to verify:

- `/viewer`
- `/heatmap`
- `/los-checker`
- `/hidden-coverage`
- `/settings`
- `/map-data`

Expected: automated checks pass, Browser pages render without console errors, and map/LOS/heatmap
pages still contain SVG and raster outputs where applicable.

- [ ] **Step 5: Commit Phase 3.5**

Stage only Phase 3.5 files and not user-owned `AGENTS.md`.

Commit message:

```text
Harden phase 3 semantics identity
```
