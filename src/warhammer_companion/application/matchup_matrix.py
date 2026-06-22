from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Sequence

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.damage import DamageEstimatePayload
from warhammer_companion.domain.deployment_scorecard import DeploymentScorecardPayload
from warhammer_companion.domain.matchups import (
    TEAM_PAIRING_MATRIX_SCHEMA_VERSION,
    PairingAssessment,
    PairingCell,
    PairingComponentCard,
    PairingListEntry,
    PairingMatrixPayload,
    PairingMetric,
    PairingScenario,
    PairingScenarioRange,
)
from warhammer_companion.domain.missions import MissionPackPayload
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.overlays import ToolkitReadiness, ToolkitWarning

LabelInput = str | Sequence[str]

MAX_PAIRING_LABELS_PER_SIDE = 8
MAX_PAIRING_LABEL_LENGTH = 80
TEAM_PAIRING_WARNINGS = (
    "Labels-only matrix repeats shared scenario metrics; roster-specific matchup computation is "
    "unavailable.",
    "Mission context is source-pending; scoring and action mechanics are unavailable.",
    "Selection guidance unavailable until a validated pairing model exists.",
)
SHARED_METRIC_NOTICE = (
    "Labels-only cell uses shared scenario metrics; not pair-specific list-vs-list computation."
)


def build_team_pairing_matrix_toolkit_result(
    *,
    packet: MapPacket,
    friendly_labels: LabelInput,
    opponent_labels: LabelInput,
    damage_result: ToolkitResult[DamageEstimatePayload],
    mission_result: ToolkitResult[MissionPackPayload],
    deployment_scorecard_results: Sequence[ToolkitResult[DeploymentScorecardPayload]],
) -> ToolkitResult[PairingMatrixPayload]:
    friendly_lists, friendly_blockers = _normalize_list_entries("friendly", friendly_labels)
    opponent_lists, opponent_blockers = _normalize_list_entries("opponent", opponent_labels)
    block_reasons = friendly_blockers + opponent_blockers
    source_ref_ids = _source_ref_ids(mission_result, deployment_scorecard_results)
    input_hash = _team_pairing_hash(
        packet_id=packet.id,
        friendly_lists=friendly_lists,
        opponent_lists=opponent_lists,
        damage_result=damage_result,
        mission_result=mission_result,
        deployment_scorecard_results=deployment_scorecard_results,
    )
    suffix = input_hash.removeprefix("sha256:")[:12]
    scenarios = _scenarios(
        packet=packet,
        mission_result=mission_result,
        deployment_scorecard_results=deployment_scorecard_results,
        source_ref_ids=source_ref_ids,
    )
    ranges = _scenario_ranges(
        damage_result=damage_result,
        deployment_scorecard_results=deployment_scorecard_results,
    )
    if block_reasons:
        return ToolkitResult(
            result_id=f"manual:team-pairing-matrix:{suffix}",
            tool_id="team_pairing_matrix",
            input_hash=input_hash,
            readiness="blocked",
            payload=PairingMatrixPayload(
                friendly_lists=friendly_lists,
                opponent_lists=opponent_lists,
                scenarios=scenarios,
                cells=(),
                ranges=ranges,
                warnings=TEAM_PAIRING_WARNINGS,
            ),
            warnings=_toolkit_warnings(),
            block_reasons=block_reasons,
            source_ref_ids=source_ref_ids,
        )

    components = _components(
        damage_result=damage_result,
        mission_result=mission_result,
        deployment_scorecard_results=deployment_scorecard_results,
    )
    cells = tuple(
        PairingCell(
            friendly_list_id=friendly.list_id,
            opponent_list_id=opponent.list_id,
            readiness=_cell_readiness(components),
            scenario_ids=tuple(scenario.scenario_id for scenario in scenarios),
            components=components,
            shared_metric_notice=SHARED_METRIC_NOTICE,
        )
        for friendly in friendly_lists
        for opponent in opponent_lists
    )
    no_usable_components = all(cell.readiness == "blocked" for cell in cells)
    result_block_reasons = (
        (
            BlockReason(
                reason_id="no-usable-pairing-components",
                detail="No deterministic source component is usable for the matrix.",
            ),
        )
        if no_usable_components
        else ()
    )
    readiness: ToolkitReadiness = "blocked" if no_usable_components else "degraded"
    return ToolkitResult(
        result_id=f"manual:team-pairing-matrix:{suffix}",
        tool_id="team_pairing_matrix",
        input_hash=input_hash,
        readiness=readiness,
        payload=PairingMatrixPayload(
            friendly_lists=friendly_lists,
            opponent_lists=opponent_lists,
            scenarios=scenarios,
            cells=cells,
            ranges=ranges,
            warnings=TEAM_PAIRING_WARNINGS,
        ),
        warnings=_toolkit_warnings(),
        block_reasons=result_block_reasons,
        source_ref_ids=source_ref_ids,
    )


