from __future__ import annotations

import json
import time
from collections.abc import Sequence
from os import PathLike
from pathlib import Path

from pydantic import BaseModel, Field
from shapely.geometry import Polygon

from warhammer_companion.domain.models import (
    BoardSize,
    DenseTerrainFeature,
    DeploymentZone,
    MapPacket,
    TerrainArea,
    TerrainKind,
)
from warhammer_companion.domain.packet_io import write_packet
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.footprints import (
    write_official_footprint_artifacts,
)
from warhammer_companion.ingestion.layouts import (
    ExtractedLayout,
    LayoutElement,
    write_official_layout_artifacts,
)

ReportPath = str | PathLike[str]
Point = tuple[float, float]

DEFAULT_INGESTION_REPORT_PATH = Path("data/processed/ingestion-report.json")


class PacketValidationResult(BaseModel):
    packet_id: str
    valid: bool
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class IngestionReport(BaseModel):
    schema_version: int = 1
    started_at_epoch: float
    duration_seconds: float
    source_footprint_pdf: str
    source_layout_pdf: str
    footprint_library_path: str
    layout_library_path: str
    map_packets_dir: str
    packet_count: int
    layout_count: int
    validation: list[PacketValidationResult]
    warnings: list[str] = Field(default_factory=list)


def build_map_packet(layout: ExtractedLayout) -> MapPacket:
    terrain_areas = [
        TerrainArea(
            id=_area_id(index),
            label=f"Terrain {index}",
            kind=TerrainKind.RUINS,
            footprint=_safe_points(area.footprint),
            blocks_los=True,
        )
        for index, area in enumerate(layout.terrain_areas, start=1)
    ]
    area_id_lookup = {
        source.id: packet_area.id
        for source, packet_area in zip(layout.terrain_areas, terrain_areas, strict=True)
    }
    dense_features = _dense_features(layout.terrain_features, area_id_lookup)
    deployment_zones = [
        DeploymentZone(
            id=_deployment_id(zone),
            label=_deployment_label(zone),
            footprint=_safe_points(zone.footprint),
        )
        for zone in layout.deployment_zones
    ]
    deployment_zones = sorted(deployment_zones, key=lambda zone: zone.id)

    return MapPacket(
        id=f"official-event-companion-page-{layout.source_page}",
        name=f"{layout.name} Page {layout.source_page}",
        source=f"Extracted from Event Companion page {layout.source_page}",
        board=BoardSize(
            width=layout.board_width_inches,
            height=layout.board_height_inches,
        ),
        terrain_areas=terrain_areas,
        dense_features=dense_features,
        deployment_zones=deployment_zones,
    )


def validate_packet(packet: MapPacket) -> PacketValidationResult:
    warnings: list[str] = []
    errors: list[str] = []
    board_is_positive = packet.board.width > 0 and packet.board.height > 0
    board = (
        Polygon(
            [
                (0.0, 0.0),
                (packet.board.width, 0.0),
                (packet.board.width, packet.board.height),
                (0.0, packet.board.height),
            ]
        )
        if board_is_positive
        else None
    )
    if not board_is_positive:
        errors.append("board dimensions must be positive")

    _check_unique("terrain area", [area.id for area in packet.terrain_areas], errors)
    _check_unique("dense feature", [feature.id for feature in packet.dense_features], errors)
    _check_unique("deployment zone", [zone.id for zone in packet.deployment_zones], errors)

    if {zone.id for zone in packet.deployment_zones} != {"attacker", "defender"}:
        errors.append("deployment zones must contain attacker and defender")
    if not packet.terrain_areas:
        errors.append("packet must contain at least one terrain area")

    terrain_ids = {area.id for area in packet.terrain_areas}
    for area in packet.terrain_areas:
        _validate_polygon(area.id, area.footprint, board, errors)
    for zone in packet.deployment_zones:
        _validate_polygon(zone.id, zone.footprint, board, errors)
    for feature in packet.dense_features:
        _validate_polygon(feature.id, feature.footprint, board, errors)
        if feature.terrain_area_id not in terrain_ids:
            errors.append(f"dense feature {feature.id} references unknown terrain area")

    if not packet.dense_features:
        warnings.append("packet has no dense feature blockers")

    return PacketValidationResult(
        packet_id=packet.id,
        valid=not errors,
        warnings=warnings,
        errors=errors,
    )


