from hashlib import sha256
from pathlib import Path

import fitz
import pytest
from fortyk_los_backend.domain.extraction import (
    FootprintMatchStatus,
    TerrainFootprintTemplate,
    extract_event_companion_layout,
    extract_terrain_footprint_templates,
    match_terrain_features_to_footprints,
)
from fortyk_los_backend.domain.models import (
    Board,
    CanonicalLayout,
    DeploymentZone,
    LayoutProvenance,
    Point,
    PolygonGeometry,
    TerrainFeature,
    ValidationStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
OFFICIAL_TERRAIN_FOOTPRINTS = REPO_ROOT / "data" / "pdfs" / "terrainareafootprints.pdf"
OFFICIAL_TERRAIN_FOOTPRINTS_SHA256 = (
    "abda484efe1e3031a92079053594a8b933a6ac429b899151f39ce8d51cbb9189"
)
OFFICIAL_EVENT_COMPANION = REPO_ROOT / "data" / "pdfs" / "event_companion.pdf"
OFFICIAL_EVENT_COMPANION_SHA256 = (
    "0e26f6586929e7ec4c50c6a17d240ed794bb7b6c654d1d9664fb908abc606a19"
)


def test_extract_terrain_footprint_templates_from_synthetic_vector_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "synthetic-footprint-templates.pdf"
    _write_synthetic_template_pdf(pdf_path)

    templates = extract_terrain_footprint_templates(pdf_path)

    assert len(templates) == 1
    [template] = templates
    assert template.template_id == "terrain-footprint-p1-01"
    assert template.page_number == 1
    assert template.bounds == pytest.approx((100.0, 100.0, 400.0, 420.0))
    assert template.aspect_ratio == pytest.approx(0.9375)
    assert template.outline_path_command_count == 1
    assert template.outline_point_count == 4
    assert template.fragment_count == 1
    assert _rounded_points(template.normalized_outline_points) == [
        (0.0, 0.0),
        (0.0, 1.0),
        (1.0, 0.0),
        (1.0, 1.0),
    ]
    assert [_rounded_points(path) for path in template.normalized_fragment_paths] == [
        [(0.25, 0.25), (0.75, 0.25)]
    ]


@pytest.mark.skipif(
    not OFFICIAL_TERRAIN_FOOTPRINTS.exists(),
    reason="official terrain footprint PDF is kept in the local gitignored cache",
)
def test_extract_terrain_footprint_templates_from_cached_official_pdf() -> None:
    assert sha256(OFFICIAL_TERRAIN_FOOTPRINTS.read_bytes()).hexdigest() == (
        OFFICIAL_TERRAIN_FOOTPRINTS_SHA256
    )

    templates = extract_terrain_footprint_templates(OFFICIAL_TERRAIN_FOOTPRINTS)

    assert [template.template_id for template in templates] == [
        "terrain-footprint-p1-01",
        "terrain-footprint-p1-02",
        "terrain-footprint-p2-01",
        "terrain-footprint-p2-02",
        "terrain-footprint-p3-01",
    ]
    assert [round(template.aspect_ratio, 3) for template in templates] == [
        2.705,
        1.495,
        0.668,
        2.22,
        1.512,
    ]
    assert [template.outline_path_command_count for template in templates] == [60, 86, 52, 38, 71]
    assert [template.outline_point_count for template in templates] == [193, 246, 148, 111, 217]
    assert [template.fragment_count for template in templates] == [12, 14, 6, 6, 9]


def test_match_terrain_features_to_footprints_prefers_best_aspect_candidate() -> None:
    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="AB",
                footprint=_rectangle(10.0, 10.0, 20.0, 20.0),
            ),
        )
    )
    templates = (
        _template("wide", aspect_ratio=2.0),
        _template("square", aspect_ratio=1.0),
    )

    matches = match_terrain_features_to_footprints(layout, templates)

    assert len(matches) == 1
    [match] = matches
    assert match.feature_id == "terrain-01"
    assert match.template_id == "square"
    assert match.status == FootprintMatchStatus.CANDIDATE
    assert match.aspect_delta == pytest.approx(0.0)


