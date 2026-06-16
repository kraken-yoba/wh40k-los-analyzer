import json
from hashlib import sha256
from pathlib import Path

import fitz
import pytest
from fortyk_los_backend.domain.extraction import (
    FootprintMatchStatus,
    TerrainFootprintTemplate,
    extract_event_companion_layout,
    extract_terrain_footprint_templates,
    generate_terrain_blockers_from_footprint_matches,
    match_terrain_features_to_footprints,
)
from fortyk_los_backend.domain.models import (
    BlockerKind,
    Board,
    CanonicalLayout,
    DeploymentZone,
    LayoutProvenance,
    Point,
    PolygonGeometry,
    TerrainCategory,
    TerrainFeature,
    ValidationStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
OFFICIAL_TERRAIN_FOOTPRINTS = REPO_ROOT / "data" / "pdfs" / "terrainareafootprints.pdf"
OFFICIAL_TERRAIN_FOOTPRINTS_SHA256 = (
    "abda484efe1e3031a92079053594a8b933a6ac429b899151f39ce8d51cbb9189"
)
OFFICIAL_TERRAIN_FOOTPRINT_TEMPLATE_EVIDENCE_SHA256 = (
    "fe4bc16bb9299d5eb52763a4937377b2c07c82e5fe92753a3031ee569fd0b2be"
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


def test_extract_terrain_footprint_templates_tessellates_cubic_fragments(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "synthetic-cubic-footprint-template.pdf"
    _write_cubic_fragment_template_pdf(pdf_path)

    templates = extract_terrain_footprint_templates(pdf_path)

    assert len(templates) == 1
    [fragment_path] = templates[0].normalized_fragment_paths
    rounded_points = _rounded_points(fragment_path)
    assert len(fragment_path) == 11
    assert rounded_points[0] == (0.1, 0.4)
    assert rounded_points[8] == (0.9, 0.4)
    assert rounded_points[-1] == (0.1, 0.4)
    assert (0.5, 0.47) in rounded_points
    assert (0.25, 0.19) not in rounded_points
    assert (0.75, 0.81) not in rounded_points


def test_terrain_footprint_template_preserves_ordered_outline_path(tmp_path: Path) -> None:
    pdf_path = tmp_path / "ordered-outline.pdf"
    _write_ordered_outline_pdf(pdf_path)

    [template] = extract_terrain_footprint_templates(pdf_path)

    assert template.outline_path_command_count == 5
    assert template.outline_point_count == 5
    assert len(template.normalized_outline_points) == 10
    assert template.normalized_outline_points[0] == template.normalized_outline_points[-1]
    assert template.normalized_outline_points[1] == template.normalized_outline_points[2]


def test_terrain_footprint_template_does_not_assign_crossing_fragment(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "crossing-fragment.pdf"
    _write_crossing_fragment_pdf(pdf_path)

    [template] = extract_terrain_footprint_templates(pdf_path)

    assert template.fragment_count == 0
    assert template.normalized_fragment_paths == ()


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
    assert [template.outline_point_count for template in templates] == [489, 631, 382, 285, 554]
    assert [template.fragment_count for template in templates] == [12, 14, 6, 6, 9]
    assert _template_evidence_digest(templates) == (
        OFFICIAL_TERRAIN_FOOTPRINT_TEMPLATE_EVIDENCE_SHA256
    )


def test_match_terrain_features_to_footprints_prefers_best_aspect_candidate() -> None:
    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="AB",
                footprint=_rectangle(10.0, 10.0, 20.0, 20.0),
                terrain_category=TerrainCategory.DENSE,
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
    assert match.rotation_degrees == 0


def test_match_terrain_features_to_footprints_records_reciprocal_orientation() -> None:
    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="AB",
                footprint=_rectangle(10.0, 10.0, 20.0, 30.0),
                terrain_category=TerrainCategory.DENSE,
            ),
        )
    )

    matches = match_terrain_features_to_footprints(
        layout,
        (_template("wide", aspect_ratio=2.0),),
    )

    assert matches[0].template_id == "wide"
    assert matches[0].rotation_degrees == 90
    assert matches[0].aspect_delta == pytest.approx(0.0)


def test_generate_terrain_blockers_from_footprint_matches_maps_fragments_to_board_inches() -> None:
    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="AB",
                footprint=_rectangle(10.0, 10.0, 20.0, 20.0),
                terrain_category=TerrainCategory.DENSE,
            ),
        )
    )
    templates = (
        _template(
            "square",
            aspect_ratio=1.0,
            fragments=((Point(x=0.25, y=0.25), Point(x=0.75, y=0.25)),),
        ),
    )
    matches = match_terrain_features_to_footprints(layout, templates)

    blockers = generate_terrain_blockers_from_footprint_matches(layout, templates, matches)

    assert len(blockers) == 1
    [blocker] = blockers
    assert blocker.blocker_id == "terrain-01-footprint-wall-01-01"
    assert blocker.feature_id == "terrain-01"
    assert blocker.kind == BlockerKind.WALL
    assert blocker.start.x == pytest.approx(12.5)
    assert blocker.start.y == pytest.approx(17.5)
    assert blocker.end.x == pytest.approx(17.5)
    assert blocker.end.y == pytest.approx(17.5)


