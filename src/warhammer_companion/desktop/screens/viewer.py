from __future__ import annotations

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QLabel,
    QVBoxLayout,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.desktop.screens.common import PacketSelectorWidget
from warhammer_companion.desktop.widgets.svg_map import SvgMapWidget


class ViewerScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.packet_selector = PacketSelectorWidget(service)
        self.summary = QLabel()
        self.map = SvgMapWidget()

        layout = QVBoxLayout(self)
        title = QLabel("Map Viewer")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.packet_selector)
        layout.addWidget(self.summary)
        layout.addWidget(self.map, stretch=1)

        self.packet_selector.selection_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.viewer_state(self.packet_selector.selected_packet_id())
        self.packet_selector.apply_state(state.packet_selector)
        packet = state.packet
        self.summary.setText(
            f"{packet.name} | terrain {len(packet.terrain_areas)} | "
            f"dense {len(packet.dense_features)} | light {len(packet.light_features)}"
        )
        self.summary.setWordWrap(True)
        self.map.set_svg(state.map_svg)
