from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, get_args

from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from warhammer_companion.domain.models import MapPacket

MovementMode = Literal["normal", "advance", "charge", "scout", "ingress", "disembark"]
MOVEMENT_MODES: tuple[MovementMode, ...] = get_args(MovementMode)
MovementProfileId = Literal[
    "ground-non-mobile",
    "ground-mobile",
    "fly-take-to-skies",
    "fly-hover-take-to-skies",
]
MOVEMENT_PROFILE_IDS: tuple[MovementProfileId, ...] = get_args(MovementProfileId)
DEFAULT_MOVEMENT_PROFILE_ID: MovementProfileId = "ground-non-mobile"
MOVEMENT_ROUTING_ALGORITHM_VERSION = "movement-grid-route/v1"
DEFAULT_ROUTING_RESOLUTION_INCHES = 1.0
MOVEMENT_ROUTING_TOLERANCE_INCHES = 0.01
MAX_ROUTING_GRID_NODES = 8_000


@dataclass(frozen=True, slots=True)
class MovementProfile:
    profile_id: MovementProfileId
    label: str
    traversal_policy: str
    endpoint_occupancy_policy: str
    effective_move_penalty: float = 0.0

    @property
    def ignores_dense_traversal(self) -> bool:
        return self.traversal_policy == "dense-features-ignored-for-traversal"


MOVEMENT_PROFILES: tuple[MovementProfile, ...] = (
    MovementProfile(
        profile_id="ground-non-mobile",
        label="Ground non-mobile",
        traversal_policy="dense-features-block-traversal",
        endpoint_occupancy_policy="dense-features-block-ending-base",
    ),
    MovementProfile(
        profile_id="ground-mobile",
        label="Ground mobile / infantry",
        traversal_policy="dense-features-ignored-for-traversal",
        endpoint_occupancy_policy="dense-features-block-ending-base",
    ),
    MovementProfile(
        profile_id="fly-take-to-skies",
        label="Fly: Take to the Skies",
        traversal_policy="dense-features-ignored-for-traversal",
        endpoint_occupancy_policy="dense-features-block-ending-base",
        effective_move_penalty=2.0,
    ),
    MovementProfile(
        profile_id="fly-hover-take-to-skies",
        label="Fly: Hover / no-cost Take to the Skies",
        traversal_policy="dense-features-ignored-for-traversal",
        endpoint_occupancy_policy="dense-features-block-ending-base",
    ),
)
MOVEMENT_PROFILES_BY_ID: dict[MovementProfileId, MovementProfile] = {
    profile.profile_id: profile for profile in MOVEMENT_PROFILES
}


@dataclass(frozen=True, slots=True)
class MovementRoutingMetadata:
    algorithm_version: str = MOVEMENT_ROUTING_ALGORITHM_VERSION
    resolution_inches: float = DEFAULT_ROUTING_RESOLUTION_INCHES
    tolerance_inches: float = MOVEMENT_ROUTING_TOLERANCE_INCHES
    traversal_policy: str = MOVEMENT_PROFILES_BY_ID[DEFAULT_MOVEMENT_PROFILE_ID].traversal_policy
    endpoint_occupancy_policy: str = MOVEMENT_PROFILES_BY_ID[
        DEFAULT_MOVEMENT_PROFILE_ID
    ].endpoint_occupancy_policy
    node_count: int = 0
    snapped_endpoint: tuple[float, float] | None = None


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
    route_distance: float | None = None
    route_points: tuple[tuple[float, float], ...] = ()
    effective_move_distance: float = 0.0
    routing_metadata: MovementRoutingMetadata = field(default_factory=MovementRoutingMetadata)

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
    movement_profile_id: MovementProfileId = DEFAULT_MOVEMENT_PROFILE_ID
    movement_profile_label: str = MOVEMENT_PROFILES_BY_ID[DEFAULT_MOVEMENT_PROFILE_ID].label
    effective_move_distance: float = 0.0
    routing_metadata: MovementRoutingMetadata = field(default_factory=MovementRoutingMetadata)
    route_path: BaseGeometry = field(default_factory=Polygon)


def coerce_movement_mode(value: str) -> MovementMode:
    if value in MOVEMENT_MODES:
        return value
    return "normal"


def coerce_movement_profile_id(value: str) -> MovementProfileId:
    if value in MOVEMENT_PROFILE_IDS:
        return value
    return DEFAULT_MOVEMENT_PROFILE_ID


def movement_profile_for_id(value: str) -> MovementProfile:
    return MOVEMENT_PROFILES_BY_ID[coerce_movement_profile_id(value)]


def effective_move_distance(move_distance: float, movement_profile_id: str) -> float:
    profile = movement_profile_for_id(movement_profile_id)
    return max(0.0, move_distance - profile.effective_move_penalty)
