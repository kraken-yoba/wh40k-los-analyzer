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
from warhammer_companion.application.view_models import HiddenCoverageState
from warhammer_companion.desktop.screens.common import PacketSelectorWidget
from warhammer_companion.desktop.widgets.svg_map import SvgMapWidget


class HiddenCoverageScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.packet_selector = PacketSelectorWidget(service)
        self.terrain_combo = QComboBox()
        self.range_slider = QSlider(Qt.Orientation.Horizontal)
        self.range_slider.setMinimum(12)
        self.range_slider.setMaximum(18)
        self.range_slider.setTickInterval(3)
        self.range_slider.setSingleStep(3)
        self.range_slider.setPageStep(3)
        self.range_slider.setValue(15)
        self.range_label = QLabel("15 in")
        self.generate_button = QPushButton("Generate")
        self.map = SvgMapWidget()

        layout = QVBoxLayout(self)
        title = QLabel("Hidden Coverage")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.packet_selector)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Terrain footprint"))
        controls.addWidget(self.terrain_combo)
        controls.addWidget(QLabel("Detection range"))
        controls.addWidget(self.range_slider)
        controls.addWidget(self.range_label)
        controls.addWidget(self.generate_button)
        layout.addLayout(controls)
        layout.addWidget(self.map, stretch=1)

        self.packet_selector.selection_changed.connect(self.refresh_plain)
        self.range_slider.valueChanged.connect(self._range_changed)
        self.generate_button.clicked.connect(self.generate_coverage)
        self.refresh_plain()

    def refresh_plain(self) -> None:
        state = self.service.viewer_state(self.packet_selector.selected_packet_id())
        self.packet_selector.apply_state(state.packet_selector)
        self._populate_terrain_from_packet(state.packet)
        self.map.set_svg(state.map_svg)

    def generate_coverage(self) -> None:
        state = self.service.hidden_coverage_state(
            packet_id=self.packet_selector.selected_packet_id(),
            terrain_area_id=self._selected_terrain_area_id(),
            detection_range=self.range_slider.value(),
        )
        self.packet_selector.apply_state(state.packet_selector)
        self._populate_terrain(state)
        self.range_slider.setValue(state.selected_detection_range)
        self._range_changed(state.selected_detection_range)
        self.map.set_svg(state.map_svg)

    def _selected_terrain_area_id(self) -> str | None:
        data = self.terrain_combo.currentData()
        return str(data) if data else None

    def _populate_terrain(self, state: HiddenCoverageState) -> None:
        self.terrain_combo.blockSignals(True)
        self.terrain_combo.clear()
        selected_index = 0
        for option in state.terrain_options:
            self.terrain_combo.addItem(option.label, option.id)
            if option.id == state.selected_terrain_area_id:
                selected_index = self.terrain_combo.count() - 1
        if not state.terrain_options:
            self.terrain_combo.addItem("No terrain footprints", "")
        self.terrain_combo.setCurrentIndex(selected_index)
        self.terrain_combo.blockSignals(False)

    def _populate_terrain_from_packet(self, packet) -> None:
        self.terrain_combo.blockSignals(True)
        self.terrain_combo.clear()
        for area in packet.terrain_areas:
            self.terrain_combo.addItem(area.label, area.id)
        if not packet.terrain_areas:
            self.terrain_combo.addItem("No terrain footprints", "")
        self.terrain_combo.setCurrentIndex(0)
        self.terrain_combo.blockSignals(False)

    def _range_changed(self, value: int) -> None:
        snapped = min((12, 15, 18), key=lambda option: (abs(option - value), option))
        self.range_label.setText(f"{snapped} in")
