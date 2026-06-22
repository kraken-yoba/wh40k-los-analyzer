from __future__ import annotations

from dataclasses import dataclass

DAMAGE_PROFILE_TOOLKIT_SCHEMA_VERSION = "damage-profile-toolkit/v0"


@dataclass(frozen=True, slots=True)
class DamageProfileInput:
    attacks: float
    hit_target: int
    wound_target: int
    save_target: int
    damage_per_unsaved_wound: float


@dataclass(frozen=True, slots=True)
class TargetProfileInput:
    wounds_per_model: float
    model_count: float


DEFAULT_DAMAGE_PROFILE_INPUT = DamageProfileInput(
    attacks=2.0,
    hit_target=4,
    wound_target=4,
    save_target=4,
    damage_per_unsaved_wound=2.0,
)
DEFAULT_TARGET_PROFILE_INPUT = TargetProfileInput(
    wounds_per_model=2.0,
    model_count=3.0,
)


@dataclass(frozen=True, slots=True)
class DamageProbabilityRow:
    outcome: int
    numerator: int
    denominator: int
    probability: float


@dataclass(frozen=True, slots=True)
class DamageEstimateSummary:
    expected_hits: float
    expected_wounds: float
    expected_unsaved_wounds: float
    expected_damage: float
    expected_models_destroyed: float
    probability_destroying_at_least_one_model: float


@dataclass(frozen=True, slots=True)
class DamageEstimatePayload:
    profile: DamageProfileInput
    target: TargetProfileInput
    summary: DamageEstimateSummary
    unsaved_wound_distribution: tuple[DamageProbabilityRow, ...]
    models_destroyed_distribution: tuple[DamageProbabilityRow, ...]
