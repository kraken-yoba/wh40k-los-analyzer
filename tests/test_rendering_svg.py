from __future__ import annotations

from warhammer_companion.rendering.svg import render_map_svg
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_los_base_renders_as_draggable_svg_element() -> None:
    svg = render_map_svg(SAMPLE_PACKETS[0], base_center=(22.0, 10.0), base_diameter=1.57)

    assert 'class="model-base"' in svg
    assert 'data-draggable-base="true"' in svg
    assert 'tabindex="0"' in svg
