from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from math import comb, isfinite

from warhammer_companion.application.toolkit import BlockReason, ToolkitResult
from warhammer_companion.domain.damage import (
    DAMAGE_PROFILE_TOOLKIT_SCHEMA_VERSION,
    DamageEstimatePayload,
    DamageEstimateSummary,
    DamageProbabilityRow,
    DamageProfileInput,
    TargetProfileInput,
)
from warhammer_companion.domain.overlays import ToolkitAssumption, ToolkitWarning


def d6_threshold_probability(threshold: int) -> float:
    return float(_d6_threshold_fraction(threshold))


def binomial_distribution(trials: int, probability: float) -> tuple[DamageProbabilityRow, ...]:
    return _binomial_distribution_fraction(trials, Fraction(probability).limit_denominator())


def models_destroyed_for_unsaved_wounds(
    *,
    unsaved_wounds: int,
    damage_per_unsaved_wound: float,
    target_wounds_per_model: int,
    target_model_count: int,
) -> int:
    destroyed = 0
    active_model_damage = 0.0
    for _ in range(unsaved_wounds):
        active_model_damage += damage_per_unsaved_wound
        if active_model_damage >= target_wounds_per_model:
            destroyed += 1
            active_model_damage = 0.0
            if destroyed >= target_model_count:
                return target_model_count
    return destroyed


def build_damage_profile_toolkit_result(
    *,
    attacks: float,
    hit_target: int,
    wound_target: int,
    save_target: int,
    damage_per_unsaved_wound: float,
    target_wounds_per_model: float,
    target_model_count: float,
) -> ToolkitResult[DamageEstimatePayload]:
    input_hash = _damage_profile_hash(
        attacks=attacks,
        hit_target=hit_target,
        wound_target=wound_target,
        save_target=save_target,
        damage_per_unsaved_wound=damage_per_unsaved_wound,
        target_wounds_per_model=target_wounds_per_model,
        target_model_count=target_model_count,
    )
    suffix = input_hash.removeprefix("sha256:")[:12]
    block_reasons = _input_block_reasons(
        attacks=attacks,
        hit_target=hit_target,
        wound_target=wound_target,
        save_target=save_target,
        damage_per_unsaved_wound=damage_per_unsaved_wound,
        target_wounds_per_model=target_wounds_per_model,
        target_model_count=target_model_count,
    )
    profile = DamageProfileInput(
        attacks=attacks,
        hit_target=hit_target,
        wound_target=wound_target,
        save_target=save_target,
        damage_per_unsaved_wound=damage_per_unsaved_wound,
    )
    target = TargetProfileInput(
        wounds_per_model=target_wounds_per_model,
        model_count=target_model_count,
    )
    if block_reasons:
        return ToolkitResult(
            result_id=f"manual:damage-profile:{suffix}",
            tool_id="damage_profile",
            input_hash=input_hash,
            readiness="blocked",
            payload=DamageEstimatePayload(
                profile=profile,
                target=target,
                summary=DamageEstimateSummary(
                    expected_hits=0.0,
                    expected_wounds=0.0,
                    expected_unsaved_wounds=0.0,
                    expected_damage=0.0,
                    expected_models_destroyed=0.0,
                    probability_destroying_at_least_one_model=0.0,
                ),
                unsaved_wound_distribution=(),
                models_destroyed_distribution=(),
            ),
            warnings=(
                ToolkitWarning(
                    warning_id="invalid-manual-damage-profile-input",
                    detail=(
                        "Manual estimate cannot run until manual attack and target inputs "
                        "are valid."
                    ),
                ),
                _manual_boundary_warning(),
            ),
            block_reasons=block_reasons,
        )

    valid_attacks = int(attacks)
    valid_target_wounds = int(target_wounds_per_model)
    valid_target_models = int(target_model_count)
    p_hit = _d6_threshold_fraction(hit_target)
    p_wound = _d6_threshold_fraction(wound_target)
    p_failed_save = 1 - _d6_threshold_fraction(save_target)
    p_unsaved = p_hit * p_wound * p_failed_save
    unsaved_distribution = _binomial_distribution_fraction(valid_attacks, p_unsaved)
    model_distribution = _model_destroyed_distribution(
        unsaved_distribution,
        damage_per_unsaved_wound=damage_per_unsaved_wound,
        target_wounds_per_model=valid_target_wounds,
        target_model_count=valid_target_models,
    )
    summary = DamageEstimateSummary(
        expected_hits=valid_attacks * float(p_hit),
        expected_wounds=valid_attacks * float(p_hit * p_wound),
        expected_unsaved_wounds=valid_attacks * float(p_unsaved),
        expected_damage=valid_attacks * float(p_unsaved) * damage_per_unsaved_wound,
        expected_models_destroyed=sum(row.outcome * row.probability for row in model_distribution),
        probability_destroying_at_least_one_model=sum(
            row.probability for row in model_distribution if row.outcome > 0
        ),
    )
    return ToolkitResult(
        result_id=f"manual:damage-profile:{suffix}",
        tool_id="damage_profile",
        input_hash=input_hash,
        readiness="estimated",
        payload=DamageEstimatePayload(
            profile=profile,
            target=target,
            summary=summary,
            unsaved_wound_distribution=unsaved_distribution,
            models_destroyed_distribution=model_distribution,
        ),
        assumptions=(
            ToolkitAssumption(
                assumption_id="manual-effective-save",
                detail=(
                    "Effective save target is supplied by the user after unmodeled AP, cover, "
                    "or invulnerable choices."
                ),
            ),
            ToolkitAssumption(
                assumption_id="single-manual-profile",
                detail="One fixed attack profile is applied into one homogeneous target profile.",
            ),
            ToolkitAssumption(
                assumption_id="exact-binomial-math",
                detail=(
                    "Expected values and distributions use exact D6/binomial math for "
                    "fixed attacks."
                ),
            ),
        ),
        warnings=(
            _manual_boundary_warning(),
            ToolkitWarning(
                warning_id="unsupported-damage-effects-omitted",
                detail=(
                    "Unsupported effects omitted: rerolls, modifiers, AP, cover, invulnerable "
                    "save selection, random attacks, random damage, mortal wounds, Feel No Pain, "
                    "damage reduction, abilities, stratagems, faction/detachment rules, and "
                    "allocation quirks."
                ),
            ),
        ),
    )


