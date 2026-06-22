from __future__ import annotations

from PySide6.QtCore import QSize  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.desktop.screens.deployment_exposure import DeploymentExposureScreen
from warhammer_companion.desktop.screens.heatmap import HeatmapScreen
from warhammer_companion.desktop.screens.hidden_coverage import HiddenCoverageScreen
from warhammer_companion.desktop.screens.los_checker import LosCheckerScreen
from warhammer_companion.desktop.screens.map_data import MapDataScreen
from warhammer_companion.desktop.screens.movement_reach import MovementReachScreen
from warhammer_companion.desktop.screens.settings import SettingsScreen
from warhammer_companion.desktop.screens.threat_range import ThreatRangeScreen
from warhammer_companion.desktop.screens.viewer import ViewerScreen


class MainWindow(QMainWindow):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.setWindowTitle("Warhammer Tournament Companion")
        self.resize(QSize(1180, 820))

        self.nav = QListWidget()
        self.nav.setFixedWidth(220)
        self.stack = QStackedWidget()

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.nav)
        layout.addWidget(self.stack, stretch=1)
        self.setCentralWidget(root)

        self._add_screen("Settings", SettingsScreen(service))
        self._add_screen("Map Data", MapDataScreen(service))
        self._add_screen("Map Viewer", ViewerScreen(service))
        self._add_screen("LOS Heatmap", HeatmapScreen(service))
        self._add_screen("LOS Checker", LosCheckerScreen(service))
        self._add_screen("Movement Reach", MovementReachScreen(service))
        self._add_screen("Threat Range", ThreatRangeScreen(service))
        self._add_screen("Deployment Exposure", DeploymentExposureScreen(service))
        self._add_screen("Hidden Coverage", HiddenCoverageScreen(service))
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(2)

    def _add_screen(self, label: str, widget: QWidget) -> None:
        item = QListWidgetItem(label)
        self.nav.addItem(item)
        self.stack.addWidget(widget)
