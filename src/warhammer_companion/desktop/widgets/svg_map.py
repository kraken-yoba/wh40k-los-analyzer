from __future__ import annotations

from PySide6.QtCore import Qt  # type: ignore[import-not-found]
from PySide6.QtGui import QPixmap  # type: ignore[import-not-found]
from PySide6.QtWidgets import QLabel, QScrollArea, QSizePolicy  # type: ignore[import-not-found]

from warhammer_companion.desktop.svg_raster import rasterize_svg


class SvgMapWidget(QScrollArea):
    def __init__(self) -> None:
        super().__init__()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setWidget(self.image_label)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(360, 420)
        self.setStyleSheet("QScrollArea { background: #e7e0d1; border: 1px solid #d7d0c1; }")

    def set_svg(self, svg: str) -> None:
        pixmap = QPixmap()
        pixmap.loadFromData(rasterize_svg(svg), "PNG")
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(pixmap.size())