def run_official_ingestion(
    *,
    paths: IngestionPaths | None = None,
    layout_pages: Sequence[int] | None = None,
) -> IngestionReport:
    paths = paths or IngestionPaths()
    started = time.time()
    footprint_pdf = paths.raw_dir / "terrain-area-footprints.pdf"
    layout_pdf = paths.raw_dir / "event-companion.pdf"
    _require_file(footprint_pdf)
    _require_file(layout_pdf)

    footprint_library = write_official_footprint_artifacts(
        footprint_pdf,
        output_path=paths.footprint_library_path,
        review_dir=paths.footprint_review_dir,
    )
    layout_library = write_official_layout_artifacts(
        layout_pdf,
        output_path=paths.layout_library_path,
        review_dir=paths.layout_review_dir,
        pages=layout_pages,
    )
    packets = [build_map_packet(layout) for layout in layout_library.layouts]
    validation = [validate_packet(packet) for packet in packets]
    duration = time.time() - started
    report = IngestionReport(
        started_at_epoch=started,
        duration_seconds=duration,
        source_footprint_pdf=str(footprint_pdf),
        source_layout_pdf=str(layout_pdf),
        footprint_library_path=str(paths.footprint_library_path),
        layout_library_path=str(paths.layout_library_path),
        map_packets_dir=str(paths.map_packets_dir),
        packet_count=len(packets),
        layout_count=len(layout_library.layouts),
        validation=validation,
        warnings=_report_warnings(footprint_library.templates, layout_library.layouts, validation),
    )
    write_ingestion_report(report, paths.ingestion_report_path)

    invalid = [result for result in validation if not result.valid]
    if invalid:
        messages = "; ".join(f"{result.packet_id}: {result.errors}" for result in invalid)
        raise ValueError(f"Official ingestion produced invalid packets: {messages}")

    _remove_generated_official_packets(paths.map_packets_dir)
    for packet in packets:
        write_packet(packet, paths.map_packets_dir / f"{packet.id}.json")
    return report


def write_ingestion_report(
    report: IngestionReport,
    output_path: ReportPath = DEFAULT_INGESTION_REPORT_PATH,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _deployment_id(zone: LayoutElement) -> str:
    if zone.source_role in {"attacker", "defender"}:
        return zone.source_role
    centroid_y = zone.polygon().centroid.y
    return "attacker" if centroid_y > 30 else "defender"


def _deployment_label(zone: LayoutElement) -> str:
    zone_id = _deployment_id(zone)
    return "Attacker" if zone_id == "attacker" else "Defender"


def _dense_features(
    features: Sequence[LayoutElement],
    area_id_lookup: dict[str, str],
) -> list[DenseTerrainFeature]:
    dense_features: list[DenseTerrainFeature] = []
    for feature in features:
        if feature.feature_type != "dense" or feature.terrain_area_id is None:
            continue
        packet_area_id = area_id_lookup.get(feature.terrain_area_id)
        if packet_area_id is None:
            continue
        dense_index = len(dense_features) + 1
        dense_features.append(
            DenseTerrainFeature(
                id=f"{packet_area_id}-dense-{dense_index}",
                terrain_area_id=packet_area_id,
                label=f"Dense {dense_index}",
                footprint=_safe_points(feature.footprint),
                blocks_los=True,
            )
        )
    return dense_features


def _area_id(index: int) -> str:
    return f"terrain-{index:02d}"


def _safe_points(points: Sequence[Point]) -> list[Point]:
    return [(round(float(x), 6), round(float(y), 6)) for x, y in points]


def _check_unique(label: str, ids: Sequence[str], errors: list[str]) -> None:
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append(f"duplicate {label} ids: {duplicates}")


def _validate_polygon(
    label: str, points: Sequence[Point], board: Polygon | None, errors: list[str]
) -> None:
    if len(points) < 3:
        errors.append(f"{label} polygon has fewer than three points")
        return
    polygon = Polygon(points)
    if polygon.is_empty or not polygon.is_valid:
        errors.append(f"{label} polygon is invalid")
        return
    if polygon.area <= 0:
        errors.append(f"{label} polygon has zero area")
    if board is not None and not board.covers(polygon):
        errors.append(f"{label} polygon extends outside board")


def _report_warnings(
    footprint_templates: Sequence[object],
    layouts: Sequence[ExtractedLayout],
    validation: Sequence[PacketValidationResult],
) -> list[str]:
    warnings: list[str] = []
    warnings.append(
        "Dense/light feature extraction is raster-segmented and should be visually reviewed."
    )
    warnings.append(f"Extracted {len(footprint_templates)} terrain footprint templates.")
    for layout in layouts:
        warnings.extend(f"{layout.id}: {warning}" for warning in layout.warnings)
    for result in validation:
        warnings.extend(f"{result.packet_id}: {warning}" for warning in result.warnings)
    return warnings


def _remove_generated_official_packets(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.glob("official-event-companion-page-*.json"):
        path.unlink()


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required official source PDF is missing: {path}")
