from __future__ import annotations

from PySide6.QtCore import Signal  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QWidget,
)

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.application.view_models import PacketSelectGroup, PacketSelectorState


def populate_packet_combo(
    combo: QComboBox,
    groups: list[PacketSelectGroup],
    selected_packet_id: str,
) -> None:
    combo.blockSignals(True)
    combo.clear()
    selected_index = 0
    for group in groups:
        for option in group.options:
            combo.addItem(option.label, option.id)
            if option.id == selected_packet_id:
                selected_index = combo.count() - 1
    combo.setCurrentIndex(selected_index)
    combo.blockSignals(False)


def selected_packet_id(combo: QComboBox) -> str | None:
    data = combo.currentData()
    return str(data) if data else None


def set_label_text(label: QLabel, text: str) -> None:
    label.setText(text)
    label.setWordWrap(True)


def double_spin_box(minimum: float, maximum: float, value: float) -> QDoubleSpinBox:
    spin_box = QDoubleSpinBox()
    spin_box.setRange(minimum, maximum)
    spin_box.setDecimals(2)
    spin_box.setSingleStep(0.25)
    spin_box.setValue(value)
    return spin_box


class PacketSelectorWidget(QWidget):
    selection_changed = Signal()

    def __init__(self, service: WarhammerCompanionService) -> None:
        super().__init__()
        self.service = service
        self.player_a_combo = QComboBox()
        self.player_b_combo = QComboBox()
        self.layout_combo = QComboBox()
        self._loading = False

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(4)
        layout.addWidget(QLabel("Player A disposition"), 0, 0)
        layout.addWidget(QLabel("Player B disposition"), 0, 1)
        layout.addWidget(QLabel("Terrain layout"), 0, 2)
        layout.addWidget(self.player_a_combo, 1, 0)
        layout.addWidget(self.player_b_combo, 1, 1)
        layout.addWidget(self.layout_combo, 1, 2)

        self.player_a_combo.currentIndexChanged.connect(self._selection_updated)
        self.player_b_combo.currentIndexChanged.connect(self._selection_updated)
        self.layout_combo.currentIndexChanged.connect(self._selection_updated)
        self.apply_state(self.service.packet_selector_state())

    def selected_packet_id(self) -> str | None:
        data = self.layout_combo.currentData()
        return str(data) if data else None

    def apply_state(self, state: PacketSelectorState) -> None:
        self._loading = True
        self._populate_combo(
            self.player_a_combo,
            [(value, value) for value in state.player_a_options],
            state.selected_player_a,
        )
        self._populate_combo(
            self.player_b_combo,
            [(value, value) for value in state.player_b_options],
            state.selected_player_b,
        )
        self._populate_combo(
            self.layout_combo,
            [
                (f"{option.label} - {option.detail}", option.packet_id)
                for option in state.layout_options
            ],
            state.selected_packet_id,
        )
        self._loading = False

    def _selection_updated(self) -> None:
        if self._loading:
            return
        state = self.service.packet_selector_state(
            player_a=str(self.player_a_combo.currentData() or ""),
            player_b=str(self.player_b_combo.currentData() or ""),
            layout_variant=self._selected_layout_variant(),
        )
        self.apply_state(state)
        self.selection_changed.emit()

    def _selected_layout_variant(self) -> str:
        packet_id = self.selected_packet_id()
        if not packet_id:
            return ""
        state = self.service.packet_selector_state(packet_id=packet_id)
        return state.selected_layout_variant

    @staticmethod
    def _populate_combo(
        combo: QComboBox,
        options: list[tuple[str, str]],
        selected_value: str,
    ) -> None:
        combo.blockSignals(True)
        combo.clear()
        selected_index = 0
        for label, value in options:
            combo.addItem(label, value)
            if value == selected_value:
                selected_index = combo.count() - 1
        combo.setCurrentIndex(selected_index)
        combo.blockSignals(False)
