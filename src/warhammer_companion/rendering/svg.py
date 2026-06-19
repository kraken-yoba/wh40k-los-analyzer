from __future__ import annotations

import base64
from html import escape
from io import BytesIO

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.los.geometry import (
    CoverageCell,
    HeatmapCell,
    VisibilityPolygon,
    VisibilityRay,
)

SVG_ATTRS = dict[str, str | int | float]

BOARD_ATTRS: SVG_ATTRS = {
    "fill": "#eee8d9",
    "stroke": "#2b322c",
    "stroke-width": 2,
}
DEPLOYMENT_ATTRS: SVG_ATTRS = {
    "fill": "#2d6f5b",
    "fill-opacity": 0.12,
    "stroke": "#2d6f5b",
    "stroke-opacity": 0.6,
    "stroke-width": 1.5,
    "stroke-dasharray": "6 4",
}
TERRAIN_AREA_ATTRS: SVG_ATTRS = {
    "fill": "#807863",
    "fill-opacity": 0.34,
    "stroke": "#2d2b24",
    "stroke-opacity": 0.78,
    "stroke-width": 1.6,
}
DENSE_FEATURE_ATTRS: SVG_ATTRS = {
    "fill": "#31362d",
    "fill-opacity": 0.72,
    "stroke": "#121612",
    "stroke-opacity": 0.82,
    "stroke-width": 1.3,
}
DENSE_RUIN_ATTRS: SVG_ATTRS = DENSE_FEATURE_ATTRS | {
    "fill": "#232b25",
    "fill-opacity": 0.82,
}
DENSE_CONTAINER_ATTRS: SVG_ATTRS = DENSE_FEATURE_ATTRS | {
    "fill": "#30464e",
    "fill-opacity": 0.74,
}
DENSE_SOLID_ATTRS: SVG_ATTRS = DENSE_FEATURE_ATTRS | {
    "fill-opacity": 0.78,
}
LIGHT_FEATURE_ATTRS: SVG_ATTRS = {
    "fill": "#c69930",
    "fill-opacity": 0.36,
    "stroke": "#976d1a",
    "stroke-opacity": 0.54,
    "stroke-width": 1.1,
}
TERRAIN_LABEL_ATTRS: SVG_ATTRS = {
    "fill": "#1c2520",
    "font-family": "Arial",
    "font-size": 13,
    "font-weight": "bold",
    "text-anchor": "middle",
    "dominant-baseline": "middle",
}
ZONE_LABEL_ATTRS: SVG_ATTRS = TERRAIN_LABEL_ATTRS | {
    "fill": "#2d6f5b",
    "font-size": 11,
}
SAFE_ZONE_ATTRS: SVG_ATTRS = {
    "fill": "none",
    "stroke": "#f7efe0",
    "stroke-width": 2.2,
    "stroke-linejoin": "round",
    "stroke-linecap": "round",
}
COVERAGE_CELL_ATTRS: SVG_ATTRS = {
    "fill": "#2a8c9e",
    "fill-opacity": 0.34,
    "stroke": "none",
}
MODEL_BASE_ATTRS: SVG_ATTRS = {
    "fill": "#e6f4ee",
    "fill-opacity": 0.88,
    "stroke": "#1f5948",
    "stroke-width": 2,
}
RAY_VISIBLE_ATTRS: SVG_ATTRS = {
    "stroke": "#2d6f5b",
    "stroke-opacity": 0.44,
    "stroke-width": 1.1,
}
RAY_BLOCKED_ATTRS: SVG_ATTRS = {
    "stroke": "#8b2f2d",
    "stroke-opacity": 0.26,
    "stroke-width": 1,
}


