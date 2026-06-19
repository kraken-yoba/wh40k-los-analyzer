from __future__ import annotations

from PySide6.QtCore import Qt  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.desktop.screens.common import populate_packet_combo, selected_packet_id
from warhammer_companion.desktop.widgets.svg_map import SvgMapWidget


class HeatmapScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.packet_combo = QComboBox()
        self.zone_combo = QComboBox()
        self.source_combo = QComboBox()
        self.source_combo.addItem("Deployment edge", "edge")
        self.source_combo.addItem("Full deployment zone", "interior")
        self.offset_slider = QSlider(Qt.Orientation.Horizontal)
        self.offset_slider.setMinimum(0)
        self.offset_slider.setMaximum(12)
        self.offset_slider.setTickInterval(1)
        self.offset_slider.setSingleStep(1)
        self.offset_label = QLabel("0 in")
        self.generate_button = QPushButton("Generate")
        self.map = SvgMapWidget()

        layout = QVBoxLayout(self)
        title = QLabel("LOS Heatmap")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.packet_combo)
        controls = QHBoxLayout()
        controls.addWidget(self.zone_combo)
        controls.addWidget(self.source_combo)
        controls.addWidget(self.offset_slider)
        controls.addWidget(self.offset_label)
        controls.addWidget(self.generate_button)
        layout.addLayout(controls)
        layout.addWidget(self.map, stretch=1)

        self.packet_combo.currentIndexChanged.connect(self.refresh)
        self.generate_button.clicked.connect(self.refresh)
        self.offset_slider.valueChanged.connect(self._offset_changed)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.heatmap_state(
            packet_id=selected_packet_id(self.packet_combo),
            zone_id=self.zone_combo.currentData() or "attacker",
            source=self.source_combo.currentData() or "edge",
            offset_inches=self.offset_slider.value(),
        )
        populate_packet_combo(self.packet_combo, state.packet_groups, state.packet.id)
        self._populate_zones(state.selected_zone_id)
        self.offset_slider.setValue(state.selected_offset_inches)
        self._offset_changed(state.selected_offset_inches)
        self.map.set_svg(state.map_svg)

    def _populate_zones(self, selected_zone_id: str) -> None:
        packet_id = selected_packet_id(self.packet_combo)
        state = self.service.viewer_state(packet_id)
        self.zone_combo.blockSignals(True)
        self.zone_combo.clear()
        selected_index = 0
        for zone in state.packet.deployment_zones:
            self.zone_combo.addItem(zone.label, zone.id)
            if zone.id == selected_zone_id:
                selected_index = self.zone_combo.count() - 1
        self.zone_combo.setCurrentIndex(selected_index)
        self.zone_combo.blockSignals(False)

    def _offset_changed(self, value: int) -> None:
        self.offset_label.setText(f"{value} in")
