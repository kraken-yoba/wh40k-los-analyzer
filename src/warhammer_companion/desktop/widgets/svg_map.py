from __future__ import annotations

from PySide6.QtCore import QByteArray  # type: ignore[import-not-found]
from PySide6.QtSvgWidgets import QSvgWidget  # type: ignore[import-not-found]
from PySide6.QtWidgets import QScrollArea, QSizePolicy  # type: ignore[import-not-found]


class SvgMapWidget(QScrollArea):
    def __init__(self) -> None:
        super().__init__()
        self.svg_widget = QSvgWidget()
        self.svg_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWidget(self.svg_widget)
        self.setWidgetResizable(True)
        self.setMinimumSize(360, 420)

    def set_svg(self, svg: str) -> None:
        self.svg_widget.load(QByteArray(svg.encode("utf-8")))
