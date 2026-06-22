# Phase 7.5 Exposure Mode Housekeeping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize Deployment Exposure mode predicate semantics without changing behavior.

**Architecture:** Keep exposure mode definitions and semantics in `domain/exposure.py`, then import
those helpers from the application builder and service adapter. This keeps domain vocabulary as the
single owner of mode meaning while web and desktop behavior remain unchanged.

**Tech Stack:** Python 3.12, pytest, Ruff, mypy, FastAPI/Jinja, PySide6.

---

## File Map

- Modify: `src/warhammer_companion/domain/exposure.py`
- Modify: `src/warhammer_companion/application/deployment_exposure.py`
- Modify: `src/warhammer_companion/application/services.py`
- Modify: `tests/test_deployment_exposure_toolkit.py`
- Modify: `tests/test_application_service.py`
- Modify: `docs/work-log/player-toolkit-implementation.md`
- Create/modify review docs under `docs/superpowers/reviews/`.

## Task 1: Add Shared Exposure Mode Helpers

- [ ] Add failing tests to `tests/test_deployment_exposure_toolkit.py`:

```python
from warhammer_companion.domain.exposure import (
    exposure_mode_includes_los,
    exposure_mode_includes_threat,
)


def test_exposure_mode_helpers_cover_all_supported_modes() -> None:
    assert exposure_mode_includes_los("threat-only") is False
    assert exposure_mode_includes_threat("threat-only") is True
    assert exposure_mode_includes_los("los-only") is True
    assert exposure_mode_includes_threat("los-only") is False
    assert exposure_mode_includes_los("threat-or-los") is True
    assert exposure_mode_includes_threat("threat-or-los") is True
    assert exposure_mode_includes_los("threat-and-los") is True
    assert exposure_mode_includes_threat("threat-and-los") is True
```

- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py::test_exposure_mode_helpers_cover_all_supported_modes -q
```

Expected: import failure because the helpers do not exist yet.

- [ ] Add the helpers to `src/warhammer_companion/domain/exposure.py`:

```python
def exposure_mode_includes_los(exposure_mode: ExposureMode) -> bool:
    """Return whether an exposure mode should render/use the LOS component."""
    return exposure_mode in {"los-only", "threat-or-los", "threat-and-los"}


def exposure_mode_includes_threat(exposure_mode: ExposureMode) -> bool:
    """Return whether an exposure mode should render/use the threat component."""
    return exposure_mode in {"threat-only", "threat-or-los", "threat-and-los"}
```

- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py::test_exposure_mode_helpers_cover_all_supported_modes -q
```

Expected: 1 passed.

## Task 2: Add Behavior-Preservation Regressions

- [ ] Add a direct invalid-mode regression to `tests/test_deployment_exposure_toolkit.py`:

```python
def test_deployment_exposure_blocks_unsupported_raw_exposure_mode() -> None:
    result = build_deployment_exposure_toolkit_result(
        SAMPLE_PACKETS[0],
        deployment_zone_id="attacker",
        friendly_center=(10.0, 5.0),
        friendly_base_diameter=1.57,
        enemy_source_center=(38.0, 52.0),
        enemy_base_diameter=1.57,
        enemy_move_distance=0.0,
        enemy_threat_range=1.0,
        enemy_threat_mode="raw-range",
        exposure_mode="unsupported",
    )

    assert result.readiness == "blocked"
    assert not result.overlays
    assert [reason.reason_id for reason in result.block_reasons] == ["invalid-exposure-mode"]
```

- [ ] Add a parameterized service/rendering regression to `tests/test_application_service.py`:

```python
@pytest.mark.parametrize(
    ("mode", "expected_los", "expected_threat"),
    [
        ("threat-only", False, True),
        ("los-only", True, False),
        ("threat-or-los", True, True),
        ("threat-and-los", True, True),
    ],
)
def test_deployment_exposure_state_renders_component_overlays_by_mode(
    mode: str,
    expected_los: bool,
    expected_threat: bool,
) -> None:
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )

    state = service.deployment_exposure_state(
        packet_id=SAMPLE_PACKETS[0].id,
        exposure_mode=mode,
        enemy_move=6.0,
        enemy_threat=2.0,
        enemy_mode="fixed-move-plus-range",
    )

    assert ("coverage-image" in state.map_svg) is expected_los
    assert ("threat-projection-image" in state.map_svg) is expected_threat
```

- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py::test_deployment_exposure_blocks_unsupported_raw_exposure_mode tests\test_application_service.py::test_deployment_exposure_state_renders_component_overlays_by_mode -q
```

Expected: tests pass before implementation because they document existing behavior; keep them as
guardrails before refactoring.

## Task 3: Replace Duplicated Callers

- [ ] Update `src/warhammer_companion/application/deployment_exposure.py` imports to include:

```python
from warhammer_companion.domain.exposure import (
    EXPOSURE_MODES,
    DeploymentExposurePayload,
    ExposureDiagnosticReason,
    ExposurePlacementDiagnostic,
    coerce_exposure_mode,
    exposure_mode_includes_los,
    exposure_mode_includes_threat,
)
```

- [ ] Include `ExposureMode` in that import and change `_placement_diagnostic(...)` so its
  `exposure_mode` parameter is typed as `ExposureMode`.
- [ ] Replace `_mode_includes_los(...)` calls with `exposure_mode_includes_los(...)`.
- [ ] Replace `_mode_includes_threat(...)` calls with `exposure_mode_includes_threat(...)`.
- [ ] Delete the private `_mode_includes_los(...)` and `_mode_includes_threat(...)` functions.
- [ ] Update `src/warhammer_companion/application/services.py` imports to include
  `exposure_mode_includes_los` and `exposure_mode_includes_threat`.
- [ ] Replace `_exposure_mode_includes_los(...)` calls with `exposure_mode_includes_los(...)`.
- [ ] Replace `_exposure_mode_includes_threat(...)` calls with
  `exposure_mode_includes_threat(...)`.
- [ ] Delete private service helper duplicates.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_deployment_exposure_toolkit.py tests\test_application_service.py tests\test_rendering_svg.py tests\test_web_server.py tests\test_desktop_app.py -q
```

Expected: all pass with only the existing Starlette `TestClient` deprecation warning if the web
suite emits it.

## Task 4: Documentation, QA, And Commit

- [ ] Update `docs/work-log/player-toolkit-implementation.md` with Phase 7.5 scope, red/green
  evidence, reviewer outcomes, Browser QA, and blockers.
- [ ] Run final validation:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

- [ ] Run Browser QA:
  - `/deployment-exposure`;
  - page 9 regression route from the Phase 7 QA doc;
  - page 52 regression route from the Phase 7 QA doc.
- [ ] Protected-path scan excludes generated/raw/PDF/credential artifacts and keeps `AGENTS.md`
  unstaged.
- [ ] Commit:

```powershell
git commit -m "Centralize exposure mode predicates"
```
