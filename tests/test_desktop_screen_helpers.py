from __future__ import annotations

import os


def test_double_spin_box_uses_tool_screen_defaults() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.screens.common import double_spin_box

    app = QApplication.instance() or QApplication([])
    spin_box = double_spin_box(0.1, 8.0, 1.57)

    assert spin_box.minimum() == 0.1
    assert spin_box.maximum() == 8.0
    assert spin_box.decimals() == 2
    assert spin_box.singleStep() == 0.25
    assert spin_box.value() == 1.57
    spin_box.deleteLater()
    app.processEvents()
