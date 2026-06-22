from __future__ import annotations

from math import inf, nan

import pytest

from warhammer_companion.application.damage_profile import (
    build_damage_profile_toolkit_result,
    d6_threshold_probability,
    models_destroyed_for_unsaved_wounds,
)


def test_d6_threshold_probability_uses_exact_roll_targets() -> None:
    assert d6_threshold_probability(2) == pytest.approx(5 / 6)
    assert d6_threshold_probability(4) == pytest.approx(1 / 2)
    assert d6_threshold_probability(6) == pytest.approx(1 / 6)


def test_damage_profile_estimates_expected_damage_and_destroyed_models() -> None:
    result = build_damage_profile_toolkit_result(
        attacks=2,
        hit_target=4,
        wound_target=4,
        save_target=4,
        damage_per_unsaved_wound=2,
        target_wounds_per_model=2,
        target_model_count=3,
    )

    assert result.tool_id == "damage_profile"
    assert result.readiness == "estimated"
    assert not result.overlays
    assert not result.source_ref_ids
    assert not result.allows_recommendation_language()
    summary = result.payload.summary
    assert summary.expected_hits == pytest.approx(1.0)
    assert summary.expected_wounds == pytest.approx(0.5)
    assert summary.expected_unsaved_wounds == pytest.approx(0.25)
    assert summary.expected_damage == pytest.approx(0.5)
    assert summary.expected_models_destroyed == pytest.approx(0.25)
    assert summary.probability_destroying_at_least_one_model == pytest.approx(15 / 64)
    assert [
        (row.outcome, row.numerator, row.denominator)
        for row in result.payload.unsaved_wound_distribution
    ] == [
        (0, 49, 64),
        (1, 14, 64),
        (2, 1, 64),
    ]
    assert [
        (row.outcome, row.numerator, row.denominator)
        for row in result.payload.models_destroyed_distribution
    ] == [
        (0, 49, 64),
        (1, 14, 64),
        (2, 1, 64),
    ]


def test_damage_profile_model_destroyed_count_accumulates_without_spillover() -> None:
    assert (
        models_destroyed_for_unsaved_wounds(
            unsaved_wounds=3,
            damage_per_unsaved_wound=3,
            target_wounds_per_model=5,
            target_model_count=3,
        )
        == 1
    )
    assert (
        models_destroyed_for_unsaved_wounds(
            unsaved_wounds=2,
            damage_per_unsaved_wound=6,
            target_wounds_per_model=5,
            target_model_count=3,
        )
        == 2
    )


def test_damage_profile_fractional_damage_below_threshold_does_not_destroy_model() -> None:
    assert (
        models_destroyed_for_unsaved_wounds(
            unsaved_wounds=3,
            damage_per_unsaved_wound=0.333333333,
            target_wounds_per_model=1,
            target_model_count=1,
        )
        == 0
    )


@pytest.mark.parametrize(
    ("overrides", "expected_reason_id"),
    [
        ({"attacks": 0}, "invalid-attack-count"),
        ({"attacks": -1}, "invalid-attack-count"),
        ({"attacks": 1.5}, "invalid-attack-count"),
        ({"attacks": inf}, "invalid-attack-count"),
        ({"hit_target": 1}, "invalid-hit-target"),
        ({"wound_target": 7}, "invalid-wound-target"),
        ({"save_target": 1}, "invalid-save-target"),
        ({"target_wounds_per_model": 0}, "invalid-target-wounds-per-model"),
        ({"target_wounds_per_model": 1.5}, "invalid-target-wounds-per-model"),
        ({"target_wounds_per_model": nan}, "invalid-target-wounds-per-model"),
        ({"target_model_count": 0}, "invalid-target-model-count"),
        ({"target_model_count": 2.5}, "invalid-target-model-count"),
        ({"target_model_count": inf}, "invalid-target-model-count"),
        ({"damage_per_unsaved_wound": -1}, "invalid-damage-per-unsaved-wound"),
        ({"damage_per_unsaved_wound": nan}, "invalid-damage-per-unsaved-wound"),
    ],
)
def test_damage_profile_blocks_invalid_manual_inputs(
    overrides: dict[str, float],
    expected_reason_id: str,
) -> None:
    params = {
        "attacks": 2,
        "hit_target": 4,
        "wound_target": 4,
        "save_target": 4,
        "damage_per_unsaved_wound": 2,
        "target_wounds_per_model": 2,
        "target_model_count": 3,
    }
    params.update(overrides)

    result = build_damage_profile_toolkit_result(**params)

    assert result.readiness == "blocked"
    assert not result.overlays
    assert expected_reason_id in {reason.reason_id for reason in result.block_reasons}


def test_damage_profile_identity_includes_manual_inputs() -> None:
    base = build_damage_profile_toolkit_result(
        attacks=2,
        hit_target=4,
        wound_target=4,
        save_target=4,
        damage_per_unsaved_wound=2,
        target_wounds_per_model=2,
        target_model_count=3,
    )
    changed = build_damage_profile_toolkit_result(
        attacks=3,
        hit_target=4,
        wound_target=4,
        save_target=4,
        damage_per_unsaved_wound=2,
        target_wounds_per_model=2,
        target_model_count=3,
    )

    suffix = base.input_hash.removeprefix("sha256:")[:12]
    assert base.input_hash != changed.input_hash
    assert base.result_id.endswith(suffix)


def test_damage_profile_warning_text_keeps_manual_estimate_boundaries() -> None:
    result = build_damage_profile_toolkit_result(
        attacks=2,
        hit_target=4,
        wound_target=4,
        save_target=4,
        damage_per_unsaved_wound=2,
        target_wounds_per_model=2,
        target_model_count=3,
    )

    normalized = " ".join(warning.detail for warning in result.warnings).lower()
    assert "manual estimate" in normalized
    assert "not roster-derived" in normalized
    assert "not official/profile-resolved" in normalized
    assert "effective save supplied by user" in normalized
    assert "unsupported effects omitted" in normalized
    assert "no source-backed rules/list claim" in normalized
    normalized_without_negative_claim = normalized.replace("not official/profile-resolved", "")
    for forbidden in (
        "legal",
        "optimal",
        "recommended",
        "likely",
        "target priority",
        "bad target",
        "official",
        "profile-resolved",
    ):
        assert forbidden not in normalized_without_negative_claim
