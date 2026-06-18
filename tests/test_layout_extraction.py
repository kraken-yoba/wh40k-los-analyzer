from __future__ import annotations

import importlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, cast

import pytest
from PIL import Image

from warhammer_companion.ingestion.coordinates import BoardTransform
from warhammer_companion.ingestion.layouts import (
    BLUE_DEPLOYMENT,
    DARK_STROKE,
    DEFAULT_LAYOUT_END_PAGE,
    DEFAULT_LAYOUT_START_PAGE,
    RED_DEPLOYMENT,
    TERRAIN_GREY,
    LayoutElement,
    detect_board_rect,
    extract_layout_from_pdf,
    write_layout_library,
    write_layout_review_overlay,
    write_official_layout_artifacts,
)
from warhammer_companion.ingestion.official_features import extract_official_feature_labels


def test_detect_board_rect_selects_dark_44_by_60_rectangle(tmp_path: Path) -> None:
    pdf_path = _synthetic_layout_pdf(tmp_path)
    fitz = _fitz()
    document = fitz.open(pdf_path)
    try:
        board_rect = detect_board_rect(document[0].get_drawings())
    finally:
        document.close()

    assert board_rect == pytest.approx((100.0, 100.0, 320.0, 400.0))


def test_extract_layout_from_pdf_returns_board_coordinate_geometry(tmp_path: Path) -> None:
    pdf_path = _synthetic_layout_pdf(tmp_path)

    layout = extract_layout_from_pdf(pdf_path, page_number=1, feature_dpi=72)

    assert layout.id == "official-layout-page-1"
    assert layout.layout_code == "Z"
    assert layout.board_rect == pytest.approx((100.0, 100.0, 320.0, 400.0))
    assert len(layout.deployment_zones) == 2
    assert len(layout.terrain_areas) == 1
    assert len(layout.terrain_features) == 2
    assert layout.deployment_zones[0].polygon().bounds == pytest.approx((0.0, 40.0, 44.0, 60.0))
    assert layout.deployment_zones[1].polygon().bounds == pytest.approx((0.0, 0.0, 44.0, 12.0))
    assert {zone.source_role for zone in layout.deployment_zones} == {"attacker", "defender"}
    assert {zone.id for zone in layout.deployment_zones} == {"page-1-attacker", "page-1-defender"}
    assert layout.terrain_areas[0].polygon().bounds == pytest.approx((10.0, 18.0, 22.0, 30.0))
    assert layout.terrain_features[0].polygon().bounds == pytest.approx(
        (12.0, 20.0, 16.0, 24.0),
        abs=0.25,
    )
    assert layout.terrain_features[0].feature_type == "dense"
    assert layout.terrain_features[0].feature_profile == "container_or_solid"
    assert layout.terrain_features[1].feature_type == "light"
    assert layout.terrain_features[1].feature_profile == "light_area"
    assert layout.terrain_features[0].terrain_area_id == layout.terrain_areas[0].id
    assert layout.terrain_features[1].terrain_area_id == layout.terrain_areas[0].id
    assert "heuristic-dense-profile:container_or_solid" in layout.terrain_features[0].warnings
    assert "raster-light-segmentation" in layout.terrain_features[1].warnings


def test_extract_layout_from_pdf_uses_official_feature_labels_for_dense_templates(
    tmp_path: Path,
) -> None:
    pdf_path = _synthetic_layout_pdf(tmp_path, include_official_feature_label=True)

    layout = extract_layout_from_pdf(pdf_path, page_number=1, feature_dpi=72)

    dense_features = [
        feature for feature in layout.terrain_features if feature.feature_type == "dense"
    ]
    assert len(dense_features) == 1
    assert dense_features[0].official_feature_code == "AB"
    assert dense_features[0].feature_profile == "ruined_wall_l"
    assert dense_features[0].feature_wall_sides is not None
    assert dense_features[0].terrain_area_id == layout.terrain_areas[0].id
    assert "official-feature-code:AB" in dense_features[0].warnings
    assert "official-feature-anchor:raster-dense" in dense_features[0].warnings
    assert "raster-dense-segmentation" not in dense_features[0].warnings


