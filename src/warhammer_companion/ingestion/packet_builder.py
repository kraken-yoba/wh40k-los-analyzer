from __future__ import annotations

import json
import time
from collections.abc import Sequence
from os import PathLike
from pathlib import Path

from pydantic import BaseModel, Field
from shapely.geometry import MultiPolygon, Polygon

from warhammer_companion.domain.models import (
    BoardSize,
    DenseTerrainFeature,
    DeploymentZone,
    LightTerrainFeature,
    MapPacket,
    TerrainArea,
    TerrainKind,
)
from warhammer_companion.domain.packet_io import write_packet
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.catalog_classifier import write_catalog_categorizer_results
from warhammer_companion.ingestion.feature_categorizer import (
    apply_layout_feature_categorizations_with_stats,
    load_feature_categorizations,
    write_visual_categorizer_request,
)
from warhammer_companion.ingestion.footprints import (
    write_official_footprint_artifacts,
)
from warhammer_companion.ingestion.layouts import (
    ExtractedLayout,
    LayoutElement,
    write_layout_library,
    write_official_layout_artifacts,
)

ReportPath = str | PathLike[str]
Point = tuple[float, float]

DEFAULT_INGESTION_REPORT_PATH = Path("data/processed/ingestion-report.json")
PACKET_POLYGON_SIMPLIFICATION_TOLERANCE = 0.5
RUIN_WALL_THICKNESS_INCHES = 0.75
NON_BLOCKING_DENSE_PROFILES = {"floor_or_platform"}
WALL_SIDE_PROFILES = {"ruined_wall_l", "ruined_wall_u", "ruined_wall_perimeter"}


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
    visual_categorizer_request_path: str | None = None
    visual_categorizer_results_path: str | None = None
    visual_categorizer_results_present: bool = False
    visual_categorizer_result_count: int = 0
    visual_categorizer_applied_count: int = 0
    visual_categorizer_unmatched_count: int = 0
    visual_categorizer_digest_mismatch_count: int = 0
    visual_categorizer_duplicate_conflict_count: int = 0
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
    light_features = _light_features(layout.terrain_features, area_id_lookup)
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
        light_features=light_features,
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
    _check_unique("light feature", [feature.id for feature in packet.light_features], errors)
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
    for dense_feature in packet.dense_features:
        _validate_polygon(dense_feature.id, dense_feature.footprint, board, errors)
        if dense_feature.terrain_area_id not in terrain_ids:
            errors.append(f"dense feature {dense_feature.id} references unknown terrain area")
    for light_feature in packet.light_features:
        _validate_polygon(light_feature.id, light_feature.footprint, board, errors)
        if light_feature.terrain_area_id not in terrain_ids:
            errors.append(f"light feature {light_feature.id} references unknown terrain area")
        if light_feature.blocks_los:
            errors.append(f"light feature {light_feature.id} must not block LOS")

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
    classify_features: bool = False,
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
    write_visual_categorizer_request(
        layout_library.layouts,
        paths.visual_categorizer_request_path,
        review_dir=paths.layout_review_dir,
    )
    if classify_features:
        write_catalog_categorizer_results(
            paths.visual_categorizer_request_path,
            paths.visual_categorizer_results_path,
        )
    categorizer_results_present = paths.visual_categorizer_results_path.exists()
    categorizations = load_feature_categorizations(paths.visual_categorizer_results_path)
    layouts = layout_library.layouts
    categorizer_warnings: list[str] = []
    categorizer_applied_count = 0
    categorizer_unmatched_count = 0
    categorizer_digest_mismatch_count = 0
    categorizer_duplicate_conflict_count = 0
    if categorizations:
        categorization_application = apply_layout_feature_categorizations_with_stats(
            layouts,
            categorizations,
        )
        layouts = categorization_application.layouts
        categorizer_applied_count = categorization_application.applied_count
        categorizer_unmatched_count = len(categorization_application.unmatched_feature_ids)
        categorizer_digest_mismatch_count = len(
            categorization_application.digest_mismatch_feature_ids
        )
        categorizer_duplicate_conflict_count = len(
            categorization_application.duplicate_conflict_feature_ids
        )
        layout_library = write_layout_library(
            layouts,
            paths.layout_library_path,
            source_pdf=str(layout_pdf),
        )
        if categorization_application.unmatched_feature_ids:
            categorizer_warnings.append(
                "Ignored unmatched visual categorizer result IDs: "
                + ", ".join(categorization_application.unmatched_feature_ids)
            )
        if categorization_application.low_confidence_feature_ids:
            categorizer_warnings.append(
                "Ignored low-confidence visual categorizer result IDs: "
                + ", ".join(categorization_application.low_confidence_feature_ids)
            )
        if categorization_application.digest_mismatch_feature_ids:
            categorizer_warnings.append(
                "Ignored stale visual categorizer result digests: "
                + ", ".join(categorization_application.digest_mismatch_feature_ids)
            )
        if categorization_application.duplicate_conflict_feature_ids:
            categorizer_warnings.append(
                "Ignored conflicting duplicate visual categorizer result IDs: "
                + ", ".join(categorization_application.duplicate_conflict_feature_ids)
            )
    else:
        categorizer_warnings.append(
            "Codex visual categorizer request written; no classifier results "
            "were present, so heuristic dense-feature profiles were used."
        )
    packets = [build_map_packet(layout) for layout in layouts]
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
        layout_count=len(layouts),
        validation=validation,
        visual_categorizer_request_path=str(paths.visual_categorizer_request_path),
        visual_categorizer_results_path=(
            str(paths.visual_categorizer_results_path) if categorizer_results_present else None
        ),
        visual_categorizer_results_present=categorizer_results_present,
        visual_categorizer_result_count=len(categorizations),
        visual_categorizer_applied_count=categorizer_applied_count,
        visual_categorizer_unmatched_count=categorizer_unmatched_count,
        visual_categorizer_digest_mismatch_count=categorizer_digest_mismatch_count,
        visual_categorizer_duplicate_conflict_count=categorizer_duplicate_conflict_count,
        warnings=_report_warnings(footprint_library.templates, layouts, validation)
        + categorizer_warnings,
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
        if feature.feature_profile in NON_BLOCKING_DENSE_PROFILES:
            continue
        for blocker_footprint in _dense_blocker_footprints(feature):
            dense_index = len(dense_features) + 1
            dense_features.append(
                DenseTerrainFeature(
                    id=f"{packet_area_id}-dense-{dense_index}",
                    terrain_area_id=packet_area_id,
                    label=f"Dense {dense_index}",
                    footprint=_safe_points(blocker_footprint),
                    profile=feature.feature_profile,
                    blocks_los=True,
                )
            )
    return dense_features


