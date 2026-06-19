from __future__ import annotations

import webbrowser

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.desktop.screens.common import set_label_text


class SettingsScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.backend_status = QLabel()
        self.backend_detail = QLabel()
        self.codex_status = QLabel()
        self.codex_detail = QLabel()
        self.refresh_button = QPushButton("Refresh")
        self.login_button = QPushButton("Start Codex login")
        self.logout_button = QPushButton("Log out")

        layout = QVBoxLayout(self)
        title = QLabel("Settings")
        title.setObjectName("screenTitle")
        layout.addWidget(title)
        layout.addWidget(self.backend_status)
        layout.addWidget(self.backend_detail)
        layout.addSpacing(12)
        layout.addWidget(self.codex_status)
        layout.addWidget(self.codex_detail)

        actions = QHBoxLayout()
        actions.addWidget(self.refresh_button)
        actions.addWidget(self.login_button)
        actions.addWidget(self.logout_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addStretch(1)

        self.refresh_button.clicked.connect(self.refresh)
        self.login_button.clicked.connect(self.start_login)
        self.logout_button.clicked.connect(self.logout)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.settings_state()
        set_label_text(self.backend_status, state.app_backend_status)
        set_label_text(self.backend_detail, state.app_backend_detail)
        set_label_text(self.codex_status, state.codex_status.label)
        set_label_text(self.codex_detail, state.codex_status.detail)
        self.login_button.setEnabled(state.codex_status.can_login)
        self.logout_button.setEnabled(state.codex_status.can_logout)

    def start_login(self) -> None:
        try:
            login = self.service.start_codex_login()
        except Exception as exc:
            QMessageBox.warning(self, "Codex login", str(exc))
            return
        if login.auth_url:
            webbrowser.open(login.auth_url)
        self.refresh()

    def logout(self) -> None:
        try:
            self.service.logout_codex()
        except Exception as exc:
            QMessageBox.warning(self, "Codex logout", str(exc))
            return
        self.refresh()
