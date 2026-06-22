from __future__ import annotations

import re
from dataclasses import replace

import pytest

from warhammer_companion.application.damage_profile import build_damage_profile_toolkit_result
from warhammer_companion.application.deployment_scorecard import (
    build_deployment_scorecard_toolkit_result,
)
from warhammer_companion.application.matchup_matrix import (
    build_team_pairing_matrix_toolkit_result,
)
from warhammer_companion.application.mission_pack import (
    PUBLIC_MISSION_SHEET_GID,
    PUBLIC_MISSION_SHEET_ID,
    build_mission_pack_toolkit_result,
)
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_team_pairing_matrix_is_degraded_labels_only_component_dossier() -> None:
    result = _build_matrix()
    text = _visible_result_text(result)

    assert result.tool_id == "team_pairing_matrix"
    assert result.readiness == "degraded"
    assert not result.allows_recommendation_language()
    assert result.overlays == ()
    assert len(result.payload.cells) == 4
    assert not hasattr(result.payload, "total_score")
    assert not hasattr(result.payload, "rank")
    assert not hasattr(result.payload, "grade")
    assert not hasattr(result.payload, "expected_points")
    assert not hasattr(result.payload, "win_probability")
    assert not hasattr(result.payload, "recommendation")
    assert "labels-only" in text
    assert "shared scenario" in text
    assert "not pair-specific" in text

    for cell in result.payload.cells:
        component_ids = [component.component_id for component in cell.components]
        assert component_ids == [
            "damage-output",
            "mission-context",
            "deployment-staging",
            "unsupported-data",
        ]
        assert cell.readiness == "degraded"
        assert "not pair-specific" in cell.shared_metric_notice.lower()
        for component in cell.components:
            for metric in component.metrics:
                assert metric.scope == "shared_scenario"

    unsupported = result.payload.cells[0].components[-1]
    assert unsupported.component_id == "unsupported-data"
    assert unsupported.assessment == "not_available"
    assert unsupported.readiness == "degraded"
    assert unsupported.source_tool_id is None
    assert unsupported.source_result_id is None
    assert unsupported.source_input_hash is None


@pytest.mark.parametrize(
    ("friendly_labels", "opponent_labels", "expected_reason"),
    [
        (" \n, ", "Gamma", "missing-friendly-lists"),
        ("Alpha", " \n, ", "missing-opponent-lists"),
        (
            "A,B,C,D,E,F,G,H,I",
            "Gamma",
            "too-many-friendly-lists",
        ),
        (
            "Alpha",
            "A,B,C,D,E,F,G,H,I",
            "too-many-opponent-lists",
        ),
        ("Alpha\n Alpha ", "Gamma", "duplicate-friendly-list-label"),
        ("Alpha", "Gamma\nGamma", "duplicate-opponent-list-label"),
        ("A" * 81, "Gamma", "friendly-list-label-too-long"),
        ("Alpha", "B" * 81, "opponent-list-label-too-long"),
    ],
)
def test_team_pairing_matrix_blocks_invalid_manual_labels(
    friendly_labels: str,
    opponent_labels: str,
    expected_reason: str,
) -> None:
    result = _build_matrix(friendly_labels=friendly_labels, opponent_labels=opponent_labels)

    assert result.readiness == "blocked"
    assert result.payload.cells == ()
    assert expected_reason in [reason.reason_id for reason in result.block_reasons]


def test_team_pairing_matrix_normalizes_labels_without_reordering() -> None:
    result = _build_matrix(
        friendly_labels="Alpha  Prime,,  Beta\nControl\x07Name",
        opponent_labels="Gamma,, Delta",
    )

    assert [entry.list_id for entry in result.payload.friendly_lists] == [
        "friendly-1",
        "friendly-2",
        "friendly-3",
    ]
    assert [entry.label for entry in result.payload.friendly_lists] == [
        "Alpha Prime",
        "Beta",
        "ControlName",
    ]
    assert [entry.list_id for entry in result.payload.opponent_lists] == [
        "opponent-1",
        "opponent-2",
    ]
    assert [entry.label for entry in result.payload.opponent_lists] == ["Gamma", "Delta"]


def test_team_pairing_matrix_identity_changes_with_labels_and_source_inputs() -> None:
    base = _build_matrix()
    changed_label = _build_matrix(friendly_labels=("Alpha", "Omega"))
    changed_damage = _build_matrix(
        damage_result=replace(_damage_result(), input_hash=f"sha256:{'0' * 64}")
    )

    assert base.input_hash != changed_label.input_hash
    assert base.input_hash != changed_damage.input_hash
    assert base.result_id.endswith(base.input_hash.removeprefix("sha256:")[:12])