def test_official_feature_labels_are_extracted_from_individual_words() -> None:
    transform = BoardTransform((0.0, 0.0, 100.0, 100.0), 100.0, 100.0)
    terrain_area = LayoutElement(
        id="area-1",
        label="Area 1",
        kind="terrain_area",
        footprint=[(0.0, 0.0), (40.0, 0.0), (40.0, 40.0), (0.0, 40.0)],
        source_page=1,
        source_bbox=(0.0, 60.0, 40.0, 100.0),
    )
    page = _FakeWordPage(
        [
            (9.0, 79.0, 11.0, 81.0, "EF", 0, 0, 0),
            (19.0, 79.0, 21.0, 81.0, "CD", 0, 0, 1),
        ]
    )

    features = extract_official_feature_labels(
        page,
        transform,
        [terrain_area],
        source_page=1,
        element_factory=LayoutElement,
    )

    assert Counter(feature.official_feature_code for feature in features) == {
        "CD": 1,
        "EF": 1,
    }
    assert all(feature.terrain_area_id == terrain_area.id for feature in features)


def test_synthetic_rotated_official_feature_template_follows_rotated_terrain_area() -> None:
    transform = BoardTransform((0.0, 0.0, 100.0, 100.0), 100.0, 100.0)
    center = (30.0, 30.0)
    angle = math.radians(35.0)
    x_axis = (math.cos(angle), math.sin(angle))
    y_axis = (-x_axis[1], x_axis[0])
    terrain_area = LayoutElement(
        id="area-rotated",
        label="Rotated Area",
        kind="terrain_area",
        footprint=_oriented_rectangle(center, x_axis, y_axis, 18.0, 10.0),
        source_page=1,
        source_bbox=(0.0, 0.0, 100.0, 100.0),
    )
    image_center = (center[0], 100.0 - center[1])
    page = _FakeWordPage(
        [
            (
                image_center[0] - 1.0,
                image_center[1] - 1.0,
                image_center[0] + 1.0,
                image_center[1] + 1.0,
                "AB",
                0,
                0,
                0,
            )
        ]
    )

    features = extract_official_feature_labels(
        page,
        transform,
        [terrain_area],
        source_page=1,
        element_factory=LayoutElement,
    )

    assert len(features) == 1
    assert (
        _angle_delta(
            _major_axis_angle_degrees(features[0].polygon()),
            _major_axis_angle_degrees(terrain_area.polygon()),
        )
        < 10.0
    )


def test_deployment_roles_follow_colour_not_drawing_order(tmp_path: Path) -> None:
    pdf_path = _synthetic_layout_pdf(tmp_path, reverse_deployment_order=True)

    layout = extract_layout_from_pdf(pdf_path, page_number=1, feature_dpi=72)

    roles_by_bottom = {
        round(zone.polygon().bounds[1], 1): zone.source_role for zone in layout.deployment_zones
    }
    assert roles_by_bottom[40.0] == "attacker"
    assert roles_by_bottom[0.0] == "defender"
    assert {zone.id for zone in layout.deployment_zones} == {"page-1-attacker", "page-1-defender"}
    assert {zone.label for zone in layout.deployment_zones} == {"Attacker", "Defender"}


def test_extract_layout_ignores_matching_colours_outside_board(tmp_path: Path) -> None:
    pdf_path = _synthetic_layout_pdf(tmp_path)

    layout = extract_layout_from_pdf(pdf_path, page_number=1, feature_dpi=72)

    assert all(element.source_bbox[1] >= 100 for element in layout.terrain_areas)
    assert all(element.source_bbox[1] >= 100 for element in layout.deployment_zones)


def test_write_layout_library_persists_extracted_layout(tmp_path: Path) -> None:
    pdf_path = _synthetic_layout_pdf(tmp_path)
    layout = extract_layout_from_pdf(pdf_path, page_number=1, feature_dpi=72)
    output_path = tmp_path / "processed" / "layout-library.json"

    library = write_layout_library([layout], output_path, source_pdf="official.pdf")

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert library.output_path == str(output_path)
    assert payload["schema_version"] == 1
    assert payload["source_pdf"] == "official.pdf"
    assert payload["layouts"][0]["deployment_zones"][0]["kind"] == "deployment"