def test_match_terrain_features_to_footprints_marks_close_scores_for_review() -> None:
    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="AB",
                footprint=_rectangle(10.0, 10.0, 20.1, 20.0),
            ),
        )
    )
    templates = (
        _template("template-a", aspect_ratio=1.0),
        _template("template-b", aspect_ratio=1.02),
    )

    matches = match_terrain_features_to_footprints(layout, templates)

    assert matches[0].status == FootprintMatchStatus.NEEDS_REVIEW
    assert matches[0].review_reason == "ambiguous_template_score"


@pytest.mark.skipif(
    not (OFFICIAL_TERRAIN_FOOTPRINTS.exists() and OFFICIAL_EVENT_COMPANION.exists()),
    reason="official PDFs are kept in the local gitignored cache",
)
def test_official_page_9_gets_provisional_matches_but_stays_blocked() -> None:
    assert sha256(OFFICIAL_TERRAIN_FOOTPRINTS.read_bytes()).hexdigest() == (
        OFFICIAL_TERRAIN_FOOTPRINTS_SHA256
    )
    assert sha256(OFFICIAL_EVENT_COMPANION.read_bytes()).hexdigest() == (
        OFFICIAL_EVENT_COMPANION_SHA256
    )
    templates = extract_terrain_footprint_templates(OFFICIAL_TERRAIN_FOOTPRINTS)

    layout = extract_event_companion_layout(
        OFFICIAL_EVENT_COMPANION,
        page_number=9,
        footprint_templates=templates,
    )
    matches = match_terrain_features_to_footprints(layout, templates)

    assert len(matches) == len(layout.terrain_features)
    assert layout.blockers == ()
    assert layout.validation_status == ValidationStatus.WARNING
    assert any(match.status == FootprintMatchStatus.NEEDS_REVIEW for match in matches)
    record_codes = {record.code for record in layout.validation_records}
    assert "terrain_footprint_match_candidates" in record_codes
    assert "terrain_footprint_match_review_required" in record_codes


def _write_synthetic_template_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=500, height=500)
    shape = page.new_shape()
    shape.draw_polyline(
        [
            fitz.Point(100, 100),
            fitz.Point(400, 100),
            fitz.Point(400, 420),
            fitz.Point(100, 420),
            fitz.Point(100, 100),
        ]
    )
    shape.finish(color=(0.0, 0.66, 0.31), width=2.0)
    shape.commit()
    page.draw_line(
        fitz.Point(175, 180),
        fitz.Point(325, 180),
        color=(0.0, 0.66, 0.31),
        width=2.0,
    )
    page.draw_line(
        fitz.Point(20, 20),
        fitz.Point(35, 20),
        color=(0.0, 0.66, 0.31),
        width=2.0,
    )
    document.save(pdf_path)


def _template(template_id: str, *, aspect_ratio: float) -> TerrainFootprintTemplate:
    return TerrainFootprintTemplate(
        template_id=template_id,
        page_number=1,
        bounds=(0.0, 0.0, aspect_ratio * 100.0, 100.0),
        aspect_ratio=aspect_ratio,
        outline_path_command_count=4,
        outline_point_count=4,
        fragment_count=0,
        normalized_outline_points=(
            Point(x=0.0, y=0.0),
            Point(x=1.0, y=0.0),
            Point(x=1.0, y=1.0),
            Point(x=0.0, y=1.0),
        ),
        normalized_fragment_paths=(),
    )


def _layout_with_features(features: tuple[TerrainFeature, ...]) -> CanonicalLayout:
    return CanonicalLayout(
        layout_id="synthetic-match-layout",
        name="Synthetic Match Layout",
        board=Board(width=44.0, height=60.0),
        terrain_features=features,
        blockers=(),
        deployments=(
            DeploymentZone(
                zone_id="attacker",
                label="Attacker",
                area=_rectangle(0.0, 0.0, 44.0, 10.0),
            ),
        ),
        provenance=LayoutProvenance(
            source_document_id="synthetic",
            source_page=1,
            extraction_method="synthetic",
        ),
        validation_status=ValidationStatus.PASSED,
    )


def _rectangle(x_min: float, y_min: float, x_max: float, y_max: float) -> PolygonGeometry:
    return PolygonGeometry(
        points=(
            Point(x=x_min, y=y_min),
            Point(x=x_max, y=y_min),
            Point(x=x_max, y=y_max),
            Point(x=x_min, y=y_max),
        )
    )


def _rounded_points(points: tuple[Point, ...]) -> list[tuple[float, float]]:
    return [(round(point.x, 2), round(point.y, 2)) for point in points]