def test_team_pairing_matrix_housekeeping_preserves_characterized_identities() -> None:
    cases = {
        "valid": (
            ("Alpha", "Beta"),
            ("Gamma", "Delta"),
            "sha256:b740bd349e0df60ce3813a73962ccb7441bc5b2811ca2cee4734f5f798609998",
            "manual:team-pairing-matrix:b740bd349e0d",
            [],
        ),
        "missing": (
            "",
            "Gamma",
            "sha256:33c693d610bd1284ac38553343fbb4a5705b9333f00c6bbfee275fb1392e4343",
            "manual:team-pairing-matrix:33c693d610bd",
            ["missing-friendly-lists"],
        ),
        "overflow": (
            "A\nB\nC\nD\nE\nF\nG\nH\nI",
            "Gamma",
            "sha256:551b8244b64bec06cdd00e39fbc39d0a01e2d758c033cf5c932d3da0c719df53",
            "manual:team-pairing-matrix:551b8244b64b",
            ["too-many-friendly-lists"],
        ),
        "duplicate": (
            "Alpha\n Alpha ",
            "Gamma",
            "sha256:fa38113d7195d4d47599e9a2d032abf2a0a04fbc6b46d9c3fb12bfde9a2445c9",
            "manual:team-pairing-matrix:fa38113d7195",
            ["duplicate-friendly-list-label"],
        ),
        "overlong": (
            "A" * 81,
            "Gamma",
            "sha256:e70c3fcd82ed7ee567db24d0459df84e8e0640af382e5868250cda3f0a6d1c4e",
            "manual:team-pairing-matrix:e70c3fcd82ed",
            ["friendly-list-label-too-long"],
        ),
    }

    for friendly, opponent, input_hash, result_id, reason_ids in cases.values():
        result = _build_matrix(friendly_labels=friendly, opponent_labels=opponent)

        assert result.input_hash == input_hash
        assert result.result_id == result_id
        assert [reason.reason_id for reason in result.block_reasons] == reason_ids


def test_team_pairing_matrix_housekeeping_preserves_normalized_label_outputs() -> None:
    result = _build_matrix(
        friendly_labels="Alpha  Prime,,  Beta\nControl\x07Name",
        opponent_labels="Gamma,, Delta",
    )

    assert [entry.label for entry in result.payload.friendly_lists] == [
        "Alpha Prime",
        "Beta",
        "ControlName",
    ]
    assert [entry.label for entry in result.payload.opponent_lists] == ["Gamma", "Delta"]
    assert [entry.list_id for entry in result.payload.friendly_lists] == [
        "friendly-1",
        "friendly-2",
        "friendly-3",
    ]
    assert [entry.list_id for entry in result.payload.opponent_lists] == [
        "opponent-1",
        "opponent-2",
    ]


def test_team_pairing_matrix_scenario_ranges_are_deterministic_shared_values() -> None:
    deployment_results = _deployment_results()
    result = _build_matrix(deployment_results=deployment_results)

    ranges = {scenario_range.metric_id: scenario_range for scenario_range in result.payload.ranges}
    threat_values = [source.payload.threat_probability_at_center for source in deployment_results]

    assert ranges["expected-damage"].min_value == pytest.approx(0.5)
    assert ranges["expected-damage"].max_value == pytest.approx(0.5)
    assert ranges["expected-models-destroyed"].min_value == pytest.approx(0.25)
    assert ranges["expected-models-destroyed"].max_value == pytest.approx(0.25)
    assert ranges["threat-probability-at-center"].min_value == pytest.approx(min(threat_values))
    assert ranges["threat-probability-at-center"].max_value == pytest.approx(max(threat_values))
    assert all(scenario_range.scope == "shared_scenario" for scenario_range in ranges.values())


def test_team_pairing_matrix_visible_text_avoids_authority_claims() -> None:
    text = _visible_result_text(_build_matrix())

    for forbidden in (
        "legal",
        "safe",
        "optimal",
        "recommended",
        "likely",
        "guaranteed",
        "preferred",
        "pairing score",
        "expected points",
        "win probability",
        "favored",
        "calibrated",
    ):
        assert re.search(rf"\b{re.escape(forbidden)}\b", text) is None


