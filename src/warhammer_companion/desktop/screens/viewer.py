from __future__ import annotations

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QComboBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.desktop.screens.common import populate_packet_combo, selected_packet_id
from warhammer_companion.desktop.widgets.svg_map import SvgMapWidget


class ViewerScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.packet_combo = QComboBox()
        self.summary = QLabel()
        self.map = SvgMapWidget()

        layout = QVBoxLayout(self)
        title = QLabel("Map Viewer")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.packet_combo)
        layout.addWidget(self.summary)
        layout.addWidget(self.map, stretch=1)

        self.packet_combo.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.viewer_state(selected_packet_id(self.packet_combo))
        populate_packet_combo(self.packet_combo, state.packet_groups, state.packet.id)
        packet = state.packet
        self.summary.setText(
            f"{packet.name} | terrain {len(packet.terrain_areas)} | "
            f"dense {len(packet.dense_features)} | light {len(packet.light_features)}"
        )
        self.summary.setWordWrap(True)
        self.map.set_svg(state.map_svg)
