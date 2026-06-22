from __future__ import annotations

import base64
import re
from dataclasses import replace
from io import BytesIO

import numpy as np
from PIL import Image

from warhammer_companion.domain.models import DeploymentZone
from warhammer_companion.los.exposure import (
    candidate_staging_center_region,
    exposure_risk_region,
)
from warhammer_companion.los.geometry import (
    heatmap_exclusion_zone,
    heatmap_visibility_polygons_from_deployment_zone,
    hidden_coverage_from_terrain_area,
    safe_heatmap_regions,
    visibility_polygon_from_base,
)
from warhammer_companion.los.movement import movement_envelope, swept_base_path
from warhammer_companion.los.threat import threat_projection_regions
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


def test_coverage_raster_preserves_visible_pixel_color_and_alpha() -> None:
    packet = SAMPLE_PACKETS[0]
    polygon = visibility_polygon_from_base(packet, center=(22.0, 10.0), base_diameter=1.57)

    svg = render_map_svg(packet, coverage_polygon=polygon)

    image = _decoded_png_for_class(svg, "coverage-image")
    rgba = np.asarray(image, dtype=np.uint8)
    visible = rgba[rgba[..., 3] > 0]
    assert visible.size > 0
    assert (42, 140, 158, 118) in {tuple(pixel) for pixel in visible}