def test_team_pairing_matrix_payload_is_sanitized_and_not_trusted() -> None:
    result = _build_matrix()
    serialized = repr(result.payload).lower()

    assert result.readiness != "trusted"
    assert result.overlays == ()
    for cell in result.payload.cells:
        for component in cell.components:
            assert component.readiness in {"trusted", "estimated", "degraded", "blocked"}
            assert component.readiness != "not_available"

    for forbidden in (
        "mappacket",
        "damageestimatepayload",
        "missionpackpayload",
        "deploymentscorecardpayload",
        "polygon",
        "linestring",
        "<svg",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        "docs.google.com",
        PUBLIC_MISSION_SHEET_ID.lower(),
        PUBLIC_MISSION_SHEET_GID,
        "mission card",
    ):
        assert forbidden not in serialized


def test_team_pairing_matrix_propagates_source_blockers_without_hiding_other_components() -> None:
    blocked_damage = build_damage_profile_toolkit_result(
        attacks=0,
        hit_target=4,
        wound_target=4,
        save_target=4,
        damage_per_unsaved_wound=2,
        target_wounds_per_model=2,
        target_model_count=3,
    )
    blocked_damage_result = _build_matrix(damage_result=blocked_damage)
    blocked_deployment_result = _build_matrix(
        deployment_results=(
            _deployment_result("alpha-strike"),
            _deployment_result("alpha-strike-2"),
        )
    )

    damage_components = _components_by_id(blocked_damage_result)["damage-output"]
    deployment_components = _components_by_id(blocked_deployment_result)["deployment-staging"]

    assert blocked_damage_result.readiness == "degraded"
    assert damage_components.assessment == "blocked"
    assert damage_components.readiness == "blocked"
    assert any("invalid-attack-count" in reason for reason in damage_components.block_reasons)

    assert blocked_deployment_result.readiness == "degraded"
    assert deployment_components.assessment == "blocked"
    assert deployment_components.readiness == "blocked"
    assert any("invalid-turn-order" in reason for reason in deployment_components.block_reasons)


def _build_matrix(
    *,
    friendly_labels=("Alpha", "Beta"),
    opponent_labels=("Gamma", "Delta"),
    damage_result=None,
    mission_result=None,
    deployment_results=None,
):
    packet = SAMPLE_PACKETS[0]
    return build_team_pairing_matrix_toolkit_result(
        packet=packet,
        friendly_labels=friendly_labels,
        opponent_labels=opponent_labels,
        damage_result=damage_result or _damage_result(),
        mission_result=mission_result or build_mission_pack_toolkit_result(),
        deployment_scorecard_results=deployment_results or _deployment_results(),
    )


def _damage_result():
    return build_damage_profile_toolkit_result(
        attacks=2,
        hit_target=4,
        wound_target=4,
        save_target=4,
        damage_per_unsaved_wound=2,
        target_wounds_per_model=2,
        target_model_count=3,
    )


def _deployment_results():
    return (_deployment_result("going-first"), _deployment_result("going-second"))


def _deployment_result(turn_order: str):
    return build_deployment_scorecard_toolkit_result(
        SAMPLE_PACKETS[0],
        deployment_zone_id="attacker",
        friendly_center=(10.0, 5.0),
        friendly_base_diameter=1.57,
        enemy_source_center=(38.0, 52.0),
        enemy_base_diameter=1.57,
        enemy_move_distance=0.0,
        enemy_threat_range=1.0,
        enemy_threat_mode="raw-range",
        exposure_mode="threat-only",
        turn_order=turn_order,
    )


def _components_by_id(result):
    return {component.component_id: component for component in result.payload.cells[0].components}


def _visible_result_text(result) -> str:
    fragments: list[str] = []
    fragments.extend(entry.label for entry in result.payload.friendly_lists)
    fragments.extend(entry.label for entry in result.payload.opponent_lists)
    fragments.extend(result.payload.warnings)
    fragments.extend(reason.detail for reason in result.block_reasons)
    for scenario in result.payload.scenarios:
        fragments.append(scenario.detail)
    for scenario_range in result.payload.ranges:
        fragments.append(scenario_range.label)
    for cell in result.payload.cells:
        fragments.append(cell.shared_metric_notice)
        for component in cell.components:
            fragments.extend((component.label, component.assessment, component.detail))
            fragments.extend(component.warnings)
            fragments.extend(component.block_reasons)
            fragments.extend(metric.label for metric in component.metrics)
    return " ".join(fragments).lower()
