from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.packet_io import load_packet_directory
from warhammer_companion.ingestion import packet_builder
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.layouts import (
    BLUE_DEPLOYMENT,
    DARK_STROKE,
    RED_DEPLOYMENT,
    TERRAIN_GREY,
    extract_layout_from_pdf,
)
from warhammer_companion.ingestion.packet_builder import (
    PacketValidationResult,
    build_map_packet,
    run_official_ingestion,
    validate_packet,
)


def test_build_map_packet_translates_layout_roles_and_dense_features(tmp_path: Path) -> None:
    layout = extract_layout_from_pdf(_synthetic_event_pdf(tmp_path), page_number=1, feature_dpi=72)

    packet = build_map_packet(layout)

    assert packet.id == "official-event-companion-page-1"
    assert {zone.id for zone in packet.deployment_zones} == {"attacker", "defender"}
    assert len(packet.terrain_areas) == 1
    assert len(packet.dense_features) == 1
    assert len(packet.light_features) == 1
    assert packet.dense_features[0].terrain_area_id == packet.terrain_areas[0].id
    assert packet.dense_features[0].profile == "container_or_solid"
    assert packet.light_features[0].terrain_area_id == packet.terrain_areas[0].id
    assert packet.light_features[0].profile == "light_area"
    assert not packet.light_features[0].blocks_los
    assert (
        packet.dense_features[0].polygon().bounds[0] >= packet.terrain_areas[0].polygon().bounds[0]
    )
    assert validate_packet(packet).valid


def test_build_map_packet_simplifies_high_vertex_polygons(tmp_path: Path) -> None:
    layout = extract_layout_from_pdf(
        _synthetic_event_pdf(tmp_path),
        page_number=1,
        feature_dpi=72,
    )
    original_area = layout.terrain_areas[0]
    dense_feature = next(
        feature for feature in layout.terrain_features if feature.feature_type == "dense"
    )
    high_vertex_area = original_area.model_copy(
        update={"footprint": _stair_step_rectangle(10.0, 10.0, 20.0, 20.0, steps=20)}
    )
    high_vertex_dense = dense_feature.model_copy(
        update={
            "footprint": _stair_step_rectangle(12.0, 12.0, 16.0, 16.0, steps=16),
            "terrain_area_id": high_vertex_area.id,
        }
    )
    high_vertex_layout = layout.model_copy(
        update={
            "terrain_areas": [high_vertex_area],
            "terrain_features": [high_vertex_dense],
        }
    )

    packet = build_map_packet(high_vertex_layout)

    assert len(packet.terrain_areas[0].footprint) < len(high_vertex_area.footprint)
    assert len(packet.dense_features[0].footprint) < len(high_vertex_dense.footprint)
    assert validate_packet(packet).valid


def test_validate_packet_rejects_missing_deployment_zone(
    tmp_path: Path,
) -> None:
    packet = build_map_packet(
        extract_layout_from_pdf(_synthetic_event_pdf(tmp_path), page_number=1)
    )
    broken = packet.model_copy(
        update={
            "deployment_zones": [zone for zone in packet.deployment_zones if zone.id == "attacker"]
        }
    )

    result = validate_packet(cast(MapPacket, broken))

    assert not result.valid
    assert "deployment zones must contain attacker and defender" in result.errors


def test_validate_packet_rejects_invalid_board_dimensions(
    tmp_path: Path,
) -> None:
    packet = build_map_packet(
        extract_layout_from_pdf(_synthetic_event_pdf(tmp_path), page_number=1)
    )
    broken = packet.model_copy(update={"board": packet.board.model_copy(update={"width": 0})})

    result = validate_packet(cast(MapPacket, broken))

    assert not result.valid
    assert "board dimensions must be positive" in result.errors


def test_validate_packet_reports_duplicate_ids_and_invalid_polygons(
    tmp_path: Path,
) -> None:
    packet = build_map_packet(
        extract_layout_from_pdf(_synthetic_event_pdf(tmp_path), page_number=1)
    )
    duplicate_zone = packet.deployment_zones[0].model_copy(update={"id": "attacker"})
    invalid_area = packet.terrain_areas[0].model_copy(
        update={"footprint": [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)]}
    )
    broken = packet.model_copy(
        update={
            "deployment_zones": [duplicate_zone, duplicate_zone],
            "terrain_areas": [invalid_area],
        }
    )

    result = validate_packet(cast(MapPacket, broken))

    assert not result.valid
    assert "duplicate deployment zone ids: ['attacker']" in result.errors
    assert f"{invalid_area.id} polygon is invalid" in result.errors


