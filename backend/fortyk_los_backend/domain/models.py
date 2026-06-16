from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator
from shapely.geometry import LineString, Polygon

GEOMETRY_EPSILON = 1e-9


class CanonicalBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ValidationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationStatus(StrEnum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class ReviewStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    UNREVIEWED = "unreviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class BlockerKind(StrEnum):
    WALL = "wall"


class Point(CanonicalBaseModel):
    x: FiniteFloat
    y: FiniteFloat


class PolygonGeometry(CanonicalBaseModel):
    points: tuple[Point, ...] = Field(min_length=3)

    @model_validator(mode="after")
    def validate_simple_polygon(self) -> Self:
        coordinates = [(point.x, point.y) for point in self.points]
        if len(set(coordinates)) != len(coordinates):
            raise ValueError("valid simple polygon required: duplicate points")

        polygon = self.to_shapely()
        if polygon.area <= GEOMETRY_EPSILON or not polygon.is_valid:
            raise ValueError("valid simple polygon required")

        return self

    def to_shapely(self) -> Polygon:
        return Polygon((point.x, point.y) for point in self.points)


class Board(CanonicalBaseModel):
    width: FiniteFloat = Field(gt=0)
    height: FiniteFloat = Field(gt=0)
    unit: Literal["inch"] = "inch"


class TerrainFeature(CanonicalBaseModel):
    feature_id: str
    label: str
    footprint: PolygonGeometry


class Blocker(CanonicalBaseModel):
    blocker_id: str
    feature_id: str
    kind: BlockerKind
    start: Point
    end: Point

    def to_shapely(self) -> LineString:
        return LineString([(self.start.x, self.start.y), (self.end.x, self.end.y)])


class DeploymentZone(CanonicalBaseModel):
    zone_id: str
    label: str
    area: PolygonGeometry


class LayoutProvenance(CanonicalBaseModel):
    source_document_id: str
    source_page: int = Field(ge=1)
    extraction_method: str


class ValidationRecord(CanonicalBaseModel):
    code: str
    severity: ValidationSeverity
    message: str
    review_status: ReviewStatus = ReviewStatus.NOT_REQUIRED

    @model_validator(mode="before")
    @classmethod
    def default_review_status_for_warning(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        severity = data.get("severity")
        review_status = data.get("review_status")
        if severity in {ValidationSeverity.WARNING, ValidationSeverity.WARNING.value} and (
            review_status is None or review_status == ReviewStatus.NOT_REQUIRED
        ):
            return {**data, "review_status": ReviewStatus.UNREVIEWED}
        return data


class CanonicalLayout(CanonicalBaseModel):
    schema_version: Literal["1.0"] = "1.0"
    layout_id: str
    name: str
    board: Board
    terrain_features: tuple[TerrainFeature, ...]
    blockers: tuple[Blocker, ...]
    deployments: tuple[DeploymentZone, ...]
    provenance: LayoutProvenance
    validation_records: tuple[ValidationRecord, ...] = Field(default_factory=tuple)
    validation_status: ValidationStatus

    @model_validator(mode="after")
    def validate_geometry_inside_board(self) -> Self:
        self._require_unique(
            [feature.feature_id for feature in self.terrain_features],
            "duplicate terrain feature id",
        )
        feature_by_id = {feature.feature_id: feature for feature in self.terrain_features}
        self._require_unique(
            [blocker.blocker_id for blocker in self.blockers],
            "duplicate blocker id",
        )
        self._require_unique(
            [deployment.zone_id for deployment in self.deployments],
            "duplicate deployment zone id",
        )
        self._require_unique(
            [record.code for record in self.validation_records],
            "duplicate validation record code",
        )

        for feature in self.terrain_features:
            for point in feature.footprint.points:
                self._require_inside_board(point, f"terrain feature {feature.feature_id}")

        for blocker in self.blockers:
            if blocker.feature_id not in feature_by_id:
                raise ValueError(
                    f"blocker {blocker.blocker_id} references unknown terrain feature "
                    f"{blocker.feature_id}"
                )
            self._require_inside_board(blocker.start, f"blocker {blocker.blocker_id}")
            self._require_inside_board(blocker.end, f"blocker {blocker.blocker_id}")
            self._require_blocker_inside_footprint(blocker, feature_by_id[blocker.feature_id])

        for deployment in self.deployments:
            for point in deployment.area.points:
                self._require_inside_board(point, f"deployment zone {deployment.zone_id}")

        return self

    def _require_inside_board(self, point: Point, owner: str) -> None:
        if point.x < 0 or point.y < 0 or point.x > self.board.width or point.y > self.board.height:
            msg = (
                f"{owner} point ({point.x}, {point.y}) is outside board bounds "
                f"0..{self.board.width} x 0..{self.board.height}"
            )
            raise ValueError(msg)

    def _require_unique(self, values: list[str], error_message: str) -> set[str]:
        seen: set[str] = set()
        for value in values:
            if value in seen:
                raise ValueError(f"{error_message}: {value}")
            seen.add(value)
        return seen

    def _require_blocker_inside_footprint(self, blocker: Blocker, feature: TerrainFeature) -> None:
        blocker_line = blocker.to_shapely()
        if blocker_line.length <= GEOMETRY_EPSILON:
            raise ValueError(f"blocker {blocker.blocker_id} has zero length")

        footprint = feature.footprint.to_shapely()
        if not footprint.covers(blocker_line):
            raise ValueError(
                f"blocker {blocker.blocker_id} is outside terrain footprint "
                f"{feature.feature_id}"
            )
