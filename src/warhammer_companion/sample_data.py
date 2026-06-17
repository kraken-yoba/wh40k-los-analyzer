from __future__ import annotations

from warhammer_companion.domain.models import (
    DenseTerrainFeature,
    DeploymentZone,
    LightTerrainFeature,
    MapPacket,
    TerrainArea,
    TerrainKind,
)

SAMPLE_PACKETS = [
    MapPacket(
        id="sample-layout-a",
        name="Sample Layout A",
        source="Hand-authored development fixture, not an extracted official layout.",
        terrain_areas=[
            TerrainArea(
                id="a",
                label="A",
                kind=TerrainKind.RUINS,
                footprint=[(4, 6), (14, 6), (14, 18), (4, 18)],
            ),
            TerrainArea(
                id="b",
                label="B",
                kind=TerrainKind.RUINS,
                footprint=[(30, 6), (40, 6), (40, 18), (30, 18)],
            ),
            TerrainArea(
                id="c",
                label="C",
                kind=TerrainKind.RUINS,
                footprint=[(15, 24), (29, 24), (29, 36), (15, 36)],
            ),
            TerrainArea(
                id="d",
                label="D",
                kind=TerrainKind.RUINS,
                footprint=[(4, 42), (14, 42), (14, 54), (4, 54)],
            ),
            TerrainArea(
                id="e",
                label="E",
                kind=TerrainKind.RUINS,
                footprint=[(30, 42), (40, 42), (40, 54), (30, 54)],
            ),
        ],
        dense_features=[
            DenseTerrainFeature(
                id="a-dense",
                terrain_area_id="a",
                label="A dense",
                footprint=[(6, 8), (12, 8), (12, 16), (6, 16)],
                profile="container_or_solid",
            ),
            DenseTerrainFeature(
                id="b-dense",
                terrain_area_id="b",
                label="B dense",
                footprint=[(32, 8), (38, 8), (38, 16), (32, 16)],
                profile="container_or_solid",
            ),
            DenseTerrainFeature(
                id="c-dense",
                terrain_area_id="c",
                label="C dense",
                footprint=[(18, 26), (26, 26), (26, 34), (18, 34)],
                profile="container_or_solid",
            ),
            DenseTerrainFeature(
                id="d-dense",
                terrain_area_id="d",
                label="D dense",
                footprint=[(6, 44), (12, 44), (12, 52), (6, 52)],
                profile="container_or_solid",
            ),
            DenseTerrainFeature(
                id="e-dense",
                terrain_area_id="e",
                label="E dense",
                footprint=[(32, 44), (38, 44), (38, 52), (32, 52)],
                profile="container_or_solid",
            ),
        ],
        light_features=[
            LightTerrainFeature(
                id="c-light",
                terrain_area_id="c",
                label="C light",
                footprint=[(15, 24), (17, 24), (17, 36), (15, 36)],
                profile="light_area",
            )
        ],
        deployment_zones=[
            DeploymentZone(
                id="attacker",
                label="Attacker",
                footprint=[(0, 0), (44, 0), (44, 10), (0, 10)],
            ),
            DeploymentZone(
                id="defender",
                label="Defender",
                footprint=[(0, 50), (44, 50), (44, 60), (0, 60)],
            ),
        ],
    )
]
