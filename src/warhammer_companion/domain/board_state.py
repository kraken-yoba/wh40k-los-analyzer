from __future__ import annotations

import hashlib
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
BOARD_STATE_SCHEMA_VERSION = "board-state/v0"


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
    packet_digest: str
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
        return cls(
            state_id=state_id,
            packet=packet,
            packet_digest=map_packet_digest(packet),
            context=context or BoardStateContext(),
            units=units,
            source_ref_ids=source_ref_ids,
            readiness="estimated",
            assumptions=assumptions,
            warnings=_board_state_warnings(units),
        )


def _board_state_warnings(units: tuple[BoardUnit, ...]) -> tuple[ToolkitWarning, ...]:
    if not units:
        return (
            ToolkitWarning(
                warning_id="missing-units",
                detail=(
                    "Model positions and base sizes are missing; board state is diagnostic only."
                ),
            ),
        )

    warnings: list[ToolkitWarning] = []
    empty_units = [unit for unit in units if not unit.models]
    missing_position = any(model.position is None for unit in units for model in unit.models)
    missing_base = any(model.base_diameter is None for unit in units for model in unit.models)
    if empty_units:
        warnings.append(
            ToolkitWarning(
                warning_id="missing-unit-models",
                detail="At least one unit has no models with positions or base sizes.",
            )
        )
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


def map_packet_digest(packet: MapPacket) -> str:
    payload = f"{BOARD_STATE_SCHEMA_VERSION}|{packet.model_dump_json()}"
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
