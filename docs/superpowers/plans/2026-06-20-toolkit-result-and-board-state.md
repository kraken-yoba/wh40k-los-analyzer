# Toolkit Result And Board State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Phase 2 shared toolkit result and minimal board-state primitives without changing existing LOS behavior.

**Architecture:** Create frozen board-state and overlay dataclasses in `src/warhammer_companion/domain/`, plus the service result envelope in `src/warhammer_companion/application/toolkit.py`. Keep `MapPacket` unchanged and let `BoardState` wrap it as selected layout geometry. Tests drive readiness semantics, overlay neutrality, and LOS regression safety before implementation.

**Tech Stack:** Python 3.12, dataclasses, typing generics, Shapely geometry, pytest, Ruff, mypy.

---

## File Structure

- Create: `src/warhammer_companion/domain/board_state.py`
  - Owns minimal board-state primitives that wrap `MapPacket`.
- Create: `src/warhammer_companion/domain/overlays.py`
  - Owns rendering-neutral map overlay primitives.
- Create: `src/warhammer_companion/application/toolkit.py`
  - Owns `ToolkitResult` and readiness metadata returned by services before rendering.
- Modify: `src/warhammer_companion/application/services.py`
  - Adds a narrow LOS toolkit-result method and keeps existing SVG state behavior.
- Modify: `src/warhammer_companion/domain/__init__.py`
  - Re-export nothing unless needed by existing imports; keep this file minimal.
- Create: `tests/test_toolkit_contracts.py`
  - Unit tests for `ToolkitResult` and `MapOverlayLayer`.
- Create: `tests/test_board_state.py`
  - Unit tests for minimal `BoardState`.
- Modify: `tests/test_application_service.py`
  - Verifies LOS service can produce `ToolkitResult` before SVG projection.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Add Phase 2 decisions, review outcomes, and verification evidence.
- Create: `docs/superpowers/reviews/2026-06-20-phase-2-consultant-toolkit-foundation.md`
  - Consultant findings and triage.
- Create: `docs/superpowers/reviews/2026-06-20-phase-2-adversarial-toolkit-foundation.md`
  - Adversarial findings and triage.

### Task 1: Write Failing Contract And Board-State Tests

**Files:**
- Create: `tests/test_toolkit_contracts.py`
- Create: `tests/test_board_state.py`
- Modify: `tests/test_application_service.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_toolkit_contracts.py`:

```python
from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from warhammer_companion.application.toolkit import (
    BlockReason,
    ExportMetadata,
    ToolkitResult,
    ValidationRecord,
)
from warhammer_companion.domain.overlays import MapOverlayLayer, ToolkitAssumption


def test_toolkit_result_readiness_controls_recommendation_language() -> None:
    blocked = ToolkitResult[None](
        result_id="blocked-los",
        tool_id="los",
        input_hash="sha256:blocked",
        readiness="blocked",
        payload=None,
        block_reasons=(BlockReason(reason_id="missing-base", detail="Base size is missing."),),
    )
    estimated = ToolkitResult[str](
        result_id="estimated-los",
        tool_id="los",
        input_hash="sha256:estimated",
        readiness="estimated",
        payload="diagnostic",
        assumptions=(ToolkitAssumption(assumption_id="2d", detail="2D geometry only."),),
    )
    trusted = ToolkitResult[str](
        result_id="trusted-los",
        tool_id="los",
        input_hash="sha256:trusted",
        readiness="trusted",
        payload="diagnostic",
        validation_records=(
            ValidationRecord(
                validator_id="fixture",
                status="passed",
                detail="Fixture validation passed.",
            ),
        ),
        export_metadata=ExportMetadata(schema_version="toolkit-result/v0"),
    )

    assert blocked.is_blocked
    assert not blocked.is_usable
    assert not blocked.allows_recommendation_language()
    assert estimated.is_usable
    assert not estimated.allows_recommendation_language()
    assert trusted.is_usable
    assert trusted.allows_recommendation_language()


def test_blocked_result_requires_block_reason_and_no_overlays() -> None:
    overlay = MapOverlayLayer(
        layer_id="reach",
        layer_kind="movement_reach",
        geometry=Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]),
        units="battlefield_inches",
        style_token="estimated-threat",
        label="Estimated reach",
        readiness="estimated",
        source_ref_ids=("manual-measurement",),
    )

    with pytest.raises(ValueError, match="block reason"):
        ToolkitResult[None](
            result_id="blocked-without-reason",
            tool_id="movement",
            input_hash="sha256:blocked",
            readiness="blocked",
            payload=None,
        )
    with pytest.raises(ValueError, match="overlays"):
        ToolkitResult[None](
            result_id="blocked-with-overlay",
            tool_id="movement",
            input_hash="sha256:blocked",
            readiness="blocked",
            payload=None,
            overlays=(overlay,),
            block_reasons=(BlockReason(reason_id="missing-base", detail="Base size is missing."),),
        )


def test_overlay_readiness_cannot_exceed_result_readiness() -> None:
    overlay = MapOverlayLayer(
        layer_id="trusted-overlay",
        layer_kind="movement_reach",
        geometry=Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]),
        units="battlefield_inches",
        style_token="trusted-threat",
        label="Trusted reach",
        readiness="trusted",
    )

    with pytest.raises(ValueError, match="exceeds result readiness"):
        ToolkitResult[str](
            result_id="estimated-result",
            tool_id="movement",
            input_hash="sha256:estimated",
            readiness="estimated",
            payload="diagnostic",
            overlays=(overlay,),
        )


def test_map_overlay_layer_is_rendering_neutral_geometry() -> None:
    geometry = Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)])

    layer = MapOverlayLayer(
        layer_id="reach",
        layer_kind="movement_reach",
        geometry=geometry,
        units="battlefield_inches",
        style_token="estimated-threat",
        label="Estimated reach",
        readiness="estimated",
        source_ref_ids=("manual-measurement",),
    )

    assert layer.geometry.area == 4.0
    assert not layer.is_empty
    assert layer.source_ref_ids == ("manual-measurement",)
```

