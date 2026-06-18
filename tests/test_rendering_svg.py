from __future__ import annotations

from warhammer_companion.los.geometry import (
    heatmap_exclusion_zone,
    heatmap_visibility_polygons_from_deployment_zone,
    safe_heatmap_regions,
    visibility_polygon_from_base,
)
from warhammer_companion.rendering.svg import render_map_svg
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_los_base_renders_as_server_rendered_svg_marker() -> None:
    svg = render_map_svg(SAMPLE_PACKETS[0], base_center=(22.0, 10.0), base_diameter=1.57)

    assert 'class="model-base"' in svg
    assert "data-draggable-base" not in svg
    assert "tabindex" not in svg


def test_heatmap_polygons_render_as_embedded_pixel_raster() -> None:
    packet = SAMPLE_PACKETS[0]
    polygons = heatmap_visibility_polygons_from_deployment_zone(packet, "attacker")

    svg = render_map_svg(packet, heatmap_polygons=polygons)

    assert 'class="heatmap-image"' in svg
    assert "data:image/png;base64," in svg
    assert 'class="heat-cell"' not in svg


def test_heatmap_raster_supports_blank_exclusion_and_safe_zone_outline() -> None:
    packet = SAMPLE_PACKETS[0]
    polygons = heatmap_visibility_polygons_from_deployment_zone(packet, "attacker")
    excluded_area = heatmap_exclusion_zone(packet, "attacker", source="interior")
    safe_regions = safe_heatmap_regions(packet, polygons, excluded_area=excluded_area)

    svg = render_map_svg(
        packet,
        heatmap_polygons=polygons,
        heatmap_exclusion=excluded_area,
        safe_regions=safe_regions,
    )

    assert 'class="heatmap-image"' in svg
    assert 'class="safe-zone-outline"' in svg


def test_binary_coverage_polygon_renders_as_embedded_pixel_raster() -> None:
    packet = SAMPLE_PACKETS[0]
    polygon = visibility_polygon_from_base(packet, center=(22.0, 10.0), base_diameter=1.57)

    svg = render_map_svg(packet, coverage_polygon=polygon)

    assert 'class="coverage-image"' in svg
    assert "data:image/png;base64," in svg
    assert 'class="coverage-cell"' not in svg


def test_light_and_dense_feature_profiles_render_with_distinct_classes() -> None:
    svg = render_map_svg(SAMPLE_PACKETS[0])

    assert "light-feature" in svg
    assert "dense-feature--container-or-solid" in svg
