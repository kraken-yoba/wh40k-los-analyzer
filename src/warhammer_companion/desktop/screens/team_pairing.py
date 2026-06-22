from __future__ import annotations

from PySide6.QtCore import Qt  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QGridLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.application.view_models import TeamPairingMatrixState


class TeamPairingScreen(QWidget):
    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.friendly_lists_input = QPlainTextEdit("Alpha\nBeta")
        self.opponent_lists_input = QPlainTextEdit("Gamma\nDelta")
        self.generate_button = QPushButton("Generate")
        self.status_label = _plain_label()
        self.matrix_detail_label = _plain_label()
        self.warning_label = _plain_label()
        self.range_label = _plain_label()

        layout = QVBoxLayout(self)
        title = QLabel("Team Pairing")
        title.setObjectName("screenTitle")
        layout.addWidget(title)

        controls = QGridLayout()
        controls.addWidget(QLabel("Friendly lists"), 0, 0)
        controls.addWidget(QLabel("Opponent lists"), 0, 1)
        controls.addWidget(self.friendly_lists_input, 1, 0)
        controls.addWidget(self.opponent_lists_input, 1, 1)
        controls.addWidget(self.generate_button, 1, 2)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.range_label)
        layout.addWidget(self.matrix_detail_label)
        layout.addStretch(1)

        self.generate_button.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        state = self.service.team_pairing_matrix_state(
            friendly_lists=self.friendly_lists_input.toPlainText(),
            opponent_lists=self.opponent_lists_input.toPlainText(),
        )
        self._apply_inputs(state)
        self._set_state(state)

    def _apply_inputs(self, state: TeamPairingMatrixState) -> None:
        self.friendly_lists_input.setPlainText(state.friendly_lists_text)
        self.opponent_lists_input.setPlainText(state.opponent_lists_text)

    def _set_state(self, state: TeamPairingMatrixState) -> None:
        self.status_label.setText(
            f"Team Pairing readiness: {state.readiness}. "
            f"Rows: {len(state.friendly_lists)}. Columns: {len(state.opponent_lists)}. "
            f"Cells: {len(state.cells)}."
        )
        self.warning_label.setText(" ".join([*state.warning_details, *state.block_reason_details]))
        self.range_label.setText(_range_text(state))
        self.matrix_detail_label.setText(_matrix_text(state))


def _plain_label() -> QLabel:
    label = QLabel("")
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.PlainText)
    return label


def _range_text(state: TeamPairingMatrixState) -> str:
    if not state.ranges:
        return "No deterministic ranges available."
    return "\n".join(
        f"{scenario_range.label}: {scenario_range.min_value:.2f}-{scenario_range.max_value:.2f} "
        f"{scenario_range.units}"
        for scenario_range in state.ranges
    )


def _matrix_text(state: TeamPairingMatrixState) -> str:
    if not state.cells:
        return "No matrix cells."
    friendly_labels = {entry.list_id: entry.label for entry in state.friendly_lists}
    opponent_labels = {entry.list_id: entry.label for entry in state.opponent_lists}
    lines: list[str] = []
    for cell in state.cells:
        lines.append(
            f"{friendly_labels[cell.friendly_list_id]} vs "
            f"{opponent_labels[cell.opponent_list_id]} ({cell.readiness})"
        )
        lines.append(cell.shared_metric_notice)
        for component in cell.components:
            lines.append(f"{component.component_id} {component.assessment}: {component.detail}")
            for metric in component.metrics:
                lines.append(f"{metric.label}: {metric.value:.2f} {metric.units}")
            lines.extend(component.block_reasons)
    return "\n".join(lines)