def test_write_layout_review_overlay_draws_extracted_geometry(tmp_path: Path) -> None:
    pdf_path = _synthetic_layout_pdf(tmp_path)
    layout = extract_layout_from_pdf(pdf_path, page_number=1, feature_dpi=72)
    overlay_path = tmp_path / "review" / "page-1.png"

    write_layout_review_overlay(Image.new("RGB", (600, 500), "white"), layout, overlay_path)

    assert overlay_path.exists()
    assert Image.open(overlay_path).size == (600, 500)


def test_write_official_layout_artifacts_uses_selected_pages(tmp_path: Path) -> None:
    pdf_path = _synthetic_layout_pdf(tmp_path)
    output_path = tmp_path / "layout-library.json"
    review_dir = tmp_path / "review"

    library = write_official_layout_artifacts(
        pdf_path,
        output_path=output_path,
        review_dir=review_dir,
        pages=[1],
        dpi=72,
    )

    assert output_path.exists()
    assert len(library.layouts) == 1
    assert (review_dir / "page-1.png").exists()


def test_official_layout_page9_smoke_when_source_pdf_is_available() -> None:
    pdf_path = Path("data/raw/event-companion.pdf")
    if not pdf_path.exists():
        pytest.skip("official Event Companion PDF is not available")

    layout = extract_layout_from_pdf(pdf_path, page_number=9)

    assert layout.layout_code == "A"
    assert layout.official_metadata is not None
    assert layout.official_metadata.first_player.force_disposition == "Take and Hold"
    assert layout.official_metadata.second_player.force_disposition == "Take and Hold"
    assert layout.official_metadata.layout_variant == "A"
    assert layout.board_rect == pytest.approx((127.99, 277.77, 468.15, 740.18), abs=0.2)
    assert len(layout.deployment_zones) == 2
    assert len(layout.terrain_areas) == 16
    official_codes = {
        feature.official_feature_code
        for feature in layout.terrain_features
        if feature.official_feature_code is not None
    }
    dense_count = sum(feature.feature_type == "dense" for feature in layout.terrain_features)
    light_count = sum(feature.feature_type == "light" for feature in layout.terrain_features)
    dense_profiles = {
        feature.feature_profile
        for feature in layout.terrain_features
        if feature.feature_type == "dense"
    }
    assert dense_count > 0
    assert light_count > 0
    assert dense_profiles <= {
        "ruined_wall_l",
        "ruined_wall_section",
        "container_or_solid",
        "solid_los_blocker",
        "unknown_dense",
    }
    assert "ruined_wall_l" in dense_profiles
    assert official_codes == {"AB", "CD", "EF", "GH"}
    cd_features = [
        feature for feature in layout.terrain_features if feature.official_feature_code == "CD"
    ]
    assert cd_features
    assert {feature.feature_profile for feature in cd_features} == {"ruined_wall_l"}
    terrain_by_ordinal = dict(enumerate(layout.terrain_areas, start=1))
    central_group = terrain_by_ordinal[3].terrain_group_id
    assert central_group is not None
    assert terrain_by_ordinal[7].terrain_group_id == central_group
    assert terrain_by_ordinal[11].terrain_group_id == central_group
    assert terrain_by_ordinal[14].terrain_group_id == terrain_by_ordinal[15].terrain_group_id
    assert terrain_by_ordinal[14].terrain_group_id is not None
    assert terrain_by_ordinal[16].terrain_group_id is None
    assert terrain_by_ordinal[1].terrain_group_id is None
    assert terrain_by_ordinal[5].terrain_group_id is None
    assert terrain_by_ordinal[12].terrain_group_id is None
    assert not layout.warnings


def test_official_layout_page20_extracts_word_level_feature_labels() -> None:
    pdf_path = Path("data/raw/event-companion.pdf")
    if not pdf_path.exists():
        pytest.skip("official Event Companion PDF is not available")

    layout = extract_layout_from_pdf(pdf_path, page_number=20)

    official_code_counts = Counter(
        feature.official_feature_code
        for feature in layout.terrain_features
        if feature.official_feature_code is not None
    )
    assert official_code_counts == {"AB": 2, "CD": 2, "EF": 2, "GH": 2}