def render_map_svg(
    packet: MapPacket,
    heatmap: list[HeatmapCell] | None = None,
    heatmap_polygons: list[VisibilityPolygon] | None = None,
    heatmap_exclusion: BaseGeometry | None = None,
    safe_regions: BaseGeometry | None = None,
    coverage: list[CoverageCell] | None = None,
    coverage_polygon: BaseGeometry | None = None,
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
        f'<rect x="0" y="0" width="{width:.0f}" height="{height:.0f}" '
        f'class="board"{_attrs(BOARD_ATTRS)}/>',
    ]

    if heatmap_polygons:
        parts.extend(
            _render_heatmap_raster(
                packet,
                heatmap_polygons,
                scale,
                heatmap_exclusion=heatmap_exclusion,
            )
        )
    elif heatmap:
        parts.extend(_render_heatmap_cells(heatmap, scale, packet.board.height))

    if safe_regions is not None:
        parts.extend(
            _render_geometry_outlines(
                safe_regions,
                scale,
                packet.board.height,
                "safe-zone-outline",
            )
        )

    if coverage_polygon is not None:
        parts.extend(_render_coverage_raster(packet, coverage_polygon, scale))
    elif coverage:
        parts.extend(_render_coverage_cells(coverage, scale, packet.board.height))

    for zone in packet.deployment_zones:
        parts.append(
            _polygon(
                zone.footprint,
                scale,
                packet.board.height,
                "deployment",
                DEPLOYMENT_ATTRS,
            )
        )
        parts.append(
            _label(
                zone.label,
                _polygon_centroid(zone.polygon()),
                scale,
                packet.board.height,
                "zone-label",
                ZONE_LABEL_ATTRS,
            )
        )

    for area in packet.terrain_areas:
        parts.append(
            _polygon(
                area.footprint,
                scale,
                packet.board.height,
                "terrain-area",
                TERRAIN_AREA_ATTRS,
            )
        )
        parts.append(
            _label(
                area.label,
                _polygon_centroid(area.polygon()),
                scale,
                packet.board.height,
                "terrain-label",
                TERRAIN_LABEL_ATTRS,
            )
        )

    for light_feature in packet.light_features:
        parts.append(
            _polygon(
                light_feature.footprint,
                scale,
                packet.board.height,
                _feature_css_class("light-feature", light_feature.profile),
                LIGHT_FEATURE_ATTRS,
            )
        )

    for dense_feature in packet.dense_features:
        parts.append(
            _polygon(
                dense_feature.footprint,
                scale,
                packet.board.height,
                _feature_css_class("dense-feature", dense_feature.profile),
                _dense_feature_attrs(dense_feature.profile),
            )
        )

    if rays:
        ox, oy = base_center or (0.0, 0.0)
        for ray in rays:
            x1, y1 = _to_svg_point((ox, oy), scale, packet.board.height)
            x2, y2 = _to_svg_point(ray.target, scale, packet.board.height)
            css_class = "ray-visible" if ray.visible else "ray-blocked"
            attrs = RAY_VISIBLE_ATTRS if ray.visible else RAY_BLOCKED_ATTRS
            parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" '
                f'x2="{x2:.1f}" y2="{y2:.1f}" class="{css_class}"{_attrs(attrs)}/>'
            )

    if base_center and base_diameter:
        cx, cy = _to_svg_point(base_center, scale, packet.board.height)
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" '
            f'r="{base_diameter * scale / 2:.1f}" '
            f'class="model-base"{_attrs(MODEL_BASE_ATTRS)}/>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _render_heatmap_raster(
    packet: MapPacket,
    polygons: list[VisibilityPolygon],
    scale: int,
    *,
    heatmap_exclusion: BaseGeometry | None = None,
) -> list[str]:
    width = int(round(packet.board.width * scale))
    height = int(round(packet.board.height * scale))
    accumulator: NDArray[np.uint16] = np.zeros((height, width), dtype=np.uint16)

    for item in polygons:
        if item.polygon.is_empty:
            continue
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        _draw_geometry_mask(draw, item.polygon, scale, packet.board.height, exterior_fill=1)
        accumulator += np.asarray(mask, dtype=np.uint16)

    visibility = accumulator.astype(np.float64) / max(len(polygons), 1)
    rgba = _colorize_heatmap_array(visibility)
    if heatmap_exclusion is not None and not heatmap_exclusion.is_empty:
        exclusion_mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(exclusion_mask)
        _draw_geometry_mask(
            draw,
            heatmap_exclusion,
            scale,
            packet.board.height,
            exterior_fill=255,
        )
        rgba[np.asarray(exclusion_mask, dtype=np.uint8) > 0, 3] = 0

    image = Image.fromarray(rgba, "RGBA")
    return [_image_data_uri(image, width, height, "heatmap-image")]


def _render_coverage_raster(packet: MapPacket, polygon: BaseGeometry, scale: int) -> list[str]:
    if polygon.is_empty:
        return []
    width = int(round(packet.board.width * scale))
    height = int(round(packet.board.height * scale))
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    _draw_geometry_mask(draw, polygon, scale, packet.board.height, exterior_fill=255)

    rgba: NDArray[np.uint8] = np.zeros((height, width, 4), dtype=np.uint8)
    visible = np.asarray(mask, dtype=np.uint8) > 0
    rgba[visible] = (42, 140, 158, 118)
    image = Image.fromarray(rgba, "RGBA")
    return [_image_data_uri(image, width, height, "coverage-image")]


def _draw_geometry_mask(
    draw: ImageDraw.ImageDraw,
    geometry: BaseGeometry,
    scale: int,
    board_height: float,
    exterior_fill: int,
) -> None:
    if isinstance(geometry, MultiPolygon):
        for polygon in geometry.geoms:
            _draw_polygon_mask(draw, polygon, scale, board_height, exterior_fill)
        return
    if isinstance(geometry, Polygon):
        _draw_polygon_mask(draw, geometry, scale, board_height, exterior_fill)