def test_generate_terrain_blockers_from_footprint_matches_rotates_reciprocal_fragments() -> None:
    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="AB",
                footprint=_rectangle(10.0, 10.0, 20.0, 30.0),
                terrain_category=TerrainCategory.DENSE,
            ),
        )
    )
    templates = (
        _template(
            "wide",
            aspect_ratio=2.0,
            fragments=((Point(x=0.25, y=0.5), Point(x=0.75, y=0.5)),),
        ),
    )
    matches = match_terrain_features_to_footprints(layout, templates)

    blockers = generate_terrain_blockers_from_footprint_matches(layout, templates, matches)

    assert matches[0].rotation_degrees == 90
    assert len(blockers) == 1
    [blocker] = blockers
    assert blocker.start.x == pytest.approx(15.0)
    assert blocker.start.y == pytest.approx(15.0)
    assert blocker.end.x == pytest.approx(15.0)
    assert blocker.end.y == pytest.approx(25.0)


@pytest.mark.parametrize(
    "terrain_category",
    [TerrainCategory.LIGHT, TerrainCategory.UNKNOWN],
)
def test_generate_terrain_blockers_from_footprint_matches_skips_non_dense_features(
    terrain_category: TerrainCategory,
) -> None:
    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="AB",
                footprint=_rectangle(10.0, 10.0, 20.0, 20.0),
                terrain_category=terrain_category,
            ),
        )
    )
    templates = (
        _template(
            "square",
            aspect_ratio=1.0,
            fragments=((Point(x=0.25, y=0.25), Point(x=0.75, y=0.25)),),
        ),
    )
    matches = match_terrain_features_to_footprints(layout, templates)

    blockers = generate_terrain_blockers_from_footprint_matches(layout, templates, matches)

    assert blockers == ()


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


def test_match_terrain_features_to_footprints_ignores_invalid_aspect_templates() -> None:
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
        _template("zero", aspect_ratio=0.0),
        _template("negative", aspect_ratio=-1.0),
        _template("infinite", aspect_ratio=float("inf")),
        _template("nan", aspect_ratio=float("nan")),
        _template("valid", aspect_ratio=1.0),
    )

    matches = match_terrain_features_to_footprints(layout, templates)

    assert len(matches) == 1
    assert matches[0].template_id == "valid"
    assert matches[0].status == FootprintMatchStatus.CANDIDATE


def test_match_terrain_features_to_footprints_returns_no_matches_without_valid_templates() -> None:
    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="AB",
                footprint=_rectangle(10.0, 10.0, 20.0, 20.0),
            ),
        )
    )

    matches = match_terrain_features_to_footprints(
        layout,
        (_template("invalid", aspect_ratio=0.0),),
    )

    assert matches == ()


def test_match_terrain_features_to_footprints_marks_weak_aspect_for_review() -> None:
    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label="AB",
                footprint=_rectangle(10.0, 10.0, 20.0, 20.0),
            ),
        )
    )

    matches = match_terrain_features_to_footprints(
        layout,
        (_template("too-wide", aspect_ratio=8.0),),
    )

    assert matches[0].status == FootprintMatchStatus.NEEDS_REVIEW
    assert matches[0].review_reason == "weak_aspect_match"


