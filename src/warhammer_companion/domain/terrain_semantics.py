from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from shapely.geometry.base import BaseGeometry as ShapelyGeometry

from warhammer_companion.domain.board_state import map_packet_digest
from warhammer_companion.domain.models import (
    DenseTerrainFeature,
    LightTerrainFeature,
    MapPacket,
    TerrainArea,
)
from warhammer_companion.domain.overlays import (
    ToolkitAssumption,
    ToolkitReadiness,
    ToolkitWarning,
)
from warhammer_companion.domain.semantics import (
    FieldSourceRef,
    SemanticsBlockReason,
    SemanticsCompatibilityState,
    SemanticsFreshnessState,
    SemanticsReadinessReport,
    SemanticsValidationRecord,
    field_source_ref_ids,
    report_semantics_readiness,
)

TerrainElementKind = Literal["terrain_area", "dense_feature", "light_feature"]


@dataclass(frozen=True, slots=True)
class TerrainSemanticsRecord:
    record_id: str
    packet_id: str
    packet_digest: str
    element_kind: TerrainElementKind
    element_id: str
    label: str
    geometry: ShapelyGeometry
    blocks_los_2d: bool
    terrain_area_id: str | None = None
    terrain_kind: str | None = None
    profile: str | None = None
    visibility_traits: tuple[str, ...] = ()
    movement_traits: tuple[str, ...] = ()
    vertical_profile: str | None = None
    readiness: ToolkitReadiness = "estimated"
    source_ref_ids: tuple[str, ...] = ()
    field_source_refs: tuple[FieldSourceRef, ...] = ()
    freshness: SemanticsFreshnessState = "unknown"
    compatibility: SemanticsCompatibilityState = "candidate"
    validation_records: tuple[SemanticsValidationRecord, ...] = ()
    assumptions: tuple[ToolkitAssumption, ...] = ()
    warnings: tuple[ToolkitWarning, ...] = ()
    block_reasons: tuple[SemanticsBlockReason, ...] = ()

    def field_source_ref_ids(self, field_name: str) -> tuple[str, ...]:
        return field_source_ref_ids(self.field_source_refs, field_name)


@dataclass(frozen=True, slots=True)
class TerrainSemanticsIndex:
    packet_id: str
    packet_digest: str
    areas: tuple[TerrainSemanticsRecord, ...]
    dense_features: tuple[TerrainSemanticsRecord, ...]
    light_features: tuple[TerrainSemanticsRecord, ...]
    source_ref_ids: tuple[str, ...] = ()
    source_pack_version: str = "source-pending"

    @classmethod
    def from_packet(
        cls,
        packet: MapPacket,
        *,
        source_ref_ids: tuple[str, ...] = (),
        source_pack_version: str = "source-pending",
    ) -> TerrainSemanticsIndex:
        packet_digest = map_packet_digest(packet)
        area_kind_by_id = {area.id: area.kind.value for area in packet.terrain_areas}
        return cls(
            packet_id=packet.id,
            packet_digest=packet_digest,
            areas=tuple(
                _area_record(
                    packet_id=packet.id,
                    packet_digest=packet_digest,
                    area=area,
                    source_ref_ids=source_ref_ids,
                )
                for area in packet.terrain_areas
            ),
            dense_features=tuple(
                _dense_feature_record(
                    packet_id=packet.id,
                    packet_digest=packet_digest,
                    feature=feature,
                    terrain_kind=area_kind_by_id.get(feature.terrain_area_id),
                    source_ref_ids=source_ref_ids,
                )
                for feature in packet.dense_features
            ),
            light_features=tuple(
                _light_feature_record(
                    packet_id=packet.id,
                    packet_digest=packet_digest,
                    feature=feature,
                    terrain_kind=area_kind_by_id.get(feature.terrain_area_id),
                    source_ref_ids=source_ref_ids,
                )
                for feature in packet.light_features
            ),
            source_ref_ids=source_ref_ids,
            source_pack_version=source_pack_version,
        )

    def records(self) -> tuple[TerrainSemanticsRecord, ...]:
        return (*self.areas, *self.dense_features, *self.light_features)

    def readiness_report(
        self,
        *,
        source_pack_compatible: bool = True,
        source_freshness: SemanticsFreshnessState = "unknown",
        require_vertical_profile: bool = False,
    ) -> SemanticsReadinessReport:
        return report_semantics_readiness(
            terrain_records=self.records(),
            source_pack_compatible=source_pack_compatible,
            source_freshness=source_freshness,
            require_vertical_profile=require_vertical_profile,
        )