def test_run_official_ingestion_persists_packets_and_report(tmp_path: Path) -> None:
    paths = IngestionPaths(tmp_path / "data")
    paths.raw_dir.mkdir(parents=True)
    _synthetic_footprint_pdf(paths.raw_dir / "terrain-area-footprints.pdf")
    _synthetic_event_pdf(paths.raw_dir / "event-companion.pdf")

    report = run_official_ingestion(paths=paths, layout_pages=[1])

    packets = load_packet_directory(paths.map_packets_dir)
    assert report.packet_count == 1
    assert report.layout_count == 1
    assert report.validation[0].valid
    assert len(packets) == 1
    assert packets[0].id == "official-event-companion-page-1"
    assert paths.footprint_library_path.exists()
    assert paths.layout_library_path.exists()
    assert paths.ingestion_report_path.exists()
    assert (paths.layout_review_dir / "page-1.png").exists()


def test_run_official_ingestion_removes_stale_official_packets(tmp_path: Path) -> None:
    paths = IngestionPaths(tmp_path / "data")
    paths.raw_dir.mkdir(parents=True)
    paths.map_packets_dir.mkdir(parents=True)
    _synthetic_footprint_pdf(paths.raw_dir / "terrain-area-footprints.pdf")
    _synthetic_event_pdf(paths.raw_dir / "event-companion.pdf")
    (paths.map_packets_dir / "official-event-companion-page-99.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (paths.map_packets_dir / "custom-packet.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    report = run_official_ingestion(paths=paths, layout_pages=[1])

    assert report.packet_count == 1
    assert sorted(path.name for path in paths.map_packets_dir.glob("*.json")) == [
        "custom-packet.json",
        "official-event-companion-page-1.json",
    ]


def test_run_official_ingestion_writes_report_for_invalid_packets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = IngestionPaths(tmp_path / "data")
    paths.raw_dir.mkdir(parents=True)
    _synthetic_footprint_pdf(paths.raw_dir / "terrain-area-footprints.pdf")
    _synthetic_event_pdf(paths.raw_dir / "event-companion.pdf")

    def fail_validation(packet: MapPacket) -> PacketValidationResult:
        return PacketValidationResult(
            packet_id=packet.id,
            valid=False,
            errors=["forced invalid packet"],
        )

    monkeypatch.setattr(packet_builder, "validate_packet", fail_validation)

    with pytest.raises(ValueError, match="Official ingestion produced invalid packets"):
        run_official_ingestion(paths=paths, layout_pages=[1])

    report = json.loads(paths.ingestion_report_path.read_text(encoding="utf-8"))
    assert report["packet_count"] == 1
    assert report["validation"][0]["valid"] is False
    assert report["validation"][0]["errors"] == ["forced invalid packet"]


def _synthetic_event_pdf(tmp_path: Path | str) -> Path:
    if isinstance(tmp_path, Path) and tmp_path.suffix == ".pdf":
        pdf_path = tmp_path
    else:
        pdf_path = Path(tmp_path) / "event-companion.pdf"
    fitz = _fitz()
    document = fitz.open()
    page = document.new_page(width=600, height=500)
    page.insert_text((40, 40), "LAYOUT Z", fontsize=16)
    page.draw_rect(fitz.Rect(100, 100, 320, 400), color=DARK_STROKE, width=2.4)
    page.draw_rect(fitz.Rect(100, 100, 320, 200), color=None, fill=RED_DEPLOYMENT)
    page.draw_rect(fitz.Rect(100, 340, 320, 400), color=None, fill=BLUE_DEPLOYMENT)
    page.draw_rect(fitz.Rect(150, 250, 210, 310), color=DARK_STROKE, fill=TERRAIN_GREY, width=0.3)
    page.draw_rect(fitz.Rect(160, 280, 180, 300), color=None, fill=(0.0, 0.452, 0.378))
    page.draw_rect(fitz.Rect(185, 280, 200, 295), color=None, fill=(148 / 255, 112 / 255, 29 / 255))
    document.save(pdf_path)
    document.close()
    return pdf_path


def _synthetic_footprint_pdf(pdf_path: Path) -> None:
    fitz = _fitz()
    document = fitz.open()
    page = document.new_page(width=360, height=240)
    shape = page.new_shape()
    shape.draw_polyline(
        [
            fitz.Point(72, 72),
            fitz.Point(216, 72),
            fitz.Point(216, 144),
            fitz.Point(72, 144),
        ]
    )
    shape.finish(color=(0.0, 0.665, 0.309), width=2, closePath=True)
    shape.commit()
    document.save(pdf_path)
    document.close()


def _stair_step_rectangle(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    *,
    steps: int,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for index in range(steps + 1):
        x = min_x + (max_x - min_x) * index / steps
        y = min_y + (0.08 if index % 2 else 0.0)
        points.append((x, y))
    for index in range(1, steps + 1):
        y = min_y + (max_y - min_y) * index / steps
        x = max_x + (0.08 if index % 2 else 0.0)
        points.append((x, y))
    for index in range(1, steps + 1):
        x = max_x - (max_x - min_x) * index / steps
        y = max_y + (0.08 if index % 2 else 0.0)
        points.append((x, y))
    for index in range(1, steps):
        y = max_y - (max_y - min_y) * index / steps
        x = min_x + (0.08 if index % 2 else 0.0)
        points.append((x, y))
    return points


def _fitz() -> Any:
    return cast(Any, importlib.import_module("fitz"))