def _draw_polygon_mask(
    draw: ImageDraw.ImageDraw,
    polygon: Polygon,
    scale: int,
    board_height: float,
    exterior_fill: int,
) -> None:
    rings = [polygon.exterior, *polygon.interiors]
    for index, ring in enumerate(rings):
        points = [_to_svg_point((x, y), scale, board_height) for x, y in ring.coords]
        fill = exterior_fill if index == 0 else 0
        draw.polygon(points, fill=fill)


def _image_data_uri(image: Image.Image, width: int, height: int, css_class: str) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return (
        f'<image x="0" y="0" width="{width}" height="{height}" '
        f'href="data:image/png;base64,{encoded}" preserveAspectRatio="none" '
        f'class="{css_class}"/>'
    )


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


def _render_coverage_cells(cells: list[CoverageCell], scale: int, board_height: float) -> list[str]:
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
            f'height="{step * scale:.1f}" '
            f'class="coverage-cell"{_attrs(COVERAGE_CELL_ATTRS)}/>'
        )
    return rendered


def _render_geometry_outlines(
    geometry: BaseGeometry,
    scale: int,
    board_height: float,
    css_class: str,
) -> list[str]:
    if geometry.is_empty:
        return []
    if isinstance(geometry, MultiPolygon):
        rendered: list[str] = []
        for polygon in geometry.geoms:
            rendered.extend(_render_polygon_outlines(polygon, scale, board_height, css_class))
        return rendered
    if isinstance(geometry, Polygon):
        return _render_polygon_outlines(geometry, scale, board_height, css_class)
    return []


def _render_polygon_outlines(
    polygon: Polygon,
    scale: int,
    board_height: float,
    css_class: str,
) -> list[str]:
    rings = [polygon.exterior, *polygon.interiors]
    return [
        _polyline(
            [(float(x), float(y)) for x, y in ring.coords],
            scale,
            board_height,
            css_class,
            SAFE_ZONE_ATTRS if css_class == "safe-zone-outline" else None,
        )
        for ring in rings
        if len(ring.coords) >= 3
    ]


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


def _feature_css_class(base_class: str, profile: str | None) -> str:
    if profile is None:
        return base_class
    modifier = profile.replace("_", "-")
    return f"{base_class} {base_class}--{escape(modifier)}"


def _dense_feature_attrs(profile: str | None) -> SVG_ATTRS:
    if profile is None:
        return DENSE_FEATURE_ATTRS
    if "container" in profile:
        return DENSE_CONTAINER_ATTRS
    if "solid" in profile or "unknown_dense" in profile:
        return DENSE_SOLID_ATTRS
    if "ruined_wall" in profile:
        return DENSE_RUIN_ATTRS
    return DENSE_FEATURE_ATTRS


def _infer_grid_step(values: list[float]) -> float:
    xs = sorted(set(values))
    if len(xs) > 1:
        return xs[1] - xs[0]
    return 1.0


def _polygon(
    points: list[tuple[float, float]],
    scale: int,
    board_height: float,
    css_class: str,
    attrs: SVG_ATTRS | None = None,
) -> str:
    svg_points = [_to_svg_point(point, scale, board_height) for point in points]
    joined = " ".join(f"{x:.1f},{y:.1f}" for x, y in svg_points)
    return f'<polygon points="{joined}" class="{css_class}"{_attrs(attrs)}/>'


def _polyline(
    points: list[tuple[float, float]],
    scale: int,
    board_height: float,
    css_class: str,
    attrs: SVG_ATTRS | None = None,
) -> str:
    svg_points = [_to_svg_point(point, scale, board_height) for point in points]
    joined = " ".join(f"{x:.1f},{y:.1f}" for x, y in svg_points)
    return f'<polyline points="{joined}" class="{css_class}"{_attrs(attrs)}/>'


def _label(
    text: str,
    point: tuple[float, float],
    scale: int,
    board_height: float,
    css_class: str,
    attrs: SVG_ATTRS | None = None,
) -> str:
    x, y = _to_svg_point(point, scale, board_height)
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{css_class}"{_attrs(attrs)}>{escape(text)}</text>'


def _attrs(attrs: SVG_ATTRS | None) -> str:
    if not attrs:
        return ""
    return "".join(f' {key}="{escape(str(value))}"' for key, value in attrs.items())


def _polygon_centroid(polygon: Polygon) -> tuple[float, float]:
    centroid = polygon.centroid
    return (centroid.x, centroid.y)


def _to_svg_point(
    point: tuple[float, float], scale: int, board_height: float
) -> tuple[float, float]:
    x, y = point
    return (x * scale, (board_height - y) * scale)
