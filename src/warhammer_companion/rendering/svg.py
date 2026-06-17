from __future__ import annotations

import base64
from html import escape
from io import BytesIO

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw
from shapely.geometry import Polygon

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.los.geometry import (
    CoverageCell,
    HeatmapCell,
    VisibilityPolygon,
    VisibilityRay,
)


def render_map_svg(
    packet: MapPacket,
    heatmap: list[HeatmapCell] | None = None,
    heatmap_polygons: list[VisibilityPolygon] | None = None,
    coverage: list[CoverageCell] | None = None,
    rays: list[VisibilityRay] | None = None,
    base_center: tuple[float, float] | None = None,
    base_diameter: float | None = None,
) -> str:
    scale = 12
    width = packet.board.width * scale
    height = packet.board.height * scale
    parts = [
        f'<svg class="map-svg" viewBox="0 0 {width:.0f} {height:.0f}" role="img" '
        f'aria-label="{escape(packet.name)} map">',
        f'<rect x="0" y="0" width="{width:.0f}" height="{height:.0f}" class="board"/>',
    ]

    if heatmap_polygons:
        parts.extend(_render_heatmap_raster(packet, heatmap_polygons, scale))
    elif heatmap:
        parts.extend(_render_heatmap_cells(heatmap, scale, packet.board.height))

    if coverage:
        parts.extend(_render_coverage(coverage, scale, packet.board.height))

    for zone in packet.deployment_zones:
        parts.append(_polygon(zone.footprint, scale, packet.board.height, "deployment"))
        parts.append(
            _label(
                zone.label,
                _polygon_centroid(zone.polygon()),
                scale,
                packet.board.height,
                "zone-label",
            )
        )

    for area in packet.terrain_areas:
        parts.append(_polygon(area.footprint, scale, packet.board.height, "terrain-area"))
        parts.append(
            _label(
                area.label,
                _polygon_centroid(area.polygon()),
                scale,
                packet.board.height,
                "terrain-label",
            )
        )

    for feature in packet.dense_features:
        parts.append(_polygon(feature.footprint, scale, packet.board.height, "dense-feature"))

    if rays:
        ox, oy = base_center or (0.0, 0.0)
        for ray in rays:
            x1, y1 = _to_svg_point((ox, oy), scale, packet.board.height)
            x2, y2 = _to_svg_point(ray.target, scale, packet.board.height)
            css_class = "ray-visible" if ray.visible else "ray-blocked"
            parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" '
                f'x2="{x2:.1f}" y2="{y2:.1f}" class="{css_class}"/>'
            )

    if base_center and base_diameter:
        cx, cy = _to_svg_point(base_center, scale, packet.board.height)
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" '
            f'r="{base_diameter * scale / 2:.1f}" class="model-base" '
            'data-draggable-base="true" tabindex="0"/>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _render_heatmap_raster(
    packet: MapPacket, polygons: list[VisibilityPolygon], scale: int
) -> list[str]:
    width = int(round(packet.board.width * scale))
    height = int(round(packet.board.height * scale))
    accumulator: NDArray[np.uint16] = np.zeros((height, width), dtype=np.uint16)

    for item in polygons:
        if item.polygon.is_empty:
            continue
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        rings = [item.polygon.exterior, *item.polygon.interiors]
        for index, ring in enumerate(rings):
            points = [_to_svg_point((x, y), scale, packet.board.height) for x, y in ring.coords]
            fill = 1 if index == 0 else 0
            draw.polygon(points, fill=fill)
        accumulator += np.asarray(mask, dtype=np.uint16)

    visibility = accumulator.astype(np.float64) / max(len(polygons), 1)
    image = Image.fromarray(_colorize_heatmap_array(visibility), "RGBA")
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return [
        f'<image x="0" y="0" width="{width}" height="{height}" '
        f'href="data:image/png;base64,{encoded}" preserveAspectRatio="none" '
        'class="heatmap-image"/>'
    ]


def _colorize_heatmap_array(visibility: NDArray[np.float64]) -> NDArray[np.uint8]:
    stops = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0], dtype=np.float32)
    colors = np.array(
        [
            [155, 59, 53],
            [207, 126, 58],
            [213, 182, 76],
            [100, 166, 93],
            [31, 122, 95],
            [31, 122, 95],
        ],
        dtype=np.float32,
    )
    rgba = np.zeros((*visibility.shape, 4), dtype=np.uint8)
    for channel in range(3):
        rgba[..., channel] = np.interp(visibility, stops, colors[:, channel]).astype(np.uint8)
    rgba[..., 3] = 184
    return rgba


def _render_heatmap_cells(cells: list[HeatmapCell], scale: int, board_height: float) -> list[str]:
    if len(cells) < 2:
        return []
    step = _infer_grid_step([cell.x for cell in cells])
    rendered: list[str] = []
    for cell in cells:
        x, y = _to_svg_point((cell.x - step / 2.0, cell.y + step / 2.0), scale, board_height)
        rendered.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{step * scale:.1f}" '
            f'height="{step * scale:.1f}" fill="{_heatmap_color(cell.visibility)}" '
            'opacity="0.82" class="heat-cell"/>'
        )
    return rendered


def _render_coverage(cells: list[CoverageCell], scale: int, board_height: float) -> list[str]:
    if len(cells) < 2:
        return []
    step = _infer_grid_step([cell.x for cell in cells])
    rendered: list[str] = []
    for cell in cells:
        if not cell.visible:
            continue
        x, y = _to_svg_point((cell.x - step / 2.0, cell.y + step / 2.0), scale, board_height)
        rendered.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{step * scale:.1f}" '
            f'height="{step * scale:.1f}" class="coverage-cell"/>'
        )
    return rendered


def _heatmap_color(visibility: float) -> str:
    if visibility >= 0.8:
        return "#1f7a5f"
    if visibility >= 0.6:
        return "#64a65d"
    if visibility >= 0.4:
        return "#d5b64c"
    if visibility >= 0.2:
        return "#cf7e3a"
    return "#9b3b35"


def _infer_grid_step(values: list[float]) -> float:
    xs = sorted(set(values))
    if len(xs) > 1:
        return xs[1] - xs[0]
    return 1.0


def _polygon(
    points: list[tuple[float, float]], scale: int, board_height: float, css_class: str
) -> str:
    svg_points = [_to_svg_point(point, scale, board_height) for point in points]
    joined = " ".join(f"{x:.1f},{y:.1f}" for x, y in svg_points)
    return f'<polygon points="{joined}" class="{css_class}"/>'


def _label(
    text: str, point: tuple[float, float], scale: int, board_height: float, css_class: str
) -> str:
    x, y = _to_svg_point(point, scale, board_height)
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{css_class}">{escape(text)}</text>'


def _polygon_centroid(polygon: Polygon) -> tuple[float, float]:
    centroid = polygon.centroid
    return (centroid.x, centroid.y)


def _to_svg_point(
    point: tuple[float, float], scale: int, board_height: float
) -> tuple[float, float]:
    x, y = point
    return (x * scale, (board_height - y) * scale)
