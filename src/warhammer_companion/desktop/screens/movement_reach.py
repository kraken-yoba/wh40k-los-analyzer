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
from warhammer_companion.application.view_models import MovementReachState
from warhammer_companion.desktop.screens.common import PacketSelectorWidget, double_spin_box
from warhammer_companion.desktop.widgets.svg_map import SvgMapWidget


class MovementReachScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.packet_selector = PacketSelectorWidget(service)
        self.start_x_input = double_spin_box(0.0, 44.0, 16.0)
        self.start_y_input = double_spin_box(0.0, 60.0, 10.0)
        self.target_x_input = double_spin_box(0.0, 44.0, 22.0)
        self.target_y_input = double_spin_box(0.0, 60.0, 10.0)
        self.base_input = double_spin_box(0.1, 8.0, 1.57)
        self.move_input = double_spin_box(0.1, 30.0, 6.0)
        self.mode_combo = QComboBox()
        self.generate_button = QPushButton("Generate")
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.map = SvgMapWidget()

        layout = QVBoxLayout(self)
        title = QLabel("Movement Reach")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.packet_selector)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Start X"))
        controls.addWidget(self.start_x_input)
        controls.addWidget(QLabel("Start Y"))
        controls.addWidget(self.start_y_input)
        controls.addWidget(QLabel("Target X"))
        controls.addWidget(self.target_x_input)
        controls.addWidget(QLabel("Target Y"))
        controls.addWidget(self.target_y_input)
        controls.addWidget(QLabel("Base"))
        controls.addWidget(self.base_input)
        controls.addWidget(QLabel("Move"))
        controls.addWidget(self.move_input)
        controls.addWidget(QLabel("Mode"))
        controls.addWidget(self.mode_combo)
        controls.addWidget(self.generate_button)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addWidget(self.map, stretch=1)

        self.packet_selector.selection_changed.connect(self.refresh)
        self.generate_button.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.movement_reach_state(
            packet_id=self.packet_selector.selected_packet_id(),
            start_x=self.start_x_input.value(),
            start_y=self.start_y_input.value(),
            target_x=self.target_x_input.value(),
            target_y=self.target_y_input.value(),
            base=self.base_input.value(),
            move=self.move_input.value(),
            mode=str(self.mode_combo.currentData() or "normal"),
        )
        self.packet_selector.apply_state(state.packet_selector)
        self._apply_inputs(state)
        self._populate_mode(state)
        self._set_status(state)
        self.map.set_svg(state.map_svg)

    def _apply_inputs(self, state: MovementReachState) -> None:
        self.start_x_input.setValue(state.start_x)
        self.start_y_input.setValue(state.start_y)
        self.target_x_input.setValue(state.target_x)
        self.target_y_input.setValue(state.target_y)
        self.base_input.setValue(state.base)
        self.move_input.setValue(state.move)

    def _populate_mode(self, state: MovementReachState) -> None:
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        selected_index = 0
        for mode in state.movement_modes:
            self.mode_combo.addItem(mode, mode)
            if mode == state.mode:
                selected_index = self.mode_combo.count() - 1
        self.mode_combo.setCurrentIndex(selected_index)
        self.mode_combo.blockSignals(False)

    def _set_status(self, state: MovementReachState) -> None:
        if state.endpoint_estimated_reachable:
            self.status_label.setText("Endpoint diagnostic: no straight-corridor blocker found.")
            return
        detail = "; ".join(state.endpoint_reason_details) or "Manual inputs need adjustment."
        self.status_label.setText(f"Endpoint diagnostic: {detail}")
