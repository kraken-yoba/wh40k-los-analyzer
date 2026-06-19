from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLabel  # type: ignore[import-not-found]

from warhammer_companion.application.view_models import PacketSelectGroup


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
