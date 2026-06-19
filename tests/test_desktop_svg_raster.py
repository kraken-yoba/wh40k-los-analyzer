from __future__ import annotations

from io import BytesIO

from PIL import Image

from warhammer_companion.desktop.app import packaged_seed_packets
from warhammer_companion.desktop.svg_raster import rasterize_svg
from warhammer_companion.rendering.svg import render_map_svg


def test_rasterize_svg_draws_shapes_and_text() -> None:
    svg = (
        '<svg viewBox="0 0 240 120">'
        '<rect x="0" y="0" width="240" height="120" fill="#eee8d9"/>'
        '<polygon points="20,20 120,20 120,90 20,90" fill="#807863" '
        'fill-opacity="0.34" stroke="#2d2b24" stroke-width="2"/>'
        '<text x="70" y="55" fill="#1c2520" font-size="18" '
        'font-weight="bold">Terrain 1</text>'
        "</svg>"
    )

    image = Image.open(BytesIO(rasterize_svg(svg))).convert("RGBA")

    assert image.size == (240, 120)
    assert len(image.getcolors(maxcolors=100_000) or []) > 3


def test_rasterize_svg_can_supersample_output() -> None:
    svg = (
        '<svg viewBox="0 0 240 120">'
        '<circle cx="60" cy="60" r="42" fill="#30464e" stroke="#121612" stroke-width="2"/>'
        "</svg>"
    )

    image = Image.open(BytesIO(rasterize_svg(svg, pixel_ratio=3))).convert("RGBA")

    assert image.size == (720, 360)


def test_rasterize_svg_draws_all_bundled_official_maps() -> None:
    packets = packaged_seed_packets()

    assert len(packets) == 45
    for packet in packets:
        image = Image.open(BytesIO(rasterize_svg(render_map_svg(packet)))).convert("RGBA")
        colors = image.getcolors(maxcolors=200_000)

        assert image.size == (528, 720), packet.id
        assert colors is not None, packet.id
        assert len(colors) > 10, packet.id
