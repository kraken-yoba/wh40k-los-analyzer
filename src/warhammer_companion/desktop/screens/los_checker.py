from __future__ import annotations

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.desktop.screens.common import PacketSelectorWidget, double_spin_box
from warhammer_companion.desktop.widgets.svg_map import SvgMapWidget


class LosCheckerScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.packet_selector = PacketSelectorWidget(service)
        self.x_input = double_spin_box(0.0, 44.0, 22.0)
        self.y_input = double_spin_box(0.0, 60.0, 10.0)
        self.base_input = double_spin_box(0.1, 8.0, 1.57)
        self.check_button = QPushButton("Check LOS")
        self.map = SvgMapWidget()

        layout = QVBoxLayout(self)
        title = QLabel("LOS Checker")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.packet_selector)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("X"))
        controls.addWidget(self.x_input)
        controls.addWidget(QLabel("Y"))
        controls.addWidget(self.y_input)
        controls.addWidget(QLabel("Base"))
        controls.addWidget(self.base_input)
        controls.addWidget(self.check_button)
        layout.addLayout(controls)
        layout.addWidget(self.map, stretch=1)

        self.packet_selector.selection_changed.connect(self.refresh)
        self.check_button.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.los_checker_state(
            packet_id=self.packet_selector.selected_packet_id(),
            x=self.x_input.value(),
            y=self.y_input.value(),
            base=self.base_input.value(),
        )
        self.packet_selector.apply_state(state.packet_selector)
        self.x_input.setValue(state.x)
        self.y_input.setValue(state.y)
        self.map.set_svg(state.map_svg)
