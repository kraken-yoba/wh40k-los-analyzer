from __future__ import annotations

from PySide6.QtCore import QThreadPool  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.desktop.workers import FunctionWorker


class MapDataScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.pool = QThreadPool.globalInstance()
        self.status_label = QLabel()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Packet", "Source", "Terrain", "Features"])
        self.refresh_button = QPushButton("Refresh")
        self.ingest_button = QPushButton("Run ingestion")
        self.delete_button = QPushButton("Delete selected")

        layout = QVBoxLayout(self)
        title = QLabel("Map Data")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        actions.addWidget(self.refresh_button)
        actions.addWidget(self.ingest_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.refresh_button.clicked.connect(self.refresh)
        self.ingest_button.clicked.connect(self.run_ingestion)
        self.delete_button.clicked.connect(self.delete_selected)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.map_data_state()
        report = state.report
        report_text = (
            f"{report.packet_count} packets from {report.layout_count} layouts"
            if report
            else "No ingestion report available."
        )
        self.status_label.setText(report_text)
        self.table.setRowCount(len(state.packets))
        for row, packet in enumerate(state.packets):
            self.table.setItem(row, 0, QTableWidgetItem(packet.name))
            self.table.setItem(row, 1, QTableWidgetItem(packet.source))
            self.table.setItem(row, 2, QTableWidgetItem(str(len(packet.terrain_areas))))
            feature_count = len(packet.dense_features) + len(packet.light_features)
            self.table.setItem(row, 3, QTableWidgetItem(str(feature_count)))
            self.table.item(row, 0).setData(256, packet.id)
        self.table.resizeColumnsToContents()

    def run_ingestion(self) -> None:
        self.ingest_button.setEnabled(False)
        self.status_label.setText("Ingestion running...")
        worker = FunctionWorker(self.service.run_ingestion)
        worker.signals.succeeded.connect(lambda _: self._ingestion_finished())
        worker.signals.failed.connect(self._ingestion_failed)
        self.pool.start(worker)

    def delete_selected(self) -> None:
        selected = self.table.currentRow()
        if selected < 0:
            return
        item = self.table.item(selected, 0)
        packet_id = item.data(256)
        if not packet_id:
            return
        deleted = self.service.delete_packet(str(packet_id))
        if not deleted:
            QMessageBox.information(self, "Delete packet", "Selected packet was not deletable.")
        self.refresh()

    def _ingestion_finished(self) -> None:
        self.ingest_button.setEnabled(True)
        self.status_label.setText("Ingestion complete.")
        self.refresh()

    def _ingestion_failed(self, message: str) -> None:
        self.ingest_button.setEnabled(True)
        self.status_label.setText("Ingestion failed.")
        QMessageBox.warning(self, "Ingestion failed", message)