def _area_record(
    *,
    packet_id: str,
    packet_digest: str,
    area: TerrainArea,
    source_ref_ids: tuple[str, ...],
) -> TerrainSemanticsRecord:
    return TerrainSemanticsRecord(
        record_id=f"{packet_id}:terrain-area:{area.id}",
        packet_id=packet_id,
        packet_digest=packet_digest,
        element_kind="terrain_area",
        element_id=area.id,
        label=area.label,
        geometry=area.polygon(),
        blocks_los_2d=area.blocks_los,
        terrain_area_id=area.id,
        terrain_kind=area.kind.value,
        source_ref_ids=source_ref_ids,
        field_source_refs=_field_source_refs(
            ("packet_id", "element_id", "geometry", "blocks_los_2d", "terrain_kind"),
            source_ref_ids,
        ),
        assumptions=_record_assumptions(source_ref_ids),
        warnings=_record_warnings(source_ref_ids),
    )


def _dense_feature_record(
    *,
    packet_id: str,
    packet_digest: str,
    feature: DenseTerrainFeature,
    terrain_kind: str | None,
    source_ref_ids: tuple[str, ...],
) -> TerrainSemanticsRecord:
    return TerrainSemanticsRecord(
        record_id=f"{packet_id}:dense-feature:{feature.id}",
        packet_id=packet_id,
        packet_digest=packet_digest,
        element_kind="dense_feature",
        element_id=feature.id,
        label=feature.label,
        geometry=feature.polygon(),
        blocks_los_2d=feature.blocks_los,
        terrain_area_id=feature.terrain_area_id,
        terrain_kind=terrain_kind,
        profile=feature.profile,
        source_ref_ids=source_ref_ids,
        field_source_refs=_field_source_refs(
            (
                "packet_id",
                "element_id",
                "geometry",
                "blocks_los_2d",
                "terrain_area_id",
                "terrain_kind",
                "profile",
            ),
            source_ref_ids,
        ),
        assumptions=_record_assumptions(source_ref_ids),
        warnings=_record_warnings(source_ref_ids),
    )


def _light_feature_record(
    *,
    packet_id: str,
    packet_digest: str,
    feature: LightTerrainFeature,
    terrain_kind: str | None,
    source_ref_ids: tuple[str, ...],
) -> TerrainSemanticsRecord:
    return TerrainSemanticsRecord(
        record_id=f"{packet_id}:light-feature:{feature.id}",
        packet_id=packet_id,
        packet_digest=packet_digest,
        element_kind="light_feature",
        element_id=feature.id,
        label=feature.label,
        geometry=feature.polygon(),
        blocks_los_2d=feature.blocks_los,
        terrain_area_id=feature.terrain_area_id,
        terrain_kind=terrain_kind,
        profile=feature.profile,
        source_ref_ids=source_ref_ids,
        field_source_refs=_field_source_refs(
            (
                "packet_id",
                "element_id",
                "geometry",
                "blocks_los_2d",
                "terrain_area_id",
                "terrain_kind",
                "profile",
            ),
            source_ref_ids,
        ),
        assumptions=_record_assumptions(source_ref_ids),
        warnings=_record_warnings(source_ref_ids),
    )


def _field_source_refs(
    field_names: tuple[str, ...],
    source_ref_ids: tuple[str, ...],
) -> tuple[FieldSourceRef, ...]:
    return tuple(FieldSourceRef(field_name, source_ref_ids) for field_name in field_names)


def _record_assumptions(source_ref_ids: tuple[str, ...]) -> tuple[ToolkitAssumption, ...]:
    return (
        ToolkitAssumption(
            assumption_id="map-packet-terrain-semantics",
            detail=(
                "Record is adapted from MapPacket geometry and LOS flags, not official terrain "
                "mechanics."
            ),
            source_ref_ids=source_ref_ids,
        ),
    )


def _record_warnings(source_ref_ids: tuple[str, ...]) -> tuple[ToolkitWarning, ...]:
    return (
        ToolkitWarning(
            warning_id="terrain-semantics-source-pending",
            detail="Terrain semantics are source-pending and support diagnostics only.",
            source_ref_ids=source_ref_ids,
        ),
    )