def _input_block_reasons(
    *,
    attacks: float,
    hit_target: int,
    wound_target: int,
    save_target: int,
    damage_per_unsaved_wound: float,
    target_wounds_per_model: float,
    target_model_count: float,
) -> tuple[BlockReason, ...]:
    reasons: list[BlockReason] = []
    if not _is_finite_positive_integer(attacks):
        reasons.append(
            BlockReason(
                "invalid-attack-count",
                "Attack count must be a finite positive integer.",
                remediation="Enter a fixed whole-number attack count of 1 or more.",
            )
        )
    reasons.extend(
        _threshold_block_reason("hit", hit_target),
    )
    reasons.extend(
        _threshold_block_reason("wound", wound_target),
    )
    reasons.extend(
        _threshold_block_reason("save", save_target),
    )
    if not _is_finite_positive_integer(target_wounds_per_model):
        reasons.append(
            BlockReason(
                "invalid-target-wounds-per-model",
                "Target wounds per model must be a finite positive integer.",
                remediation="Enter the target wounds per model as a whole number of 1 or more.",
            )
        )
    if not _is_finite_positive_integer(target_model_count):
        reasons.append(
            BlockReason(
                "invalid-target-model-count",
                "Target model count must be a finite positive integer.",
                remediation="Enter the target model count as a whole number of 1 or more.",
            )
        )
    if not isfinite(damage_per_unsaved_wound) or damage_per_unsaved_wound < 0:
        reasons.append(
            BlockReason(
                "invalid-damage-per-unsaved-wound",
                "Damage per unsaved wound must be a finite non-negative number.",
                remediation="Enter flat damage as zero or a positive number.",
            )
        )
    return tuple(reasons)


def _threshold_block_reason(label: str, threshold: int) -> tuple[BlockReason, ...]:
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, int)
        or threshold < 2
        or threshold > 6
    ):
        return (
            BlockReason(
                f"invalid-{label}-target",
                f"{label.title()} target must be an integer from 2+ through 6+.",
                remediation=f"Enter a {label} threshold from 2 through 6.",
            ),
        )
    return ()