def test_official_layout_page52_rotated_feature_templates_follow_terrain_footprint() -> None:
    pdf_path = Path("data/raw/event-companion.pdf")
    if not pdf_path.exists():
        pytest.skip("official Event Companion PDF is not available")

    layout = extract_layout_from_pdf(pdf_path, page_number=52)
    terrain_by_ordinal = dict(enumerate(layout.terrain_areas, start=1))

    for terrain_ordinal, official_code in ((15, "AB"), (16, "EF")):
        terrain_area = terrain_by_ordinal[terrain_ordinal]
        feature = next(
            feature
            for feature in layout.terrain_features
            if feature.terrain_area_id == terrain_area.id
            and feature.official_feature_code == official_code
        )
        assert (
            _angle_delta(
                _major_axis_angle_degrees(feature.polygon()),
                _major_axis_angle_degrees(terrain_area.polygon()),
            )
            < 10.0
        )


def test_default_layout_page_range_constants_are_current_mvp_range() -> None:
    assert DEFAULT_LAYOUT_START_PAGE == 9
    assert DEFAULT_LAYOUT_END_PAGE == 53


def _synthetic_layout_pdf(
    tmp_path: Path,
    *,
    reverse_deployment_order: bool = False,
    include_official_feature_label: bool = False,
) -> Path:
    pdf_path = tmp_path / "layout.pdf"
    fitz = _fitz()
    document = fitz.open()
    page = document.new_page(width=600, height=500)
    page.insert_text((40, 40), "LAYOUT Z", fontsize=16)
    board = fitz.Rect(100, 100, 320, 400)
    page.draw_rect(board, color=DARK_STROKE, width=2.4)
    deployments = [
        (fitz.Rect(100, 100, 320, 200), RED_DEPLOYMENT),
        (fitz.Rect(100, 340, 320, 400), BLUE_DEPLOYMENT),
    ]
    if reverse_deployment_order:
        deployments.reverse()
    for rect, fill in deployments:
        page.draw_rect(rect, color=None, fill=fill)
    page.draw_rect(fitz.Rect(150, 250, 210, 310), color=DARK_STROKE, fill=TERRAIN_GREY, width=0.3)
    page.draw_rect(
        fitz.Rect(160, 280, 180, 300),
        color=None,
        fill=(0.0, 0.452, 0.378),
    )
    page.draw_rect(
        fitz.Rect(185, 280, 200, 295),
        color=None,
        fill=(148 / 255, 112 / 255, 29 / 255),
    )
    if include_official_feature_label:
        page.insert_text((170, 270), "AB", fontsize=10)
    page.draw_rect(fitz.Rect(15, 15, 60, 60), color=None, fill=TERRAIN_GREY)
    document.save(pdf_path)
    document.close()
    return pdf_path


class _FakeWordPage:
    def __init__(self, words: list[tuple[float, float, float, float, str, int, int, int]]) -> None:
        self._words = words

    def get_text(self, mode: str) -> list[tuple[float, float, float, float, str, int, int, int]]:
        assert mode == "words"
        return self._words


def _oriented_rectangle(
    center: tuple[float, float],
    x_axis: tuple[float, float],
    y_axis: tuple[float, float],
    width: float,
    height: float,
) -> list[tuple[float, float]]:
    half_width = width / 2.0
    half_height = height / 2.0
    offsets = [
        (-half_width, -half_height),
        (half_width, -half_height),
        (half_width, half_height),
        (-half_width, half_height),
    ]
    return [
        (
            center[0] + x_axis[0] * x_offset + y_axis[0] * y_offset,
            center[1] + x_axis[1] * x_offset + y_axis[1] * y_offset,
        )
        for x_offset, y_offset in offsets
    ]


def _major_axis_angle_degrees(polygon) -> float:
    rectangle = polygon.minimum_rotated_rectangle
    coords = list(rectangle.exterior.coords)[:-1]
    edges: list[tuple[float, float, float]] = []
    for index, start in enumerate(coords):
        end = coords[(index + 1) % len(coords)]
        dx = float(end[0] - start[0])
        dy = float(end[1] - start[1])
        length = (dx * dx + dy * dy) ** 0.5
        edges.append((length, dx, dy))
    _, dx, dy = max(edges, key=lambda edge: edge[0])
    angle = math.degrees(math.atan2(dy, dx)) % 180.0
    return angle


def _angle_delta(left: float, right: float) -> float:
    delta = abs(left - right) % 180.0
    return min(delta, 180.0 - delta)


def _fitz() -> Any:
    return cast(Any, importlib.import_module("fitz"))