def _normalize_list_entries(
    side: str,
    labels: LabelInput,
) -> tuple[tuple[PairingListEntry, ...], tuple[BlockReason, ...]]:
    normalized = _normalized_labels(labels)
    reasons: list[BlockReason] = []
    if not normalized:
        reasons.append(
            BlockReason(
                reason_id=f"missing-{side}-lists",
                detail=f"Enter at least one {side} list label.",
            )
        )
    if len(normalized) > MAX_PAIRING_LABELS_PER_SIDE:
        reasons.append(
            BlockReason(
                reason_id=f"too-many-{side}-lists",
                detail=f"Enter no more than {MAX_PAIRING_LABELS_PER_SIDE} {side} list labels.",
            )
        )
    if any(len(label) > MAX_PAIRING_LABEL_LENGTH for label in normalized):
        reasons.append(
            BlockReason(
                reason_id=f"{side}-list-label-too-long",
                detail=(
                    f"{side.title()} list labels must be "
                    f"{MAX_PAIRING_LABEL_LENGTH} characters or less."
                ),
            )
        )
    seen: set[str] = set()
    duplicate_found = False
    for label in normalized:
        key = label.casefold()
        if key in seen:
            duplicate_found = True
            break
        seen.add(key)
    if duplicate_found:
        reasons.append(
            BlockReason(
                reason_id=f"duplicate-{side}-list-label",
                detail=f"{side.title()} list labels must be unique after normalization.",
            )
        )
    entries = tuple(
        PairingListEntry(list_id=f"{side}-{index}", label=label)
        for index, label in enumerate(normalized, start=1)
    )
    return entries, tuple(reasons)


def _normalized_labels(labels: LabelInput) -> tuple[str, ...]:
    fragments: list[str] = []
    for raw_label in _raw_label_items(labels):
        normalized_text = _normalize_raw_label_text(raw_label)
        fragments.extend(re.split(r"[,\n]+", normalized_text))
    return tuple(
        label for fragment in fragments if (label := re.sub(r"\s+", " ", fragment).strip())
    )


def _raw_label_items(labels: LabelInput) -> tuple[str, ...]:
    if isinstance(labels, str):
        return (labels,)
    return tuple(str(label) for label in labels)


def _normalize_raw_label_text(raw_label: str) -> str:
    normalized = raw_label.replace("\r\n", "\n").replace("\r", "\n")
    chars: list[str] = []
    for char in normalized:
        if char in {",", "\n"}:
            chars.append(char)
        elif char.isspace():
            chars.append(" ")
        elif char.isprintable():
            chars.append(char)
    return "".join(chars)


def _scenarios(
    *,
    packet: MapPacket,
    mission_result: ToolkitResult[MissionPackPayload],
    deployment_scorecard_results: Sequence[ToolkitResult[DeploymentScorecardPayload]],
    source_ref_ids: tuple[str, ...],
) -> tuple[PairingScenario, ...]:
    return (
        PairingScenario(
            scenario_id="scenario-1",
            packet_id=packet.id,
            packet_label=packet.name,
            mission_pack_result_id=mission_result.result_id,
            mission_pack_readiness=_component_readiness(mission_result.readiness),
            deployment_scorecard_result_ids=tuple(
                result.result_id for result in deployment_scorecard_results
            ),
            turn_orders=tuple(result.payload.turn_order for result in deployment_scorecard_results),
            source_ref_ids=source_ref_ids,
            detail=(
                "Labels-only shared scenario; deterministic metrics repeat across matrix cells and "
                "are not pair-specific."
            ),
        ),
    )


def _components(
    *,
    damage_result: ToolkitResult[DamageEstimatePayload],
    mission_result: ToolkitResult[MissionPackPayload],
    deployment_scorecard_results: Sequence[ToolkitResult[DeploymentScorecardPayload]],
) -> tuple[PairingComponentCard, ...]:
    return (
        _damage_component(damage_result),
        _mission_component(mission_result),
        _deployment_component(deployment_scorecard_results),
        _unsupported_component(),
    )


