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
from warhammer_companion.domain.threat import ThreatMode, ThreatProjectionRegion

ExposureMode = Literal["threat-only", "los-only", "threat-or-los", "threat-and-los"]
EXPOSURE_MODES: tuple[ExposureMode, ...] = get_args(ExposureMode)


@dataclass(frozen=True, slots=True)
class ExposureDiagnosticReason:
    reason_id: str
    detail: str


@dataclass(frozen=True, slots=True)
class ExposurePlacementDiagnostic:
    within_board: bool
    within_deployment_zone: bool
    clear_of_dense_features: bool
    exposed_to_los: bool
    exposed_to_threat: bool
    not_exposed_under_assumptions: bool
    reasons: tuple[ExposureDiagnosticReason, ...] = ()

    @property
    def reason_ids(self) -> tuple[str, ...]:
        return tuple(reason.reason_id for reason in self.reasons)


@dataclass(frozen=True, slots=True)
class DeploymentExposurePayload:
    packet: MapPacket
    deployment_zone_id: str
    friendly_center: tuple[float, float]
    friendly_base_diameter: float
    enemy_source_center: tuple[float, float]
    enemy_base_diameter: float
    enemy_move_distance: float
    enemy_threat_range: float
    enemy_threat_mode: ThreatMode
    exposure_mode: ExposureMode
    enemy_threat_regions: tuple[ThreatProjectionRegion, ...]
    enemy_los_region: BaseGeometry
    allowed_center_region: BaseGeometry
    risk_region: BaseGeometry
    candidate_center_region: BaseGeometry
    placement: ExposurePlacementDiagnostic
    threat_probability_at_center: float
    enemy_movement_profile_id: MovementProfileId = DEFAULT_MOVEMENT_PROFILE_ID
    enemy_movement_profile_label: str = MOVEMENT_PROFILES_BY_ID[DEFAULT_MOVEMENT_PROFILE_ID].label
    enemy_effective_move_distance: float = 0.0
    enemy_routing_metadata: MovementRoutingMetadata = field(default_factory=MovementRoutingMetadata)


def coerce_exposure_mode(value: str) -> ExposureMode:
    if value in EXPOSURE_MODES:
        return value
    return "threat-or-los"


def exposure_mode_includes_los(exposure_mode: ExposureMode) -> bool:
    """Return whether an exposure mode should render/use the LOS component."""
    return exposure_mode in {"los-only", "threat-or-los", "threat-and-los"}


def exposure_mode_includes_threat(exposure_mode: ExposureMode) -> bool:
    """Return whether an exposure mode should render/use the threat component."""
    return exposure_mode in {"threat-only", "threat-or-los", "threat-and-los"}