@pytest.mark.parametrize("label", ["Terrain 01", "AB/CD"])
def test_match_terrain_features_to_footprints_marks_low_confidence_labels_for_review(
    label: str,
) -> None:
    layout = _layout_with_features(
        (
            TerrainFeature(
                feature_id="terrain-01",
                label=label,
                footprint=_rectangle(10.0, 10.0, 20.0, 20.0),
            ),
        )
    )

    matches = match_terrain_features_to_footprints(
        layout,
        (_template("square", aspect_ratio=1.0),),
    )

    assert matches[0].status == FootprintMatchStatus.NEEDS_REVIEW
    assert matches[0].review_reason == "low_confidence_feature_label"


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
    assert len(layout.blockers) > 0
    dense_feature_ids = {
        feature.feature_id
        for feature in layout.terrain_features
        if feature.terrain_category == TerrainCategory.DENSE
    }
    assert {blocker.feature_id for blocker in layout.blockers} <= dense_feature_ids
    assert layout.validation_status == ValidationStatus.WARNING
    assert any(match.status == FootprintMatchStatus.NEEDS_REVIEW for match in matches)
    record_codes = {record.code for record in layout.validation_records}
    assert "terrain_footprint_match_candidates" in record_codes
    assert "terrain_footprint_match_review_required" in record_codes
    assert "terrain_footprint_blocker_candidates" in record_codes
    assert "terrain_footprint_blocker_review_required" in record_codes


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


def _write_cubic_fragment_template_pdf(pdf_path: Path) -> None:
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
    shape = page.new_shape()
    shape.draw_bezier(
        fitz.Point(130, 228),
        fitz.Point(175, 160),
        fitz.Point(325, 360),
        fitz.Point(370, 228),
    )
    shape.finish(color=(0.0, 0.66, 0.31), width=2.0)
    shape.commit()
    document.save(pdf_path)


def _write_ordered_outline_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=500, height=500)
    shape = page.new_shape()
    shape.draw_polyline(
        [
            fitz.Point(100, 100),
            fitz.Point(300, 90),
            fitz.Point(410, 260),
            fitz.Point(320, 430),
            fitz.Point(110, 390),
            fitz.Point(100, 100),
        ]
    )
    shape.finish(color=(0.0, 0.66, 0.31), width=2.0)
    shape.commit()
    document.save(pdf_path)


def _write_crossing_fragment_pdf(pdf_path: Path) -> None:
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
        fitz.Point(50, 180),
        fitz.Point(250, 180),
        color=(0.0, 0.66, 0.31),
        width=2.0,
    )
    document.save(pdf_path)


def _template(
    template_id: str,
    *,
    aspect_ratio: float,
    fragments: tuple[tuple[Point, ...], ...] = (),
) -> TerrainFootprintTemplate:
    return TerrainFootprintTemplate(
        template_id=template_id,
        page_number=1,
        bounds=(0.0, 0.0, aspect_ratio * 100.0, 100.0),
        aspect_ratio=aspect_ratio,
        outline_path_command_count=4,
        outline_point_count=4,
        fragment_count=len(fragments),
        normalized_outline_points=(
            Point(x=0.0, y=0.0),
            Point(x=1.0, y=0.0),
            Point(x=1.0, y=1.0),
            Point(x=0.0, y=1.0),
        ),
        normalized_fragment_paths=fragments,
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


def _template_evidence_digest(templates: tuple[TerrainFootprintTemplate, ...]) -> str:
    payload = [
        {
            "aspect_ratio": round(template.aspect_ratio, 6),
            "bounds": [round(value, 3) for value in template.bounds],
            "fragment_count": template.fragment_count,
            "normalized_fragment_paths": [
                [_digest_point(point) for point in path]
                for path in template.normalized_fragment_paths
            ],
            "normalized_outline_points": [
                _digest_point(point) for point in template.normalized_outline_points
            ],
            "outline_path_command_count": template.outline_path_command_count,
            "outline_point_count": template.outline_point_count,
            "page_number": template.page_number,
            "template_id": template.template_id,
        }
        for template in templates
    ]
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return sha256(encoded).hexdigest()


def _digest_point(point: Point) -> list[float]:
    return [round(point.x, 6), round(point.y, 6)]