`tests/test_board_state.py`:

```python
from __future__ import annotations

from warhammer_companion.domain.board_state import BoardModel, BoardState, BoardUnit
from warhammer_companion.los.geometry import visibility_polygon_from_base
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_board_state_from_packet_keeps_map_packet_layout_only() -> None:
    packet = SAMPLE_PACKETS[0]
    before = packet.model_dump()

    state = BoardState.from_packet(packet, state_id="state-page-9")

    assert state.packet is packet
    assert state.state_id == "state-page-9"
    assert state.readiness == "estimated"
    assert state.units == ()
    assert state.warnings
    assert packet.model_dump() == before
    assert not hasattr(packet, "rules_pack")
    assert not hasattr(packet, "units")


def test_board_state_reports_missing_model_positions_and_base_sizes() -> None:
    packet = SAMPLE_PACKETS[0]
    unit = BoardUnit(
        unit_id="unit-1",
        label="Unit 1",
        controller="friendly",
        models=(
            BoardModel(model_id="m1", base_diameter=1.57, position=None),
            BoardModel(model_id="m2", base_diameter=None, position=(10.0, 10.0)),
        ),
    )

    state = BoardState.from_packet(packet, state_id="state-with-gaps", units=(unit,))

    assert state.readiness == "estimated"
    warning_text = " ".join(warning.detail for warning in state.warnings)
    assert "position" in warning_text
    assert "base size" in warning_text


def test_board_state_with_model_data_remains_estimated_until_rules_are_source_backed() -> None:
    packet = SAMPLE_PACKETS[0]
    unit = BoardUnit(
        unit_id="unit-1",
        label="Unit 1",
        controller="friendly",
        models=(BoardModel(model_id="m1", base_diameter=1.57, position=(22.0, 10.0)),),
    )

    state = BoardState.from_packet(packet, state_id="state-with-models", units=(unit,))

    assert state.readiness == "estimated"
    assert any("source-backed mechanics" in warning.detail for warning in state.warnings)


def test_phase_2_contracts_do_not_change_existing_los_geometry() -> None:
    packet = SAMPLE_PACKETS[0]

    before = visibility_polygon_from_base(packet, center=(22.0, 10.0), base_diameter=1.57)
    state = BoardState.from_packet(packet, state_id="state-los-regression")
    after = visibility_polygon_from_base(state.packet, center=(22.0, 10.0), base_diameter=1.57)

    assert after.equals_exact(before, tolerance=1e-9)
```

Append to `tests/test_application_service.py`:

```python
def test_los_checker_toolkit_result_wraps_analysis_before_svg_projection() -> None:
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )

    result = service.los_checker_toolkit_result(
        packet_id=SAMPLE_PACKETS[0].id,
        x=22.0,
        y=10.0,
        base=1.57,
    )

    assert result.tool_id == "los_checker"
    assert result.readiness == "estimated"
    assert result.payload.packet is SAMPLE_PACKETS[0]
    assert result.overlays
    assert result.overlays[0].layer_kind == "line_of_sight_coverage"
    assert not result.allows_recommendation_language()
```

