from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

from shapely.geometry.base import BaseGeometry

from warhammer_companion.domain.models import MapPacket

MovementMode = Literal["normal", "advance", "charge", "scout", "ingress", "disembark"]
MOVEMENT_MODES: tuple[MovementMode, ...] = get_args(MovementMode)


@dataclass(frozen=True, slots=True)
class MovementDiagnosticReason:
    reason_id: str
    detail: str


@dataclass(frozen=True, slots=True)
class MovementEndpointDiagnostic:
    distance: float
    within_distance: bool
    within_board: bool
    clear_of_dense_features: bool
    estimated_reachable: bool
    reasons: tuple[MovementDiagnosticReason, ...] = ()

    @property
    def reason_ids(self) -> tuple[str, ...]:
        return tuple(reason.reason_id for reason in self.reasons)


@dataclass(frozen=True, slots=True)
class MovementReachPayload:
    packet: MapPacket
    mode: MovementMode
    start_center: tuple[float, float]
    target_center: tuple[float, float]
    base_diameter: float
    move_distance: float
    movement_envelope: BaseGeometry
    swept_path: BaseGeometry
    endpoint: MovementEndpointDiagnostic
    dense_collision_regions: BaseGeometry


def coerce_movement_mode(value: str) -> MovementMode:
    if value in MOVEMENT_MODES:
        return value
    return "normal"
