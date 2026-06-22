from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, get_args

from shapely.geometry.base import BaseGeometry

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.movement import (
    DEFAULT_MOVEMENT_PROFILE_ID,
    MOVEMENT_PROFILES_BY_ID,
    MovementProfileId,
    MovementRoutingMetadata,
)

ThreatMode = Literal[
    "raw-range",
    "fixed-move-plus-range",
    "d6-move-plus-range",
    "2d6-move-plus-range",
]
THREAT_MODES: tuple[ThreatMode, ...] = get_args(ThreatMode)
THREAT_MEASUREMENT_CONVENTION = "source-base-edge-to-target-point"


@dataclass(frozen=True, slots=True)
class ThreatDiceOutcome:
    dice_label: str
    variable_inches: int
    numerator: int
    denominator: int
    probability: float
    total_reach: float
    effective_move_distance: float = 0.0


@dataclass(frozen=True, slots=True)
class ThreatProjectionRegion:
    outcome: ThreatDiceOutcome
    geometry: BaseGeometry


@dataclass(frozen=True, slots=True)
class ThreatRangePayload:
    packet: MapPacket
    mode: ThreatMode
    source_center: tuple[float, float]
    target_point: tuple[float, float]
    base_diameter: float
    move_distance: float
    threat_range: float
    measurement_convention: str
    distribution: tuple[ThreatDiceOutcome, ...]
    threat_regions: tuple[ThreatProjectionRegion, ...]
    max_threat_region: BaseGeometry
    target_probability: float
    movement_profile_id: MovementProfileId = DEFAULT_MOVEMENT_PROFILE_ID
    movement_profile_label: str = MOVEMENT_PROFILES_BY_ID[DEFAULT_MOVEMENT_PROFILE_ID].label
    effective_move_distance: float = 0.0
    routing_metadata: MovementRoutingMetadata = field(default_factory=MovementRoutingMetadata)


def coerce_threat_mode(value: str) -> ThreatMode:
    if value in THREAT_MODES:
        return value
    return "raw-range"