- [ ] **Step 2: Run tests to verify they fail for the missing module**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_toolkit_contracts.py tests\test_board_state.py tests\test_application_service.py -q
```

Expected: failure during import with missing `warhammer_companion.application.toolkit` or missing
`warhammer_companion.domain.board_state`.

### Task 2: Implement Minimal Domain Contracts

**Files:**
- Create: `src/warhammer_companion/domain/board_state.py`
- Create: `src/warhammer_companion/domain/overlays.py`
- Create: `src/warhammer_companion/application/toolkit.py`
- Modify: `src/warhammer_companion/application/services.py`
- Test: `tests/test_toolkit_contracts.py`
- Test: `tests/test_board_state.py`

- [ ] **Step 1: Add implementation**

`src/warhammer_companion/domain/overlays.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from shapely.geometry.base import BaseGeometry

ToolkitReadiness = Literal["trusted", "estimated", "degraded", "blocked"]


@dataclass(frozen=True, slots=True)
class ToolkitAssumption:
    assumption_id: str
    detail: str
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolkitWarning:
    warning_id: str
    detail: str
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MapOverlayLayer:
    layer_id: str
    layer_kind: str
    geometry: BaseGeometry
    units: str
    style_token: str
    label: str
    readiness: ToolkitReadiness
    source_ref_ids: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return self.geometry.is_empty
```

`src/warhammer_companion/application/toolkit.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Literal, TypeVar, get_args

from warhammer_companion.domain.overlays import (
    MapOverlayLayer,
    ToolkitAssumption,
    ToolkitReadiness,
    ToolkitWarning,
)

PayloadT = TypeVar("PayloadT")
READINESS_ORDER: dict[ToolkitReadiness, int] = {
    "blocked": 0,
    "degraded": 1,
    "estimated": 2,
    "trusted": 3,
}


@dataclass(frozen=True, slots=True)
class BlockReason:
    reason_id: str
    detail: str
    remediation: str | None = None
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationRecord:
    validator_id: str
    status: Literal["passed", "warning", "failed", "not_run"]
    detail: str
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExportMetadata:
    schema_version: str = "toolkit-result/v0"
    content_type: str = "application/json"
    generated_by: str = "warhammer-companion"


@dataclass(frozen=True, slots=True)
class ToolkitResult(Generic[PayloadT]):
    result_id: str
    tool_id: str
    input_hash: str
    readiness: ToolkitReadiness
    payload: PayloadT
    overlays: tuple[MapOverlayLayer, ...] = ()
    assumptions: tuple[ToolkitAssumption, ...] = ()
    warnings: tuple[ToolkitWarning, ...] = ()
    block_reasons: tuple[BlockReason, ...] = ()
    source_ref_ids: tuple[str, ...] = ()
    validation_records: tuple[ValidationRecord, ...] = ()
    export_metadata: ExportMetadata = field(default_factory=ExportMetadata)

    def __post_init__(self) -> None:
        if self.readiness not in get_args(ToolkitReadiness):
            raise ValueError(f"Unknown toolkit readiness: {self.readiness}")
        if self.readiness == "blocked" and not self.block_reasons:
            raise ValueError("blocked toolkit results require at least one block reason")
        if self.readiness == "blocked" and self.overlays:
            raise ValueError("blocked toolkit results cannot include tactical overlays")
        result_rank = READINESS_ORDER[self.readiness]
        for overlay in self.overlays:
            if READINESS_ORDER[overlay.readiness] > result_rank:
                raise ValueError("overlay readiness exceeds result readiness")

    @property
    def is_blocked(self) -> bool:
        return self.readiness == "blocked"

    @property
    def is_usable(self) -> bool:
        return self.readiness in {"trusted", "estimated", "degraded"} and not self.is_blocked

    def allows_recommendation_language(self) -> bool:
        return self.readiness == "trusted"
```

`src/warhammer_companion/domain/board_state.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from shapely.geometry.base import BaseGeometry

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.overlays import (
    ToolkitAssumption,
    ToolkitReadiness,
    ToolkitWarning,
)

PlayerRole = Literal["friendly", "enemy", "neutral", "unknown"]


@dataclass(frozen=True, slots=True)
class BoardStateContext:
    battle_round: int | None = None
    turn: int | None = None
    phase: str | None = None
    active_player: PlayerRole = "unknown"
    going_first: PlayerRole = "unknown"


@dataclass(frozen=True, slots=True)
class BoardModel:
    model_id: str
    base_diameter: float | None = None
    position: tuple[float, float] | None = None
    footprint: BaseGeometry | None = None
    source_ref_ids: tuple[str, ...] = ()
    readiness: ToolkitReadiness = "estimated"
    warnings: tuple[ToolkitWarning, ...] = ()


@dataclass(frozen=True, slots=True)
class BoardUnit:
    unit_id: str
    label: str
    controller: PlayerRole
    models: tuple[BoardModel, ...] = ()
    source_ref_ids: tuple[str, ...] = ()
    readiness: ToolkitReadiness = "estimated"
    warnings: tuple[ToolkitWarning, ...] = ()


