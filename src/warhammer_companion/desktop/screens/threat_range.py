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
from warhammer_companion.application.view_models import ThreatRangeState
from warhammer_companion.desktop.screens.common import PacketSelectorWidget, double_spin_box
from warhammer_companion.desktop.widgets.svg_map import SvgMapWidget


class ThreatRangeScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.packet_selector = PacketSelectorWidget(service)
        self.source_mode_combo = QComboBox()
        self.source_deployment_zone_combo = QComboBox()
        self.source_zone_label = QLabel("Zone")
        self.source_x_label = QLabel("Source X")
        self.source_x_input = double_spin_box(0.0, 44.0, 16.0)
        self.source_y_label = QLabel("Source Y")
        self.source_y_input = double_spin_box(0.0, 60.0, 10.0)
        self.target_x_input = double_spin_box(0.0, 44.0, 24.0)
        self.target_y_input = double_spin_box(0.0, 60.0, 10.0)
        self.base_input = double_spin_box(0.1, 8.0, 1.57)
        self.move_input = double_spin_box(0.0, 30.0, 6.0)
        self.threat_input = double_spin_box(0.0, 30.0, 2.0)
        self.mode_combo = QComboBox()
        self.profile_combo = QComboBox()
        self.generate_button = QPushButton("Generate")
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.map = SvgMapWidget()

        layout = QVBoxLayout(self)
        title = QLabel("Threat Range")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.packet_selector)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Source"))
        controls.addWidget(self.source_mode_combo)
        controls.addWidget(self.source_zone_label)
        controls.addWidget(self.source_deployment_zone_combo)
        controls.addWidget(self.source_x_label)
        controls.addWidget(self.source_x_input)
        controls.addWidget(self.source_y_label)
        controls.addWidget(self.source_y_input)
        controls.addWidget(QLabel("Target X"))
        controls.addWidget(self.target_x_input)
        controls.addWidget(QLabel("Target Y"))
        controls.addWidget(self.target_y_input)
        controls.addWidget(QLabel("Base"))
        controls.addWidget(self.base_input)
        controls.addWidget(QLabel("Move"))
        controls.addWidget(self.move_input)
        controls.addWidget(QLabel("Threat"))
        controls.addWidget(self.threat_input)
        controls.addWidget(QLabel("Mode"))
        controls.addWidget(self.mode_combo)
        controls.addWidget(QLabel("Profile"))
        controls.addWidget(self.profile_combo)
        controls.addWidget(self.generate_button)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addWidget(self.map, stretch=1)

        self.packet_selector.selection_changed.connect(self.refresh)
        self.source_mode_combo.currentIndexChanged.connect(self._update_source_control_visibility)
        self.generate_button.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.threat_range_state(
            packet_id=self.packet_selector.selected_packet_id(),
            source_x=self.source_x_input.value(),
            source_y=self.source_y_input.value(),
            target_x=self.target_x_input.value(),
            target_y=self.target_y_input.value(),
            base=self.base_input.value(),
            move=self.move_input.value(),
            threat=self.threat_input.value(),
            mode=str(self.mode_combo.currentData() or "fixed-move-plus-range"),
            movement_profile=str(self.profile_combo.currentData() or "ground-non-mobile"),
            source_mode=str(self.source_mode_combo.currentData() or "point"),
            source_deployment_zone_id=str(
                self.source_deployment_zone_combo.currentData() or "attacker"
            ),
        )
        self.packet_selector.apply_state(state.packet_selector)
        self._apply_inputs(state)
        self._populate_source_mode(state)
        self._populate_source_deployment_zone(state)
        self._populate_mode(state)
        self._populate_profile(state)
        self._set_status(state)
        self.map.set_svg(state.map_svg)

    def _apply_inputs(self, state: ThreatRangeState) -> None:
        self.source_x_input.setValue(state.source_x)
        self.source_y_input.setValue(state.source_y)
        self.target_x_input.setValue(state.target_x)
        self.target_y_input.setValue(state.target_y)
        self.base_input.setValue(state.base)
        self.move_input.setValue(state.move)
        self.threat_input.setValue(state.threat)

    def _populate_mode(self, state: ThreatRangeState) -> None:
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        selected_index = 0
        for mode in state.threat_modes:
            self.mode_combo.addItem(mode, mode)
            if mode == state.mode:
                selected_index = self.mode_combo.count() - 1
        self.mode_combo.setCurrentIndex(selected_index)
        self.mode_combo.blockSignals(False)

    def _populate_source_mode(self, state: ThreatRangeState) -> None:
        self.source_mode_combo.blockSignals(True)
        self.source_mode_combo.clear()
        selected_index = 0
        for mode in state.source_modes:
            label = "Deployment zone" if mode == "deployment-zone" else "Point"
            self.source_mode_combo.addItem(label, mode)
            if mode == state.source_mode:
                selected_index = self.source_mode_combo.count() - 1
        self.source_mode_combo.setCurrentIndex(selected_index)
        self.source_mode_combo.blockSignals(False)
        self._update_source_control_visibility()

    def _populate_source_deployment_zone(self, state: ThreatRangeState) -> None:
        self.source_deployment_zone_combo.blockSignals(True)
        self.source_deployment_zone_combo.clear()
        selected_index = 0
        for option in state.source_deployment_zone_options:
            self.source_deployment_zone_combo.addItem(option.label, option.id)
            if option.id == state.source_deployment_zone_id:
                selected_index = self.source_deployment_zone_combo.count() - 1
        self.source_deployment_zone_combo.setCurrentIndex(selected_index)
        self.source_deployment_zone_combo.blockSignals(False)

    def _update_source_control_visibility(self) -> None:
        uses_deployment_zone = self.source_mode_combo.currentData() == "deployment-zone"
        for widget in (self.source_zone_label, self.source_deployment_zone_combo):
            widget.setVisible(uses_deployment_zone)
        for widget in (
            self.source_x_label,
            self.source_x_input,
            self.source_y_label,
            self.source_y_input,
        ):
            widget.setVisible(not uses_deployment_zone)

    def _populate_profile(self, state: ThreatRangeState) -> None:
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        selected_index = 0
        for profile in state.movement_profiles:
            self.profile_combo.addItem(profile.label, profile.profile_id)
            if profile.profile_id == state.movement_profile:
                selected_index = self.profile_combo.count() - 1
        self.profile_combo.setCurrentIndex(selected_index)
        self.profile_combo.blockSignals(False)

    def _set_status(self, state: ThreatRangeState) -> None:
        probability = state.target_probability * 100.0
        measurement = state.measurement_convention.replace("-", " ")
        warnings = " ".join(state.warning_details)
        self.status_label.setText(
            f"Source: {state.source_label}. "
            f"Profile: {state.movement_profile_label}. "
            f"Effective movement: {state.effective_move:.2f} in. "
            f"Target point probability: {probability:.1f}%. "
            f"Measurement: {measurement}. {warnings}"
        )
