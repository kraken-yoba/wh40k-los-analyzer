from hashlib import sha256
from pathlib import Path

import fitz
import pytest
from fortyk_los_backend.domain.extraction import extract_terrain_footprint_outlines

REPO_ROOT = Path(__file__).resolve().parents[3]
OFFICIAL_TERRAIN_FOOTPRINTS = REPO_ROOT / "data" / "pdfs" / "terrainareafootprints.pdf"
OFFICIAL_TERRAIN_FOOTPRINTS_SHA256 = (
    "abda484efe1e3031a92079053594a8b933a6ac429b899151f39ce8d51cbb9189"
)


def test_extract_terrain_footprint_outlines_from_synthetic_vector_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "synthetic-footprints.pdf"
    _write_synthetic_footprints_pdf(pdf_path)

    outlines = extract_terrain_footprint_outlines(pdf_path)

    assert len(outlines) == 1
    [outline] = outlines
    assert outline.footprint_id == "terrain-footprint-p1-01"
    assert outline.page_number == 1
    assert outline.bounds == pytest.approx((100.0, 100.0, 400.0, 420.0))
    assert outline.path_command_count == 1
    assert outline.point_count == 4


@pytest.mark.skipif(
    not OFFICIAL_TERRAIN_FOOTPRINTS.exists(),
    reason="official terrain footprint PDF is kept in the local gitignored cache",
)
def test_extract_terrain_footprint_outlines_from_cached_official_pdf() -> None:
    assert sha256(OFFICIAL_TERRAIN_FOOTPRINTS.read_bytes()).hexdigest() == (
        OFFICIAL_TERRAIN_FOOTPRINTS_SHA256
    )

    outlines = extract_terrain_footprint_outlines(OFFICIAL_TERRAIN_FOOTPRINTS)

    assert [(outline.page_number, outline.footprint_id) for outline in outlines] == [
        (1, "terrain-footprint-p1-01"),
        (1, "terrain-footprint-p1-02"),
        (2, "terrain-footprint-p2-01"),
        (2, "terrain-footprint-p2-02"),
        (3, "terrain-footprint-p3-01"),
    ]
    assert [outline.path_command_count for outline in outlines] == [60, 86, 52, 38, 71]
    assert [outline.point_count for outline in outlines] == [193, 246, 148, 111, 217]
    assert [outline.bounds for outline in outlines] == [
        pytest.approx((111.5, 74.9, 830.4, 340.7), abs=0.1),
        pytest.approx((288.8, 210.4, 1146.6, 784.0), abs=0.1),
        pytest.approx((216.6, 187.5, 530.8, 657.5), abs=0.1),
        pytest.approx((620.9, 333.1, 1051.5, 527.1), abs=0.1),
        pytest.approx((227.7, 131.3, 1052.8, 676.9), abs=0.1),
    ]


def _write_synthetic_footprints_pdf(pdf_path: Path) -> None:
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
        fitz.Point(20, 20),
        fitz.Point(35, 20),
        color=(0.0, 0.66, 0.31),
        width=2.0,
    )
    document.save(pdf_path)
