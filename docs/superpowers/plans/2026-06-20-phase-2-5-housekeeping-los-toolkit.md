# Phase 2.5 LOS Toolkit Housekeeping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract LOS toolkit-result construction from the broad service module into a focused application module without changing behavior.

**Architecture:** `WarhammerCompanionService` keeps packet selection, input clamping, and view-model projection. `warhammer_companion.application.los_toolkit` owns LOS toolkit payload construction, hashing, assumptions, warnings, and overlay metadata.

**Tech Stack:** Python 3.12, dataclasses, Shapely, pytest, Ruff, mypy.

---

## File Structure

- Create: `src/warhammer_companion/application/los_toolkit.py`
  - Owns `LosCheckerToolkitPayload` and `build_los_checker_toolkit_result()`.
- Modify: `src/warhammer_companion/application/services.py`
  - Imports the LOS builder and removes local LOS toolkit construction details.
- Create: `tests/test_los_toolkit.py`
  - Tests the extracted builder directly.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Records Phase 2.5 decisions and verification.

### Task 1: Add Failing Extracted-Builder Test

**Files:**
- Create: `tests/test_los_toolkit.py`

- [ ] **Step 1: Add test**

```python
from __future__ import annotations

from warhammer_companion.application.los_toolkit import build_los_checker_toolkit_result
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_build_los_checker_toolkit_result_preserves_phase_2_contract() -> None:
    packet = SAMPLE_PACKETS[0]
    before = packet.model_dump()

    result = build_los_checker_toolkit_result(
        packet,
        center=(22.0, 10.0),
        base_diameter=1.57,
    )

    suffix = result.input_hash.removeprefix("sha256:")[:12]
    assert result.tool_id == "los_checker"
    assert result.readiness == "estimated"
    assert result.payload.packet is packet
    assert result.payload.center == (22.0, 10.0)
    assert result.payload.base_diameter == 1.57
    assert result.payload.rays
    assert result.payload.board_state.packet_digest.startswith("sha256:")
    assert result.result_id.endswith(suffix)
    assert result.overlays[0].layer_kind == "line_of_sight_coverage"
    assert result.overlays[0].layer_id.endswith(suffix)
    assert not result.allows_recommendation_language()
    assert packet.model_dump() == before
```

- [ ] **Step 2: Verify red**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_los_toolkit.py -q
```

Expected: import failure because `warhammer_companion.application.los_toolkit` does not exist.

### Task 2: Extract LOS Toolkit Builder

**Files:**
- Create: `src/warhammer_companion/application/los_toolkit.py`
- Modify: `src/warhammer_companion/application/services.py`
- Test: `tests/test_los_toolkit.py`
- Test: `tests/test_application_service.py`

- [ ] **Step 1: Move LOS payload and builder**

Move `LosCheckerToolkitPayload`, `LOS_CHECKER_TOOLKIT_SCHEMA_VERSION`, and the LOS input-hash
helper into `application/los_toolkit.py`. Add:

```python
def build_los_checker_toolkit_result(
    packet: MapPacket,
    *,
    center: tuple[float, float],
    base_diameter: float,
) -> ToolkitResult[LosCheckerToolkitPayload]:
    ...
```

The implementation must be behavior-equivalent to Phase 2.

- [ ] **Step 2: Thin the service**

`WarhammerCompanionService.los_checker_toolkit_result()` should select the packet, clamp the input,
and call `build_los_checker_toolkit_result(packet, center=center, base_diameter=base)`.

- [ ] **Step 3: Verify target tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_los_toolkit.py tests\test_application_service.py tests\test_toolkit_contracts.py tests\test_board_state.py -q
```

Expected: all selected tests pass.

### Task 3: QA And Commit

**Files:**
- Modify: `docs/work-log/player-toolkit-implementation.md`

- [ ] **Step 1: Run QA**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_los_toolkit.py tests\test_application_service.py tests\test_toolkit_contracts.py tests\test_board_state.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_los_toolkit.py tests\test_application_service.py tests\test_los_geometry.py tests\test_rendering_svg.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
git diff --check
```

Expected: every command exits 0.

- [ ] **Step 2: Commit**

Run:

```powershell
git add docs/superpowers/specs/2026-06-20-phase-2-5-housekeeping-los-toolkit.md docs/superpowers/plans/2026-06-20-phase-2-5-housekeeping-los-toolkit.md docs/superpowers/qa/2026-06-20-phase-2-5-housekeeping-los-toolkit-qa.md docs/superpowers/reviews/2026-06-20-phase-2-5-consultant-los-toolkit.md docs/superpowers/reviews/2026-06-20-phase-2-5-adversarial-los-toolkit.md docs/work-log/player-toolkit-implementation.md src/warhammer_companion/application/los_toolkit.py src/warhammer_companion/application/services.py tests/test_los_toolkit.py
git commit -m "Housekeep phase 2.5 LOS toolkit extraction"
```

Expected: a single behavior-preserving housekeeping commit. Do not stage `AGENTS.md`.