def test_movement_envelope_renders_as_embedded_raster_with_endpoint_markers() -> None:
    packet = SAMPLE_PACKETS[0]
    envelope = movement_envelope(
        packet,
        start_center=(16.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
    )
    movement_path = swept_base_path(
        start_center=(16.0, 10.0),
        target_center=(22.0, 10.0),
        base_diameter=1.57,
    )

    svg = render_map_svg(
        packet,
        movement_envelope=envelope,
        movement_path=movement_path,
        movement_start_center=(16.0, 10.0),
        movement_target_center=(22.0, 10.0),
        movement_base_diameter=1.57,
    )

    assert 'class="movement-envelope-image"' in svg
    assert 'class="movement-path-outline"' in svg
    assert 'class="movement-start-base"' in svg
    assert 'class="movement-target-base"' in svg
    assert "data:image/png;base64," in svg


def test_movement_envelope_raster_preserves_visible_pixel_color_and_alpha() -> None:
    packet = SAMPLE_PACKETS[0]
    envelope = movement_envelope(
        packet,
        start_center=(16.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
    )

    svg = render_map_svg(packet, movement_envelope=envelope)

    image = _decoded_png_for_class(svg, "movement-envelope-image")
    rgba = np.asarray(image, dtype=np.uint8)
    visible = rgba[rgba[..., 3] > 0]
    assert visible.size > 0
    assert (75, 125, 178, 96) in {tuple(pixel) for pixel in visible}


def test_threat_projection_renders_probability_raster_and_markers() -> None:
    packet = SAMPLE_PACKETS[0]
    regions = threat_projection_regions(
        packet,
        source_center=(16.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
        threat_range=2.0,
        mode="2d6-move-plus-range",
    )

    svg = render_map_svg(
        packet,
        threat_regions=regions,
        threat_source_center=(16.0, 10.0),
        threat_target_point=(24.0, 10.0),
        threat_base_diameter=1.57,
    )

    assert 'class="threat-projection-image"' in svg
    assert 'class="threat-source-base"' in svg
    assert 'class="threat-target-point"' in svg
    assert "data:image/png;base64," in svg
    image = _decoded_png_for_class(svg, "threat-projection-image")
    assert image.size == (528, 720)
    alpha = np.asarray(image, dtype=np.uint8)[..., 3]
    positive_alpha = alpha[alpha > 0]
    assert int(alpha.min()) == 0
    assert int(positive_alpha.max()) > int(positive_alpha.min())


def test_threat_source_region_renders_without_point_source_marker() -> None:
    packet = SAMPLE_PACKETS[0]
    regions = threat_projection_regions(
        packet,
        source_center=(16.0, 10.0),
        base_diameter=1.57,
        move_distance=0.0,
        threat_range=2.0,
        mode="raw-range",
    )
    source_region = packet.deployment_zone("attacker").polygon().buffer(-1.57 / 2.0)

    svg = render_map_svg(
        packet,
        threat_regions=regions,
        threat_source_region=source_region,
        threat_target_point=(24.0, 10.0),
        threat_base_diameter=1.57,
    )

    assert 'class="threat-source-region"' in svg
    assert 'class="threat-source-base"' not in svg
    assert 'class="threat-projection-image"' in svg


def test_deployment_exposure_projection_reuses_existing_overlay_primitives() -> None:
    packet = SAMPLE_PACKETS[0]
    threat_regions = threat_projection_regions(
        packet,
        source_center=(38.0, 52.0),
        base_diameter=1.57,
        move_distance=0.0,
        threat_range=1.0,
        mode="raw-range",
    )
    threat_region = threat_regions[0].geometry
    los_region = visibility_polygon_from_base(packet, center=(38.0, 52.0), base_diameter=1.57)
    risk_region = exposure_risk_region(
        threat_region=threat_region,
        los_region=los_region,
        exposure_mode="threat-and-los",
    )
    candidate_region = candidate_staging_center_region(
        packet,
        deployment_zone_id="attacker",
        base_radius=1.57 / 2.0,
        risk_region=risk_region,
    )

    svg = render_map_svg(
        packet,
        coverage_polygon=los_region,
        safe_regions=candidate_region,
        base_center=(10.0, 5.0),
        base_diameter=1.57,
        threat_regions=threat_regions,
        threat_source_center=(38.0, 52.0),
        threat_base_diameter=1.57,
    )

    assert 'class="safe-zone-outline"' in svg
    assert 'class="coverage-image"' in svg
    assert 'class="threat-projection-image"' in svg
    assert 'class="model-base"' in svg
    assert 'class="threat-source-base"' in svg


def test_hidden_coverage_renders_as_embedded_exposure_heatmap() -> None:
    packet = SAMPLE_PACKETS[0]
    terrain_area_id = packet.terrain_areas[0].id
    coverage = hidden_coverage_from_terrain_area(
        packet,
        terrain_area_id,
        observer_grid_step=4.0,
        hidden_sample_step=3.0,
    )

    svg = render_map_svg(packet, hidden_coverage=coverage)

    assert 'class="hidden-coverage-image"' in svg
    assert 'class="selected-terrain-area"' in svg
    assert 'class="hidden-sample-point"' in svg
    assert "data:image/png;base64," in svg


def test_hidden_coverage_raster_preserves_zero_and_positive_alpha_pixels() -> None:
    packet = SAMPLE_PACKETS[0]
    terrain_area_id = packet.terrain_areas[0].id
    coverage = hidden_coverage_from_terrain_area(
        packet,
        terrain_area_id,
        observer_grid_step=4.0,
        hidden_sample_step=3.0,
    )

    svg = render_map_svg(packet, hidden_coverage=coverage)

    image = _decoded_png_for_class(svg, "hidden-coverage-image")
    alpha = np.asarray(image, dtype=np.uint8)[..., 3]
    assert int(alpha.max()) > 0
    assert int(alpha.min()) == 0


def test_heatmap_raster_exclusion_preserves_transparent_pixels() -> None:
    packet = SAMPLE_PACKETS[0]
    polygons = heatmap_visibility_polygons_from_deployment_zone(packet, "attacker")
    excluded_area = heatmap_exclusion_zone(packet, "attacker", source="interior")

    svg = render_map_svg(
        packet,
        heatmap_polygons=polygons,
        heatmap_exclusion=excluded_area,
    )

    image = _decoded_png_for_class(svg, "heatmap-image")
    alpha = np.asarray(image, dtype=np.uint8)[..., 3]
    assert int(alpha.max()) > 0
    assert int(alpha.min()) == 0


def test_hidden_coverage_raster_uses_pixel_accumulated_threat_regions() -> None:
    packet = SAMPLE_PACKETS[0]
    terrain_area_id = packet.terrain_areas[0].id
    coverage = hidden_coverage_from_terrain_area(
        packet,
        terrain_area_id,
        observer_grid_step=4.0,
        hidden_sample_step=3.0,
    )
    assert coverage.threat_regions
    pixel_only_coverage = replace(coverage, cells=[])

    svg = render_map_svg(packet, hidden_coverage=pixel_only_coverage)

    assert 'class="hidden-coverage-image"' in svg
    assert 'width="528" height="720"' in svg
    assert "data:image/png;base64," in svg


def test_light_and_dense_feature_profiles_render_with_distinct_classes() -> None:
    svg = render_map_svg(SAMPLE_PACKETS[0])

    assert "light-feature" in svg
    assert "dense-feature--container-or-solid" in svg


def test_map_svg_includes_presentation_attributes_for_desktop_rasterizer() -> None:
    svg = render_map_svg(
        SAMPLE_PACKETS[0],
        base_center=(22.0, 10.0),
        base_diameter=1.57,
    )

    assert 'class="board" fill="#eee8d9" stroke="#2b322c"' in svg
    assert 'class="terrain-area" fill="#807863"' in svg
    assert 'class="dense-feature dense-feature--container-or-solid" fill="#30464e"' in svg
    assert 'class="light-feature light-feature--light-area" fill="#c69930"' in svg
    assert 'class="terrain-label" fill="#1c2520"' in svg
    assert 'class="model-base" fill="#e6f4ee"' in svg


def test_curved_deployment_zone_visual_boundary_is_densified() -> None:
    curved_attacker = DeploymentZone(
        id="attacker",
        label="Attacker",
        footprint=[
            (22.0, 60.0),
            (22.0, 40.0),
            (18.5, 39.3),
            (15.6, 37.4),
            (13.7, 34.5),
            (13.0, 30.0),
            (0.0, 30.0),
            (0.0, 60.0),
        ],
    )
    packet = SAMPLE_PACKETS[0].model_copy(
        update={
            "deployment_zones": [
                curved_attacker,
                SAMPLE_PACKETS[0].deployment_zones[1],
            ]
        }
    )

    svg = render_map_svg(packet)
    match = re.search(r'<polygon points="([^"]+)" class="deployment"', svg)

    assert match is not None
    assert len(match.group(1).split()) > len(curved_attacker.footprint) * 2


def _decoded_png_for_class(svg: str, css_class: str) -> Image.Image:
    pattern = rf'<image [^>]*href="data:image/png;base64,([^"]+)"[^>]*class="{css_class}"'
    match = re.search(pattern, svg)
    assert match is not None
    return Image.open(BytesIO(base64.b64decode(match.group(1)))).convert("RGBA")
