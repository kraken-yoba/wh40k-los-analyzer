from __future__ import annotations

from PySide6.QtCore import Qt  # type: ignore[import-not-found]
from PySide6.QtGui import QPainter, QPaintEvent, QPixmap  # type: ignore[import-not-found]
from PySide6.QtWidgets import QLabel, QScrollArea, QSizePolicy  # type: ignore[import-not-found]

from warhammer_companion.desktop.svg_raster import rasterize_svg

DESKTOP_MAP_PIXEL_RATIO = 3.0


class _SmoothPixmapLabel(QLabel):
    def __init__(self) -> None:
        super().__init__()
        self._source_pixmap = QPixmap()
        self.setAccessibleName("Rendered map")

    def set_source_pixmap(self, pixmap: QPixmap, logical_width: int, logical_height: int) -> None:
        self._source_pixmap = pixmap
        self.setFixedSize(logical_width, logical_height)
        self.update()

    def source_pixmap(self) -> QPixmap:
        return self._source_pixmap

    def paintEvent(self, event: QPaintEvent) -> None:
        if self._source_pixmap.isNull():
            super().paintEvent(event)
            return
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(self.rect(), self._source_pixmap)
        finally:
            painter.end()


class SvgMapWidget(QScrollArea):
    def __init__(self) -> None:
        super().__init__()
        self.image_label = _SmoothPixmapLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setWidget(self.image_label)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(360, 420)
        self.setStyleSheet("QScrollArea { background: #e7e0d1; border: 1px solid #d7d0c1; }")

    def set_svg(self, svg: str) -> None:
        pixmap = QPixmap()
        pixmap.loadFromData(rasterize_svg(svg, pixel_ratio=DESKTOP_MAP_PIXEL_RATIO), "PNG")
        self.image_label.set_source_pixmap(
            pixmap,
            int(round(pixmap.width() / DESKTOP_MAP_PIXEL_RATIO)),
            int(round(pixmap.height() / DESKTOP_MAP_PIXEL_RATIO)),
        )

    def rendered_pixmap(self) -> QPixmap:
        return self.image_label.source_pixmap()