@dataclass(frozen=True, slots=True)
class BoardState:
    state_id: str
    packet: MapPacket
    context: BoardStateContext = field(default_factory=BoardStateContext)
    units: tuple[BoardUnit, ...] = ()
    source_ref_ids: tuple[str, ...] = ()
    readiness: ToolkitReadiness = "estimated"
    assumptions: tuple[ToolkitAssumption, ...] = ()
    warnings: tuple[ToolkitWarning, ...] = ()

    @classmethod
    def from_packet(
        cls,
        packet: MapPacket,
        *,
        state_id: str,
        context: BoardStateContext | None = None,
        units: tuple[BoardUnit, ...] = (),
        source_ref_ids: tuple[str, ...] = (),
        assumptions: tuple[ToolkitAssumption, ...] = (),
    ) -> BoardState:
        warnings = _board_state_warnings(units)
        return cls(
            state_id=state_id,
            packet=packet,
            context=context or BoardStateContext(),
            units=units,
            source_ref_ids=source_ref_ids,
            readiness="estimated",
            assumptions=assumptions,
            warnings=warnings,
        )


def _board_state_warnings(units: tuple[BoardUnit, ...]) -> tuple[ToolkitWarning, ...]:
    warnings: list[ToolkitWarning] = []
    if not units:
        warnings.append(
            ToolkitWarning(
                warning_id="missing-units",
                detail="Model positions and base sizes are missing; board state is diagnostic only.",
            )
        )
        return tuple(warnings)
    missing_position = any(model.position is None for unit in units for model in unit.models)
    missing_base = any(model.base_diameter is None for unit in units for model in unit.models)
    if missing_position:
        warnings.append(
            ToolkitWarning(
                warning_id="missing-model-position",
                detail="At least one model position is missing.",
            )
        )
    if missing_base:
        warnings.append(
            ToolkitWarning(
                warning_id="missing-base-size",
                detail="At least one model base size is missing.",
            )
        )
    warnings.append(
        ToolkitWarning(
            warning_id="source-backed-mechanics-pending",
            detail="Board state remains estimated until source-backed mechanics are available.",
        )
    )
    return tuple(warnings)
```

- [ ] **Step 2: Run target tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_toolkit_contracts.py tests\test_board_state.py tests\test_application_service.py -q
```

Expected: all selected tests pass.

### Task 3: Run Regression And Quality Checks

**Files:**
- Test: `tests/test_toolkit_contracts.py`
- Test: `tests/test_board_state.py`
- Test: `tests/test_application_service.py`
- Test: `tests/test_los_geometry.py`
- Test: `tests/test_rendering_svg.py`

- [ ] **Step 1: Run targeted regression tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_toolkit_contracts.py tests\test_board_state.py tests\test_application_service.py tests\test_los_geometry.py tests\test_rendering_svg.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run type and style checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
```

Expected: all commands exit 0.

### Task 4: Review, QA, And Commit

**Files:**
- Create: `docs/superpowers/reviews/2026-06-20-phase-2-consultant-toolkit-foundation.md`
- Create: `docs/superpowers/reviews/2026-06-20-phase-2-adversarial-toolkit-foundation.md`
- Modify: `docs/work-log/player-toolkit-implementation.md`

- [ ] **Step 1: Record consultant and adversarial review outcomes**

The review files must include:

```markdown
## Final Status

Approved.
```

Only write `Approved` after the reviewer findings are triaged and any accepted fixes are applied.

- [ ] **Step 2: Run full Phase 2 QA**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_toolkit_contracts.py tests\test_board_state.py tests\test_application_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_toolkit_contracts.py tests\test_board_state.py tests\test_application_service.py tests\test_los_geometry.py tests\test_rendering_svg.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected: every command exits 0. Browser and Computer Use checks are waived because this phase
changes no web, desktop, rendered SVG, or packaged UI behavior.

- [ ] **Step 3: Commit an atomic checkpoint**

Run:

```powershell
git add docs/superpowers/specs/2026-06-20-toolkit-result-and-board-state-spec.md docs/superpowers/plans/2026-06-20-toolkit-result-and-board-state.md docs/superpowers/qa/2026-06-20-toolkit-result-and-board-state-qa.md docs/superpowers/reviews/2026-06-20-phase-2-consultant-toolkit-foundation.md docs/superpowers/reviews/2026-06-20-phase-2-adversarial-toolkit-foundation.md docs/work-log/player-toolkit-implementation.md src/warhammer_companion/domain/board_state.py src/warhammer_companion/domain/overlays.py src/warhammer_companion/application/toolkit.py src/warhammer_companion/application/services.py tests/test_toolkit_contracts.py tests/test_board_state.py tests/test_application_service.py
git commit -m "Add phase 2 toolkit foundation"
```

Expected: a single commit on `codex/assistant-companion-roadmap`. Do not stage `AGENTS.md`.
