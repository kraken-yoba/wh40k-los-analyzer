from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float


class PolygonGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    points: list[Point] = Field(min_length=3)


class Board(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: float = Field(gt=0)
    height: float = Field(gt=0)
    unit: Literal["inch"] = "inch"


class TerrainFeature(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_id: str
    label: str
    footprint: PolygonGeometry


class Blocker(BaseModel):
    model_config = ConfigDict(extra="forbid")

    blocker_id: str
    feature_id: str
    kind: BlockerKind
    start: Point
    end: Point


class DeploymentZone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zone_id: str
    label: str
    area: PolygonGeometry


class LayoutProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_document_id: str
    source_page: int = Field(ge=1)
    extraction_method: str


class ValidationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: ValidationSeverity
    message: str
    review_status: ReviewStatus = ReviewStatus.NOT_REQUIRED

    @model_validator(mode="after")
    def default_review_status_for_warning(self) -> Self:
        needs_review = (
            self.severity == ValidationSeverity.WARNING
            and self.review_status == ReviewStatus.NOT_REQUIRED
        )
        if needs_review:
            self.review_status = ReviewStatus.UNREVIEWED
        return self


class CanonicalLayout(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    layout_id: str
    name: str
    board: Board
    terrain_features: list[TerrainFeature]
    blockers: list[Blocker]
    deployments: list[DeploymentZone]
    provenance: LayoutProvenance
    validation_records: list[ValidationRecord] = Field(default_factory=list)
    validation_status: ValidationStatus

    @model_validator(mode="after")
    def validate_geometry_inside_board(self) -> Self:
        feature_ids = self._require_unique(
            [feature.feature_id for feature in self.terrain_features],
            "duplicate terrain feature id",
        )
        self._require_unique(
            [blocker.blocker_id for blocker in self.blockers],
            "duplicate blocker id",
        )
        self._require_unique(
            [deployment.zone_id for deployment in self.deployments],
            "duplicate deployment zone id",
        )

        for feature in self.terrain_features:
            for point in feature.footprint.points:
                self._require_inside_board(point, f"terrain feature {feature.feature_id}")

        for blocker in self.blockers:
            if blocker.feature_id not in feature_ids:
                raise ValueError(
                    f"blocker {blocker.blocker_id} references unknown terrain feature "
                    f"{blocker.feature_id}"
                )
            self._require_inside_board(blocker.start, f"blocker {blocker.blocker_id}")
            self._require_inside_board(blocker.end, f"blocker {blocker.blocker_id}")

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
