from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from warhammer_companion.ingestion.layouts import FeatureProfile, WallSide

FeaturePosition = Literal["center", "edge", "corner", "multiple", "unknown"]
BlockerTemplate = Literal[
    "l_wall",
    "u_wall",
    "perimeter_wall",
    "solid_polygon",
    "non_blocking_review",
]

FEATURE_CATALOG_VERSION = 1
PACKAGE_DIR = Path(__file__).resolve().parents[1]


class TerrainFeatureType(BaseModel):
    type_id: str = Field(pattern=r"^[a-z0-9-]+$")
    display_name: str
    description: str
    feature_profile: FeatureProfile
    blocks_los: bool
    blocker_template: BlockerTemplate
    representative_image_path: str
    typical_positions: list[FeaturePosition]
    default_wall_sides: list[WallSide] | None = None
    classification_hints: list[str] = Field(default_factory=list)

    def resolved_representative_image_path(self) -> str:
        return str(PACKAGE_DIR / self.representative_image_path)


TERRAIN_FEATURE_TYPES: tuple[TerrainFeatureType, ...] = (
    TerrainFeatureType(
        type_id="ruined-wall-l",
        display_name="L shaped ruined wall",
        description=(
            "Two connected vertical wall runs forming an L. Floors or open interior space are "
            "not LOS blockers; only the wall runs block LOS."
        ),
        feature_profile="ruined_wall_l",
        blocks_los=True,
        blocker_template="l_wall",
        representative_image_path="catalog_assets/ruined-wall-l.svg",
        typical_positions=["corner", "edge"],
        default_wall_sides=["left", "top"],
        classification_hints=["two perpendicular wall runs", "open interior", "ruin corner"],
    ),
    TerrainFeatureType(
        type_id="ruined-wall-u",
        display_name="U shaped ruined wall",
        description=(
            "Three connected vertical wall runs forming a U. The open side and any upper floor "
            "surface should remain non-blocking."
        ),
        feature_profile="ruined_wall_u",
        blocks_los=True,
        blocker_template="u_wall",
        representative_image_path="catalog_assets/ruined-wall-u.svg",
        typical_positions=["center", "edge", "corner"],
        default_wall_sides=["left", "right", "top"],
        classification_hints=["three wall runs", "one open side", "ruin shell"],
    ),
    TerrainFeatureType(
        type_id="ruined-wall-perimeter",
        display_name="Perimeter ruined wall",
        description=(
            "Vertical wall sections around most or all sides of the feature. Only the perimeter "
            "walls block LOS; interior floors do not."
        ),
        feature_profile="ruined_wall_perimeter",
        blocks_los=True,
        blocker_template="perimeter_wall",
        representative_image_path="catalog_assets/ruined-wall-perimeter.svg",
        typical_positions=["center", "edge"],
        default_wall_sides=["left", "right", "top", "bottom"],
        classification_hints=["walls on most sides", "ring or box ruin", "open interior"],
    ),
    TerrainFeatureType(
        type_id="armoured-container",
        display_name="Armoured container",
        description=(
            "A solid container-like dense feature that blocks LOS across its full footprint."
        ),
        feature_profile="container_or_solid",
        blocks_los=True,
        blocker_template="solid_polygon",
        representative_image_path="catalog_assets/armoured-container.svg",
        typical_positions=["center", "edge", "multiple"],
        classification_hints=["rectangular container", "solid block", "ribbed top"],
    ),
    TerrainFeatureType(
        type_id="solid-los-blocker",
        display_name="Solid LOS blocker",
        description=(
            "A generic dense vertical object that blocks LOS across its detected footprint."
        ),
        feature_profile="solid_los_blocker",
        blocks_los=True,
        blocker_template="solid_polygon",
        representative_image_path="catalog_assets/solid-los-blocker.svg",
        typical_positions=["center", "edge", "corner", "multiple"],
        classification_hints=["solid vertical mass", "no open wall shape"],
    ),
    TerrainFeatureType(
        type_id="floor-or-platform",
        display_name="Floor or platform",
        description=(
            "A horizontal surface such as an upper floor, gantry, or platform. It is kept for "
            "review and future rules but is not an LOS blocker."
        ),
        feature_profile="floor_or_platform",
        blocks_los=False,
        blocker_template="non_blocking_review",
        representative_image_path="catalog_assets/floor-or-platform.svg",
        typical_positions=["center", "edge"],
        classification_hints=["flat horizontal surface", "platform", "upper floor"],
    ),
)

_FEATURE_TYPES_BY_ID = {entry.type_id: entry for entry in TERRAIN_FEATURE_TYPES}


def terrain_feature_type_by_id(type_id: str) -> TerrainFeatureType:
    return _FEATURE_TYPES_BY_ID[type_id]


def terrain_feature_type_options() -> list[TerrainFeatureType]:
    return list(TERRAIN_FEATURE_TYPES)
