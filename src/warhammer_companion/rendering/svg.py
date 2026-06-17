from __future__ import annotations

from html import escape

from shapely.geometry import Polygon

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.los.geometry import HeatmapCell, VisibilityRay


def render_map_svg(
    packet: MapPacket,
    heatmap: list[HeatmapCell] | None = None,
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

    if heatmap:
        parts.extend(_render_heatmap(heatmap, scale, packet.board.height))

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
            f'r="{base_diameter * scale / 2:.1f}" class="model-base"/>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _render_heatmap(cells: list[HeatmapCell], scale: int, board_height: float) -> list[str]:
    if len(cells) < 2:
        return []
    step = _infer_grid_step(cells)
    rendered: list[str] = []
    for cell in cells:
        x, y = _to_svg_point((cell.x - step / 2.0, cell.y + step / 2.0), scale, board_height)
        opacity = 0.12 + 0.58 * cell.visibility
        rendered.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{step * scale:.1f}" height="{step * scale:.1f}" '
            f'fill="rgb(36, 130, 95)" opacity="{opacity:.3f}" class="heat-cell"/>'
        )
    return rendered


def _infer_grid_step(cells: list[HeatmapCell]) -> float:
    xs = sorted({cell.x for cell in cells})
    if len(xs) > 1:
        return xs[1] - xs[0]
    return 4.0


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
