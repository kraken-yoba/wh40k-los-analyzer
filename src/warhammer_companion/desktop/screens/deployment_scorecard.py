from __future__ import annotations

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.application.view_models import DeploymentScorecardState
from warhammer_companion.desktop.screens.common import PacketSelectorWidget, double_spin_box
from warhammer_companion.desktop.widgets.svg_map import SvgMapWidget


class DeploymentScorecardScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.packet_selector = PacketSelectorWidget(service)
        self.deployment_zone_combo = QComboBox()
        self.friendly_x_input = double_spin_box(0.0, 44.0, 19.24)
        self.friendly_y_input = double_spin_box(0.0, 60.0, 51.48)
        self.friendly_base_input = double_spin_box(0.1, 8.0, 1.57)
        self.enemy_x_input = double_spin_box(0.0, 44.0, 24.77)
        self.enemy_y_input = double_spin_box(0.0, 60.0, 8.46)
        self.enemy_base_input = double_spin_box(0.1, 8.0, 1.57)
        self.enemy_move_input = double_spin_box(0.0, 30.0, 0.0)
        self.enemy_threat_input = double_spin_box(0.0, 30.0, 1.0)
        self.enemy_mode_combo = QComboBox()
        self.enemy_profile_combo = QComboBox()
        self.exposure_mode_combo = QComboBox()
        self.turn_order_combo = QComboBox()
        self.generate_button = QPushButton("Generate")
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.component_list_label = QLabel("")
        self.component_list_label.setWordWrap(True)
        self.map = SvgMapWidget()

        layout = QVBoxLayout(self)
        title = QLabel("Deployment Scorecard")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.packet_selector)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Zone"))
        controls.addWidget(self.deployment_zone_combo)
        controls.addWidget(QLabel("Friendly X"))
        controls.addWidget(self.friendly_x_input)
        controls.addWidget(QLabel("Friendly Y"))
        controls.addWidget(self.friendly_y_input)
        controls.addWidget(QLabel("Friendly base"))
        controls.addWidget(self.friendly_base_input)
        controls.addWidget(QLabel("Enemy X"))
        controls.addWidget(self.enemy_x_input)
        controls.addWidget(QLabel("Enemy Y"))
        controls.addWidget(self.enemy_y_input)
        controls.addWidget(QLabel("Enemy base"))
        controls.addWidget(self.enemy_base_input)
        controls.addWidget(QLabel("Enemy move"))
        controls.addWidget(self.enemy_move_input)
        controls.addWidget(QLabel("Enemy threat"))
        controls.addWidget(self.enemy_threat_input)
        controls.addWidget(QLabel("Enemy mode"))
        controls.addWidget(self.enemy_mode_combo)
        controls.addWidget(QLabel("Enemy profile"))
        controls.addWidget(self.enemy_profile_combo)
        controls.addWidget(QLabel("Exposure"))
        controls.addWidget(self.exposure_mode_combo)
        controls.addWidget(QLabel("Turn order"))
        controls.addWidget(self.turn_order_combo)
        controls.addWidget(self.generate_button)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addWidget(self.component_list_label)
        layout.addWidget(self.map, stretch=1)

        self.packet_selector.selection_changed.connect(self.refresh)
        self.generate_button.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.deployment_scorecard_state(
            packet_id=self.packet_selector.selected_packet_id(),
            deployment_zone_id=str(self.deployment_zone_combo.currentData() or "attacker"),
            friendly_x=self.friendly_x_input.value(),
            friendly_y=self.friendly_y_input.value(),
            friendly_base=self.friendly_base_input.value(),
            enemy_x=self.enemy_x_input.value(),
            enemy_y=self.enemy_y_input.value(),
            enemy_base=self.enemy_base_input.value(),
            enemy_move=self.enemy_move_input.value(),
            enemy_threat=self.enemy_threat_input.value(),
            enemy_mode=str(self.enemy_mode_combo.currentData() or "raw-range"),
            enemy_movement_profile=str(
                self.enemy_profile_combo.currentData() or "ground-non-mobile"
            ),
            exposure_mode=str(self.exposure_mode_combo.currentData() or "threat-and-los"),
            turn_order=str(self.turn_order_combo.currentData() or "going-first"),
        )
        self._set_state(state)

    def _set_state(self, state: DeploymentScorecardState) -> None:
        self.packet_selector.apply_state(state.packet_selector)
        self._apply_inputs(state)
        self._populate_deployment_zones(state)
        self._populate_modes(state)
        self._set_status(state)
        self.map.set_svg(state.map_svg)

    def _apply_inputs(self, state: DeploymentScorecardState) -> None:
        self.friendly_x_input.setValue(state.friendly_x)
        self.friendly_y_input.setValue(state.friendly_y)
        self.friendly_base_input.setValue(state.friendly_base)
        self.enemy_x_input.setValue(state.enemy_x)
        self.enemy_y_input.setValue(state.enemy_y)
        self.enemy_base_input.setValue(state.enemy_base)
        self.enemy_move_input.setValue(state.enemy_move)
        self.enemy_threat_input.setValue(state.enemy_threat)

    def _populate_deployment_zones(self, state: DeploymentScorecardState) -> None:
        self.deployment_zone_combo.blockSignals(True)
        self.deployment_zone_combo.clear()
        selected_index = 0
        for option in state.deployment_zone_options:
            self.deployment_zone_combo.addItem(option.label, option.id)
            if option.id == state.deployment_zone_id:
                selected_index = self.deployment_zone_combo.count() - 1
        self.deployment_zone_combo.setCurrentIndex(selected_index)
        self.deployment_zone_combo.blockSignals(False)

    def _populate_modes(self, state: DeploymentScorecardState) -> None:
        self._populate_combo(self.enemy_mode_combo, state.enemy_threat_modes, state.enemy_mode)
        self.enemy_profile_combo.blockSignals(True)
        self.enemy_profile_combo.clear()
        selected_index = 0
        for profile in state.enemy_movement_profiles:
            self.enemy_profile_combo.addItem(profile.label, profile.profile_id)
            if profile.profile_id == state.enemy_movement_profile:
                selected_index = self.enemy_profile_combo.count() - 1
        self.enemy_profile_combo.setCurrentIndex(selected_index)
        self.enemy_profile_combo.blockSignals(False)
        self._populate_combo(self.exposure_mode_combo, state.exposure_modes, state.exposure_mode)
        self._populate_combo(self.turn_order_combo, state.turn_order_options, state.turn_order)

    def _set_status(self, state: DeploymentScorecardState) -> None:
        warnings = " ".join(state.warning_details)
        blockers = " ".join(state.block_reason_details)
        self.status_label.setText(
            f"Enemy profile: {state.enemy_movement_profile_label}. "
            f"Enemy effective movement: {state.enemy_effective_move:.2f} in. "
            f"Readiness: {state.readiness}. Turn order: {state.turn_order}. "
            f"Threat probability at center: {state.threat_probability_at_center * 100.0:.1f}%. "
            f"{warnings} {blockers}"
        )
        self.component_list_label.setText(
            "\n".join(
                f"{component.label} [{component.assessment}]: {component.detail}"
                for component in state.components
            )
        )

    @staticmethod
    def _populate_combo(combo: QComboBox, options: list[str], selected: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        selected_index = 0
        for option in options:
            combo.addItem(option, option)
            if option == selected:
                selected_index = combo.count() - 1
        if selected not in options:
            combo.addItem(selected, selected)
            selected_index = combo.count() - 1
        combo.setCurrentIndex(selected_index)
        combo.blockSignals(False)