def _light_features(
    features: Sequence[LayoutElement],
    area_id_lookup: dict[str, str],
) -> list[LightTerrainFeature]:
    light_features: list[LightTerrainFeature] = []
    for feature in features:
        is_non_blocking_dense = feature.feature_profile in NON_BLOCKING_DENSE_PROFILES
        if (
            feature.feature_type != "light" and not is_non_blocking_dense
        ) or feature.terrain_area_id is None:
            continue
        packet_area_id = area_id_lookup.get(feature.terrain_area_id)
        if packet_area_id is None:
            continue
        light_index = len(light_features) + 1
        label_prefix = "Review" if is_non_blocking_dense else "Light"
        light_features.append(
            LightTerrainFeature(
                id=f"{packet_area_id}-light-{light_index}",
                terrain_area_id=packet_area_id,
                label=f"{label_prefix} {light_index}",
                footprint=_safe_points(feature.footprint),
                profile=feature.feature_profile,
                blocks_los=False,
            )
        )
    return light_features


def _dense_blocker_footprints(feature: LayoutElement) -> list[list[Point]]:
    if feature.feature_profile in WALL_SIDE_PROFILES and feature.feature_wall_sides:
        return _wall_strip_footprints(feature, sides=feature.feature_wall_sides)
    if feature.feature_profile == "ruined_wall_perimeter":
        return _wall_strip_footprints(feature, sides=("left", "right", "top", "bottom"))
    if feature.feature_profile == "ruined_wall_u":
        return _wall_strip_footprints(feature, sides=("left", "right", "top"))
    if feature.feature_profile == "ruined_wall_l":
        return _wall_strip_footprints(feature, sides=("left", "top"))
    return [_safe_points(feature.footprint)]


def _wall_strip_footprints(
    feature: LayoutElement,
    *,
    sides: Sequence[str],
) -> list[list[Point]]:
    polygon = Polygon(feature.footprint)
    if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
        return [_safe_points(feature.footprint)]

    min_x, min_y, max_x, max_y = polygon.bounds
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0:
        return [_safe_points(feature.footprint)]
    thickness = min(RUIN_WALL_THICKNESS_INCHES, width / 2.0, height / 2.0)
    strip_by_side = {
        "left": Polygon(
            [
                (min_x, min_y),
                (min_x + thickness, min_y),
                (min_x + thickness, max_y),
                (min_x, max_y),
            ]
        ),
        "right": Polygon(
            [
                (max_x - thickness, min_y),
                (max_x, min_y),
                (max_x, max_y),
                (max_x - thickness, max_y),
            ]
        ),
        "top": Polygon(
            [
                (min_x, max_y - thickness),
                (max_x, max_y - thickness),
                (max_x, max_y),
                (min_x, max_y),
            ]
        ),
        "bottom": Polygon(
            [
                (min_x, min_y),
                (max_x, min_y),
                (max_x, min_y + thickness),
                (min_x, min_y + thickness),
            ]
        ),
    }
    footprints: list[list[Point]] = []
    for side in sides:
        strip = strip_by_side[side].intersection(polygon)
        clipped = _largest_polygon(strip)
        if not clipped.is_empty and clipped.area > 0:
            footprints.append(_safe_points(_polygon_points(clipped)))
    return footprints or [_safe_points(feature.footprint)]


def _area_id(index: int) -> str:
    return f"terrain-{index:02d}"


def _safe_points(points: Sequence[Point]) -> list[Point]:
    polygon = Polygon(points)
    if not polygon.is_empty and polygon.is_valid and polygon.area > 0:
        simplified = polygon.simplify(
            PACKET_POLYGON_SIMPLIFICATION_TOLERANCE,
            preserve_topology=True,
        )
        if isinstance(simplified, Polygon) and not simplified.is_empty and simplified.area > 0:
            points = [(float(x), float(y)) for x, y in list(simplified.exterior.coords)[:-1]]
    return [(round(float(x), 6), round(float(y), 6)) for x, y in points]


def _polygon_points(polygon: Polygon) -> list[Point]:
    return [(float(x), float(y)) for x, y in list(polygon.exterior.coords)[:-1]]


def _largest_polygon(geometry: object) -> Polygon:
    if isinstance(geometry, Polygon):
        return geometry
    if isinstance(geometry, MultiPolygon) and geometry.geoms:
        return max(geometry.geoms, key=lambda polygon: polygon.area)
    return Polygon()


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
