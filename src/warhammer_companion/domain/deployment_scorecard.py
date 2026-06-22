from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

from warhammer_companion.domain.exposure import DeploymentExposurePayload
from warhammer_companion.domain.missions import MissionSourceRef
from warhammer_companion.domain.models import MapPacket

TurnOrderAssumption = Literal["going-first", "going-second"]
TURN_ORDER_ASSUMPTIONS: tuple[TurnOrderAssumption, ...] = get_args(TurnOrderAssumption)

DeploymentScorecardAssessment = Literal["checked", "warning", "blocked"]
DEPLOYMENT_SCORECARD_ASSESSMENTS: tuple[DeploymentScorecardAssessment, ...] = get_args(
    DeploymentScorecardAssessment
)

DeploymentScorecardComponentId = Literal[
    "deployment-fit",
    "selected-exposure",
    "mission-readiness",
    "turn-order-assumption",
]
DEPLOYMENT_SCORECARD_COMPONENT_IDS: tuple[DeploymentScorecardComponentId, ...] = get_args(
    DeploymentScorecardComponentId
)


@dataclass(frozen=True, slots=True)
class DeploymentScorecardComponent:
    component_id: DeploymentScorecardComponentId
    label: str
    assessment: DeploymentScorecardAssessment
    detail: str
    source_ref_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.component_id not in DEPLOYMENT_SCORECARD_COMPONENT_IDS:
            raise ValueError(f"Unknown deployment scorecard component: {self.component_id}")
        if self.assessment not in DEPLOYMENT_SCORECARD_ASSESSMENTS:
            raise ValueError(f"Unknown deployment scorecard assessment: {self.assessment}")


@dataclass(frozen=True, slots=True)
class DeploymentScorecardPayload:
    packet: MapPacket
    deployment_zone_id: str
    friendly_center: tuple[float, float]
    friendly_base_diameter: float
    enemy_source_center: tuple[float, float]
    enemy_base_diameter: float
    enemy_move_distance: float
    enemy_threat_range: float
    enemy_threat_mode: str
    exposure_mode: str
    turn_order: str
    deployment_exposure_result_id: str
    deployment_exposure_readiness: str
    deployment_exposure: DeploymentExposurePayload
    mission_pack_result_id: str
    mission_pack_readiness: str
    mission_source_refs: tuple[MissionSourceRef, ...]
    components: tuple[DeploymentScorecardComponent, ...]
    not_exposed_under_assumptions: bool
    threat_probability_at_center: float
