# Phase 5.5 Movement Housekeeping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce small duplication introduced or exposed by Phase 5 while preserving movement reach, LOS, web, desktop, and rendering behavior.

**Architecture:** Keep the cleanup inside existing adapter/rendering boundaries. Add one shared PySide numeric-control helper and reuse the existing generic raster plumbing for binary coverage output without unifying overlay semantics.

**Tech Stack:** Python 3.12, PySide6, Shapely, Pillow, NumPy, FastAPI/Jinja, pytest, Ruff, mypy.

---

## File Map

- `src/warhammer_companion/desktop/screens/common.py`: add shared `double_spin_box(...)`.
- `src/warhammer_companion/desktop/screens/los_checker.py`: replace private `_spin_box(...)`.
- `src/warhammer_companion/desktop/screens/movement_reach.py`: replace private `_spin_box(...)`.
- `src/warhammer_companion/rendering/svg.py`: make `_render_coverage_raster(...)` delegate to `_render_geometry_raster(...)`.
- `tests/test_desktop_screen_helpers.py`: add TDD coverage for the shared spin-box helper.
- `tests/test_rendering_svg.py`: add decoded PNG pixel tests for representative raster semantics.
- `docs/work-log/player-toolkit-implementation.md`: record Phase 5.5 decisions, review, and validation.

## Task 1: Shared Desktop Spin-Box Helper

**Files:**

- Modify: `src/warhammer_companion/desktop/screens/common.py`
- Modify: `src/warhammer_companion/desktop/screens/los_checker.py`
- Modify: `src/warhammer_companion/desktop/screens/movement_reach.py`
- Create: `tests/test_desktop_screen_helpers.py`

- [ ] **Step 1: Write the failing helper test**

Add:

```python
from __future__ import annotations

import os


def test_double_spin_box_uses_tool_screen_defaults() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.screens.common import double_spin_box

    app = QApplication.instance() or QApplication([])
    spin_box = double_spin_box(0.1, 8.0, 1.57)

    assert spin_box.minimum() == 0.1
    assert spin_box.maximum() == 8.0
    assert spin_box.decimals() == 2
    assert spin_box.singleStep() == 0.25
    assert spin_box.value() == 1.57
    spin_box.deleteLater()
    app.processEvents()
```

- [ ] **Step 2: Run the failing helper test**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_desktop_screen_helpers.py -q
```

Expected: import failure because `double_spin_box` does not exist.

- [ ] **Step 3: Add the shared helper**

Add `QDoubleSpinBox` import and:

```python
def double_spin_box(minimum: float, maximum: float, value: float) -> QDoubleSpinBox:
    spin_box = QDoubleSpinBox()
    spin_box.setRange(minimum, maximum)
    spin_box.setDecimals(2)
    spin_box.setSingleStep(0.25)
    spin_box.setValue(value)
    return spin_box
```

- [ ] **Step 4: Replace private helpers**

In both desktop screens, import `double_spin_box` from `common.py`, replace `_spin_box(...)` calls
with `double_spin_box(...)`, remove the private helper, and remove unused `QDoubleSpinBox` imports.

- [ ] **Step 5: Verify desktop helper and screens**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_desktop_screen_helpers.py tests\test_desktop_app.py -q
```

Expected: helper test and desktop smoke tests pass.

## Task 2: Shared Geometry Raster Helper

**Files:**

- Modify: `src/warhammer_companion/rendering/svg.py`
- Test: `tests/test_rendering_svg.py`

- [ ] **Step 1: Write raster semantic lock tests**

Add helpers that extract the base64 PNG from a rendered `<image class="...">` and assert:

- `coverage-image` has a visible pixel with color `(42, 140, 158, 118)`.
- `movement-envelope-image` has a visible pixel with color `(75, 125, 178, 96)`.
- `hidden-coverage-image` has at least one alpha-positive pixel and at least one alpha-zero pixel.
- `heatmap-image` keeps exclusion pixels transparent when a heatmap exclusion region is provided.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rendering_svg.py -q
```

Expected: tests pass before refactor because they describe existing behavior.

- [ ] **Step 2: Confirm current rendering behavior**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rendering_svg.py::test_binary_coverage_polygon_renders_as_embedded_pixel_raster tests\test_rendering_svg.py::test_movement_envelope_renders_as_embedded_raster_with_endpoint_markers -q
```

Expected: both tests pass before refactor.

- [ ] **Step 3: Delegate coverage raster rendering**

Change `_render_coverage_raster(...)` to:

```python
def _render_coverage_raster(packet: MapPacket, polygon: BaseGeometry, scale: int) -> list[str]:
    return _render_geometry_raster(
        packet,
        polygon,
        scale,
        css_class="coverage-image",
        color=(42, 140, 158, 118),
    )
```

No SVG class, color, order, or public parameter changes.

- [ ] **Step 4: Verify renderer output remains stable**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rendering_svg.py -q
```

Expected: rendering tests pass, including decoded PNG semantic locks.

## Task 3: Documentation, Review, And Validation

**Files:**

- Modify: `docs/work-log/player-toolkit-implementation.md`
- Modify: `docs/superpowers/reviews/2026-06-21-phase-5-5-consultant-movement-housekeeping.md`
- Modify: `docs/superpowers/reviews/2026-06-21-phase-5-5-adversarial-movement-housekeeping.md`

- [ ] **Step 1: Record consultant/adversarial review outcomes**

Summarize scope approval, constraints, and any accepted fixes.

- [ ] **Step 2: Run final validation**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest tests\test_desktop_screen_helpers.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_los_geometry.py tests\test_movement_reach_geometry.py -q
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected: all checks pass; existing Starlette deprecation warning is acceptable.

- [ ] **Step 3: Manual Browser QA**

Launch the local app and verify `/heatmap`, `/los-checker`, `/hidden-coverage`, and
`/movement-reach` render one map SVG with no console warnings or errors. Smoke both the default
official packet path and `layout_variant=B` / page-52-style route selection where practical. Confirm
`heatmap-image`, `coverage-image`, `hidden-coverage-image`, and `movement-envelope-image` remain
present on the relevant pages.

- [ ] **Step 4: Protected-path scan and commit**

Do not stage `AGENTS.md`. Stage only Phase 5.5 docs/source/tests and commit:

```powershell
git commit -m "Housekeep movement reach adapters"
```
