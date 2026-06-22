from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget  # type: ignore[import-not-found]

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.application.view_models import MissionPackState


class MissionPackScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.mission_list_label = QLabel("")
        self.mission_list_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        title = QLabel("Mission Pack")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.mission_list_label)
        layout.addStretch(1)

        self.refresh()

    def refresh(self) -> None:
        self._set_state(self.service.mission_pack_state())

    def _set_state(self, state: MissionPackState) -> None:
        warnings = " ".join(state.warning_details)
        source_count = len(state.source_refs)
        self.status_label.setText(
            f"Source-pending mission skeleton. Readiness: {state.readiness}. "
            f"Primary missions: {state.mission_count}. Source refs: {source_count}. "
            f"{warnings}"
        )
        self.mission_list_label.setText(
            "\n".join(mission.label for mission in state.primary_missions)
        )