def _damage_component(
    result: ToolkitResult[DamageEstimatePayload],
) -> PairingComponentCard:
    if result.is_blocked:
        return PairingComponentCard(
            component_id="damage-output",
            label="Damage Output",
            assessment="blocked",
            readiness="blocked",
            detail="Shared manual damage-output component is blocked until inputs are valid.",
            source_tool_id=result.tool_id,
            source_result_id=result.result_id,
            source_input_hash=result.input_hash,
            warnings=_warning_details(result),
            block_reasons=_block_reason_details(result),
        )
    summary = result.payload.summary
    return PairingComponentCard(
        component_id="damage-output",
        label="Damage Output",
        assessment="checked",
        readiness=_component_readiness(result.readiness),
        detail=(
            "Shared scenario metric from the manual damage profile; not pair-specific and not "
            "roster-derived."
        ),
        source_tool_id=result.tool_id,
        source_result_id=result.result_id,
        source_input_hash=result.input_hash,
        metrics=(
            PairingMetric(
                metric_id="expected-damage",
                label="Shared expected damage",
                value=summary.expected_damage,
                units="damage",
            ),
            PairingMetric(
                metric_id="expected-models-destroyed",
                label="Shared expected models destroyed",
                value=summary.expected_models_destroyed,
                units="models",
            ),
        ),
        warnings=_warning_details(result),
    )


def _mission_component(
    result: ToolkitResult[MissionPackPayload],
) -> PairingComponentCard:
    assessment: PairingAssessment = "blocked" if result.is_blocked else "warning"
    readiness: ToolkitReadiness = "blocked" if result.is_blocked else "degraded"
    return PairingComponentCard(
        component_id="mission-context",
        label="Mission Context",
        assessment=assessment,
        readiness=readiness,
        detail=(
            "Shared mission context is source-pending; scoring and action mechanics are "
            "unavailable."
        ),
        source_tool_id=result.tool_id,
        source_result_id=result.result_id,
        source_input_hash=result.input_hash,
        source_ref_ids=result.source_ref_ids,
        warnings=_warning_details(result),
        block_reasons=_block_reason_details(result),
    )


def _deployment_component(
    results: Sequence[ToolkitResult[DeploymentScorecardPayload]],
) -> PairingComponentCard:
    result_tuple = tuple(results)
    usable = tuple(result for result in result_tuple if result.is_usable)
    if not usable:
        return PairingComponentCard(
            component_id="deployment-staging",
            label="Deployment Staging",
            assessment="blocked",
            readiness="blocked",
            detail=(
                "Shared deployment-staging component is blocked until manual staging inputs run."
            ),
            source_tool_id="deployment_scorecard",
            source_result_id=",".join(result.result_id for result in result_tuple) or None,
            source_input_hash=",".join(result.input_hash for result in result_tuple) or None,
            block_reasons=tuple(
                reason for result in result_tuple for reason in _block_reason_details(result)
            ),
            warnings=tuple(
                warning for result in result_tuple for warning in _warning_details(result)
            ),
        )
    metrics = tuple(
        PairingMetric(
            metric_id=f"threat-probability-at-center-{result.payload.turn_order}",
            label=f"Shared threat probability at selected point ({result.payload.turn_order})",
            value=result.payload.threat_probability_at_center,
            units="probability",
        )
        for result in usable
    )
    return PairingComponentCard(
        component_id="deployment-staging",
        label="Deployment Staging",
        assessment="checked" if len(usable) == len(result_tuple) else "warning",
        readiness="degraded" if len(usable) != len(result_tuple) else "estimated",
        detail=(
            "Shared deployment-staging diagnostics from manual turn-order scorecards; not "
            "pair-specific."
        ),
        source_tool_id="deployment_scorecard",
        source_result_id=",".join(result.result_id for result in result_tuple),
        source_input_hash=",".join(result.input_hash for result in result_tuple),
        source_ref_ids=_unique_ids(
            source_ref_id for result in result_tuple for source_ref_id in result.source_ref_ids
        ),
        metrics=metrics,
        warnings=tuple(warning for result in result_tuple for warning in _warning_details(result)),
        block_reasons=tuple(
            reason for result in result_tuple for reason in _block_reason_details(result)
        ),
    )


