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
from warhammer_companion.application.view_models import HeatmapState, LosAnalysisState
from warhammer_companion.desktop.screens.common import PacketSelectorWidget, double_spin_box
from warhammer_companion.desktop.widgets.svg_map import SvgMapWidget


class LineOfSightScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.packet_selector = PacketSelectorWidget(service)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("LOS Heatmap", "heatmap")
        self.mode_combo.addItem("LOS Checker", "checker")

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

        self.x_input = double_spin_box(0.0, 44.0, 22.0)
        self.y_input = double_spin_box(0.0, 60.0, 10.0)
        self.base_input = double_spin_box(0.1, 8.0, 1.57)

        self.generate_button = QPushButton("Generate")
        self.check_button = QPushButton("Check LOS")
        self.map = SvgMapWidget()

        layout = QVBoxLayout(self)
        title = QLabel("Line of Sight")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.packet_selector)

        mode_controls = QHBoxLayout()
        mode_controls.addWidget(QLabel("Mode"))
        mode_controls.addWidget(self.mode_combo)
        layout.addLayout(mode_controls)

        self.heatmap_controls = QWidget()
        heatmap_layout = QHBoxLayout(self.heatmap_controls)
        heatmap_layout.setContentsMargins(0, 0, 0, 0)
        heatmap_layout.addWidget(self.zone_combo)
        heatmap_layout.addWidget(self.source_combo)
        heatmap_layout.addWidget(self.offset_slider)
        heatmap_layout.addWidget(self.offset_label)
        heatmap_layout.addWidget(self.generate_button)
        layout.addWidget(self.heatmap_controls)

        self.checker_controls = QWidget()
        checker_layout = QHBoxLayout(self.checker_controls)
        checker_layout.setContentsMargins(0, 0, 0, 0)
        checker_layout.addWidget(QLabel("X"))
        checker_layout.addWidget(self.x_input)
        checker_layout.addWidget(QLabel("Y"))
        checker_layout.addWidget(self.y_input)
        checker_layout.addWidget(QLabel("Base"))
        checker_layout.addWidget(self.base_input)
        checker_layout.addWidget(self.check_button)
        layout.addWidget(self.checker_controls)

        layout.addWidget(self.map, stretch=1)

        self.packet_selector.selection_changed.connect(self.refresh)
        self.mode_combo.currentIndexChanged.connect(self.refresh)
        self.generate_button.clicked.connect(self.refresh)
        self.check_button.clicked.connect(self.refresh)
        self.offset_slider.valueChanged.connect(self._offset_changed)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.los_analysis_state(
            packet_id=self.packet_selector.selected_packet_id(),
            mode=str(self.mode_combo.currentData() or "heatmap"),
            zone_id=str(self.zone_combo.currentData() or "attacker"),
            source=str(self.source_combo.currentData() or "edge"),
            offset_inches=self.offset_slider.value(),
            x=self.x_input.value(),
            y=self.y_input.value(),
            base=self.base_input.value(),
        )
        self.packet_selector.apply_state(state.packet_selector)
        self._populate_mode(state)
        if state.heatmap is not None:
            self._set_heatmap_state(state.heatmap)
        if state.checker is not None:
            self.x_input.setValue(state.checker.x)
            self.y_input.setValue(state.checker.y)
            self.base_input.setValue(state.checker.base)
        self.heatmap_controls.setVisible(state.mode == "heatmap")
        self.checker_controls.setVisible(state.mode == "checker")
        self.map.set_svg(state.map_svg)

    def _populate_mode(self, state: LosAnalysisState) -> None:
        self.mode_combo.blockSignals(True)
        selected_index = self.mode_combo.findData(state.mode)
        self.mode_combo.setCurrentIndex(max(selected_index, 0))
        self.mode_combo.blockSignals(False)

    def _set_heatmap_state(self, state: HeatmapState) -> None:
        self._populate_zones(state)
        self._populate_source(state.selected_source)
        self.offset_slider.blockSignals(True)
        self.offset_slider.setValue(state.selected_offset_inches)
        self.offset_slider.blockSignals(False)
        self._offset_changed(state.selected_offset_inches)

    def _populate_zones(self, state: HeatmapState) -> None:
        self.zone_combo.blockSignals(True)
        self.zone_combo.clear()
        selected_index = 0
        for zone in state.packet.deployment_zones:
            self.zone_combo.addItem(zone.label, zone.id)
            if zone.id == state.selected_zone_id:
                selected_index = self.zone_combo.count() - 1
        self.zone_combo.setCurrentIndex(selected_index)
        self.zone_combo.blockSignals(False)

    def _populate_source(self, selected_source: str) -> None:
        self.source_combo.blockSignals(True)
        selected_index = self.source_combo.findData(selected_source)
        self.source_combo.setCurrentIndex(max(selected_index, 0))
        self.source_combo.blockSignals(False)

    def _offset_changed(self, value: int) -> None:
        self.offset_label.setText(f"{value} in")
