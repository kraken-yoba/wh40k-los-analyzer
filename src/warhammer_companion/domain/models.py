from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field
from shapely.geometry import Polygon

Inches = Annotated[float, Field(ge=0)]
Point = tuple[float, float]


class TerrainKind(StrEnum):
    RUINS = "ruins"
    WOODS = "woods"
    CRATER = "crater"
    HILLS = "hills"
    OTHER = "other"


class BoardSize(BaseModel):
    width: Inches = 44.0
    height: Inches = 60.0


class TerrainArea(BaseModel):
    id: str
    label: str
    kind: TerrainKind
    footprint: list[Point]
    terrain_group_id: str | None = None
    blocks_los: bool = True

    def polygon(self) -> Polygon:
        return Polygon(self.footprint)


class DenseTerrainFeature(BaseModel):
    id: str
    terrain_area_id: str
    label: str
    footprint: list[Point]
    profile: str | None = None
    blocks_los: bool = True

    def polygon(self) -> Polygon:
        return Polygon(self.footprint)


class LightTerrainFeature(BaseModel):
    id: str
    terrain_area_id: str
    label: str
    footprint: list[Point]
    profile: str | None = None
    blocks_los: bool = False

    def polygon(self) -> Polygon:
        return Polygon(self.footprint)


class DeploymentZone(BaseModel):
    id: str
    label: str
    footprint: list[Point]

    def polygon(self) -> Polygon:
        return Polygon(self.footprint)


class MapPacket(BaseModel):
    id: str
    name: str
    source: str
    board: BoardSize = Field(default_factory=BoardSize)
    terrain_areas: list[TerrainArea]
    dense_features: list[DenseTerrainFeature]
    light_features: list[LightTerrainFeature] = Field(default_factory=list)
    deployment_zones: list[DeploymentZone]

    def blockers(self) -> list[Polygon]:
        terrain_blockers = [area.polygon() for area in self.terrain_areas if area.blocks_los]
        dense_blockers = [
            feature.polygon() for feature in self.dense_features if feature.blocks_los
        ]
        return terrain_blockers + dense_blockers

    def deployment_zone(self, zone_id: str) -> DeploymentZone:
        for zone in self.deployment_zones:
            if zone.id == zone_id:
                return zone
        raise KeyError(f"Unknown deployment zone: {zone_id}")