def _d6_threshold_fraction(threshold: int) -> Fraction:
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, int)
        or threshold < 2
        or threshold > 6
    ):
        raise ValueError("D6 threshold must be an integer from 2 through 6.")
    return Fraction(7 - threshold, 6)


def _binomial_distribution_fraction(
    trials: int,
    probability: Fraction,
) -> tuple[DamageProbabilityRow, ...]:
    rows: list[DamageProbabilityRow] = []
    success_numerator = probability.numerator
    denominator = probability.denominator**trials
    failure_numerator = probability.denominator - success_numerator
    for outcome in range(trials + 1):
        numerator = (
            comb(trials, outcome)
            * success_numerator**outcome
            * failure_numerator ** (trials - outcome)
        )
        row_probability = Fraction(numerator, denominator)
        rows.append(
            DamageProbabilityRow(
                outcome=outcome,
                numerator=numerator,
                denominator=denominator,
                probability=float(row_probability),
            )
        )
    return tuple(rows)


def _model_destroyed_distribution(
    unsaved_distribution: tuple[DamageProbabilityRow, ...],
    *,
    damage_per_unsaved_wound: float,
    target_wounds_per_model: int,
    target_model_count: int,
) -> tuple[DamageProbabilityRow, ...]:
    common_denominators = {row.denominator for row in unsaved_distribution}
    if len(common_denominators) == 1:
        denominator = common_denominators.pop()
        grouped_numerators: dict[int, int] = {}
        for row in unsaved_distribution:
            destroyed = models_destroyed_for_unsaved_wounds(
                unsaved_wounds=row.outcome,
                damage_per_unsaved_wound=damage_per_unsaved_wound,
                target_wounds_per_model=target_wounds_per_model,
                target_model_count=target_model_count,
            )
            grouped_numerators[destroyed] = grouped_numerators.get(destroyed, 0) + row.numerator
        return tuple(
            DamageProbabilityRow(
                outcome=outcome,
                numerator=numerator,
                denominator=denominator,
                probability=float(Fraction(numerator, denominator)),
            )
            for outcome, numerator in sorted(grouped_numerators.items())
        )

    grouped: dict[int, Fraction] = {}
    for row in unsaved_distribution:
        destroyed = models_destroyed_for_unsaved_wounds(
            unsaved_wounds=row.outcome,
            damage_per_unsaved_wound=damage_per_unsaved_wound,
            target_wounds_per_model=target_wounds_per_model,
            target_model_count=target_model_count,
        )
        grouped[destroyed] = grouped.get(destroyed, Fraction(0, 1)) + Fraction(
            row.numerator,
            row.denominator,
        )
    return tuple(
        DamageProbabilityRow(
            outcome=outcome,
            numerator=probability.numerator,
            denominator=probability.denominator,
            probability=float(probability),
        )
        for outcome, probability in sorted(grouped.items())
    )


def _damage_profile_hash(
    *,
    attacks: float,
    hit_target: int,
    wound_target: int,
    save_target: int,
    damage_per_unsaved_wound: float,
    target_wounds_per_model: float,
    target_model_count: float,
) -> str:
    payload = {
        "attacks": _canonical_float(attacks),
        "damage_per_unsaved_wound": _canonical_float(damage_per_unsaved_wound),
        "hit_target": hit_target,
        "save_target": save_target,
        "schema_version": DAMAGE_PROFILE_TOOLKIT_SCHEMA_VERSION,
        "target_model_count": _canonical_float(target_model_count),
        "target_wounds_per_model": _canonical_float(target_wounds_per_model),
        "tool_id": "damage_profile",
        "wound_target": wound_target,
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _manual_boundary_warning() -> ToolkitWarning:
    return ToolkitWarning(
        warning_id="manual-damage-estimate-boundary",
        detail=(
            "Manual estimate only; not roster-derived; not official/profile-resolved; effective "
            "save supplied by user; unsupported effects omitted; no source-backed rules/list claim."
        ),
    )


def _is_finite_positive_integer(value: float) -> bool:
    if isinstance(value, bool) or not isfinite(value):
        return False
    return float(value).is_integer() and value >= 1


def _canonical_float(value: float) -> str:
    if isfinite(value):
        return f"{value:.6f}"
    if value != value:
        return "nan"
    if value > 0:
        return "inf"
    return "-inf"