def _unsupported_component() -> PairingComponentCard:
    return PairingComponentCard(
        component_id="unsupported-data",
        label="Unsupported Data",
        assessment="not_available",
        readiness="degraded",
        detail=(
            "Roster-aware mission scoring, objective/action reliability, mobility screening gaps, "
            "matchup weighting, selection guidance, and tournament-point model are unavailable in "
            "Phase 11A."
        ),
    )


def _scenario_ranges(
    *,
    damage_result: ToolkitResult[DamageEstimatePayload],
    deployment_scorecard_results: Sequence[ToolkitResult[DeploymentScorecardPayload]],
) -> tuple[PairingScenarioRange, ...]:
    ranges: list[PairingScenarioRange] = []
    if damage_result.is_usable:
        summary = damage_result.payload.summary
        ranges.append(
            PairingScenarioRange(
                metric_id="expected-damage",
                label="Shared expected damage",
                min_value=summary.expected_damage,
                max_value=summary.expected_damage,
                units="damage",
            )
        )
        ranges.append(
            PairingScenarioRange(
                metric_id="expected-models-destroyed",
                label="Shared expected models destroyed",
                min_value=summary.expected_models_destroyed,
                max_value=summary.expected_models_destroyed,
                units="models",
            )
        )
    threat_values = [
        result.payload.threat_probability_at_center
        for result in deployment_scorecard_results
        if result.is_usable
    ]
    if threat_values:
        ranges.append(
            PairingScenarioRange(
                metric_id="threat-probability-at-center",
                label="Shared threat probability at selected point",
                min_value=min(threat_values),
                max_value=max(threat_values),
                units="probability",
            )
        )
    return tuple(ranges)


def _cell_readiness(components: tuple[PairingComponentCard, ...]) -> ToolkitReadiness:
    usable_source_components = [
        component
        for component in components
        if component.component_id != "unsupported-data" and component.assessment != "blocked"
    ]
    if not usable_source_components:
        return "blocked"
    return "degraded"


def _component_readiness(readiness: ToolkitReadiness) -> ToolkitReadiness:
    if readiness == "trusted":
        return "estimated"
    return readiness


def _source_ref_ids(
    mission_result: ToolkitResult[MissionPackPayload],
    deployment_scorecard_results: Sequence[ToolkitResult[DeploymentScorecardPayload]],
) -> tuple[str, ...]:
    return _unique_ids(
        (
            *mission_result.source_ref_ids,
            *(
                source_ref_id
                for result in deployment_scorecard_results
                for source_ref_id in result.source_ref_ids
            ),
        )
    )


def _unique_ids(source_ref_ids: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for source_ref_id in source_ref_ids:
        if source_ref_id in seen:
            continue
        seen.add(source_ref_id)
        ordered.append(source_ref_id)
    return tuple(ordered)


def _warning_details(result: ToolkitResult[object]) -> tuple[str, ...]:
    return tuple(warning.detail for warning in result.warnings)


def _block_reason_details(result: ToolkitResult[object]) -> tuple[str, ...]:
    return tuple(f"{reason.reason_id}: {reason.detail}" for reason in result.block_reasons)


def _toolkit_warnings() -> tuple[ToolkitWarning, ...]:
    return (
        ToolkitWarning(
            warning_id="labels-only-shared-scenario",
            detail=TEAM_PAIRING_WARNINGS[0],
        ),
        ToolkitWarning(
            warning_id="mission-context-source-pending",
            detail=TEAM_PAIRING_WARNINGS[1],
        ),
        ToolkitWarning(
            warning_id="pairing-model-unavailable",
            detail=TEAM_PAIRING_WARNINGS[2],
        ),
    )


def _team_pairing_hash(
    *,
    packet_id: str,
    friendly_lists: tuple[PairingListEntry, ...],
    opponent_lists: tuple[PairingListEntry, ...],
    damage_result: ToolkitResult[DamageEstimatePayload],
    mission_result: ToolkitResult[MissionPackPayload],
    deployment_scorecard_results: Sequence[ToolkitResult[DeploymentScorecardPayload]],
) -> str:
    payload = {
        "damage_input_hash": damage_result.input_hash,
        "deployment_scorecard_input_hashes": [
            result.input_hash for result in deployment_scorecard_results
        ],
        "friendly_labels": [entry.label for entry in friendly_lists],
        "mission_pack_input_hash": mission_result.input_hash,
        "opponent_labels": [entry.label for entry in opponent_lists],
        "packet_id": packet_id,
        "schema_version": TEAM_PAIRING_MATRIX_SCHEMA_VERSION,
        "tool_id": "team_pairing_matrix",
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
