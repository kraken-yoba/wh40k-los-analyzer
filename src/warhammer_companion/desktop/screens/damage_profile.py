from __future__ import annotations

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.application.view_models import DamageProfileState
from warhammer_companion.desktop.screens.common import double_spin_box
from warhammer_companion.domain.damage import (
    DEFAULT_DAMAGE_PROFILE_INPUT,
    DEFAULT_TARGET_PROFILE_INPUT,
)


class DamageProfileScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.attacks_input = _integer_spin_box(1, 120, int(DEFAULT_DAMAGE_PROFILE_INPUT.attacks))
        self.hit_input = _integer_spin_box(2, 6, DEFAULT_DAMAGE_PROFILE_INPUT.hit_target)
        self.wound_input = _integer_spin_box(2, 6, DEFAULT_DAMAGE_PROFILE_INPUT.wound_target)
        self.save_input = _integer_spin_box(2, 6, DEFAULT_DAMAGE_PROFILE_INPUT.save_target)
        self.damage_input = double_spin_box(
            0.0,
            100.0,
            DEFAULT_DAMAGE_PROFILE_INPUT.damage_per_unsaved_wound,
        )
        self.wounds_input = _integer_spin_box(
            1,
            100,
            int(DEFAULT_TARGET_PROFILE_INPUT.wounds_per_model),
        )
        self.models_input = _integer_spin_box(
            1,
            120,
            int(DEFAULT_TARGET_PROFILE_INPUT.model_count),
        )
        self.generate_button = QPushButton("Generate")
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        title = QLabel("Damage Profile")
        title.setObjectName("screenTitle")
        layout.addWidget(title)

        controls = QGridLayout()
        controls.addWidget(QLabel("Attacks"), 0, 0)
        controls.addWidget(self.attacks_input, 1, 0)
        controls.addWidget(QLabel("Hit target"), 0, 1)
        controls.addWidget(self.hit_input, 1, 1)
        controls.addWidget(QLabel("Wound target"), 0, 2)
        controls.addWidget(self.wound_input, 1, 2)
        controls.addWidget(QLabel("Effective save"), 0, 3)
        controls.addWidget(self.save_input, 1, 3)
        controls.addWidget(QLabel("Damage"), 2, 0)
        controls.addWidget(self.damage_input, 3, 0)
        controls.addWidget(QLabel("Wounds/model"), 2, 1)
        controls.addWidget(self.wounds_input, 3, 1)
        controls.addWidget(QLabel("Models"), 2, 2)
        controls.addWidget(self.models_input, 3, 2)
        controls.addWidget(self.generate_button, 3, 3)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addStretch(1)

        self.generate_button.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.damage_profile_state(
            attacks=self.attacks_input.value(),
            hit=int(self.hit_input.value()),
            wound=int(self.wound_input.value()),
            save=int(self.save_input.value()),
            damage=self.damage_input.value(),
            wounds=self.wounds_input.value(),
            models=self.models_input.value(),
        )
        self._apply_inputs(state)
        self._set_status(state)

    def _apply_inputs(self, state: DamageProfileState) -> None:
        self.attacks_input.setValue(state.attacks)
        self.hit_input.setValue(state.hit_target)
        self.wound_input.setValue(state.wound_target)
        self.save_input.setValue(state.save_target)
        self.damage_input.setValue(state.damage_per_unsaved_wound)
        self.wounds_input.setValue(state.target_wounds_per_model)
        self.models_input.setValue(state.target_model_count)

    def _set_status(self, state: DamageProfileState) -> None:
        warnings = " ".join(state.warning_details)
        if state.is_blocked:
            reasons = " ".join(state.block_reason_details)
            self.status_label.setText(f"Manual estimate blocked. {reasons} {warnings}")
            return
        self.status_label.setText(
            "Manual estimate. "
            f"Expected hits: {state.expected_hits:.2f}. "
            f"Expected wounds: {state.expected_wounds:.2f}. "
            f"Expected unsaved wounds: {state.expected_unsaved_wounds:.2f}. "
            f"Expected damage: {state.expected_damage:.2f}. "
            f"Expected models destroyed: {state.expected_models_destroyed:.2f}. "
            f"At least one model destroyed: "
            f"{state.probability_destroying_at_least_one_model * 100.0:.1f}%. "
            f"{warnings}"
        )


def _integer_spin_box(minimum: int, maximum: int, value: int):
    spin_box = double_spin_box(float(minimum), float(maximum), float(value))
    spin_box.setDecimals(0)
    spin_box.setSingleStep(1)
    return spin_box
