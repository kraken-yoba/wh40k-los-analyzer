from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

from warhammer_companion.domain.overlays import ToolkitReadiness

TEAM_PAIRING_MATRIX_SCHEMA_VERSION = "team-pairing-matrix/v0"

PairingComponentId = Literal[
    "damage-output",
    "mission-context",
    "deployment-staging",
    "unsupported-data",
]
PAIRING_COMPONENT_IDS: tuple[PairingComponentId, ...] = get_args(PairingComponentId)

PairingAssessment = Literal["checked", "warning", "blocked", "not_available"]
PAIRING_ASSESSMENTS: tuple[PairingAssessment, ...] = get_args(PairingAssessment)

PAIRING_METRIC_SCOPE = "shared_scenario"


@dataclass(frozen=True, slots=True)
class PairingListEntry:
    list_id: str
    label: str


@dataclass(frozen=True, slots=True)
class PairingMetric:
    metric_id: str
    label: str
    value: float
    units: str
    scope: str = PAIRING_METRIC_SCOPE


@dataclass(frozen=True, slots=True)
class PairingScenarioRange:
    metric_id: str
    label: str
    min_value: float
    max_value: float
    units: str
    scope: str = PAIRING_METRIC_SCOPE


@dataclass(frozen=True, slots=True)
class PairingScenario:
    scenario_id: str
    packet_id: str
    packet_label: str
    mission_pack_result_id: str
    mission_pack_readiness: ToolkitReadiness
    deployment_scorecard_result_ids: tuple[str, ...]
    turn_orders: tuple[str, ...]
    source_ref_ids: tuple[str, ...]
    detail: str


@dataclass(frozen=True, slots=True)
class PairingComponentCard:
    component_id: PairingComponentId
    label: str
    assessment: PairingAssessment
    readiness: ToolkitReadiness
    detail: str
    source_tool_id: str | None = None
    source_result_id: str | None = None
    source_input_hash: str | None = None
    source_ref_ids: tuple[str, ...] = ()
    metrics: tuple[PairingMetric, ...] = ()
    warnings: tuple[str, ...] = ()
    block_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.component_id not in PAIRING_COMPONENT_IDS:
            raise ValueError(f"Unknown pairing component: {self.component_id}")
        if self.assessment not in PAIRING_ASSESSMENTS:
            raise ValueError(f"Unknown pairing assessment: {self.assessment}")


@dataclass(frozen=True, slots=True)
class PairingCell:
    friendly_list_id: str
    opponent_list_id: str
    readiness: ToolkitReadiness
    scenario_ids: tuple[str, ...]
    components: tuple[PairingComponentCard, ...]
    shared_metric_notice: str


@dataclass(frozen=True, slots=True)
class PairingMatrixPayload:
    friendly_lists: tuple[PairingListEntry, ...]
    opponent_lists: tuple[PairingListEntry, ...]
    scenarios: tuple[PairingScenario, ...]
    cells: tuple[PairingCell, ...]
    ranges: tuple[PairingScenarioRange, ...]
    warnings: tuple[str, ...]
