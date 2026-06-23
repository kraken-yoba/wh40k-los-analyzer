from __future__ import annotations

from math import cos, hypot, radians, sin
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TTS_BOARD_SNAPSHOT_SCHEMA_VERSION: Final[Literal["tts-board-snapshot/v0"]] = "tts-board-snapshot/v0"
TTS_BOARD_TRANSFORM_SCHEMA_VERSION: Final[Literal["tts-board-transform/v0"]] = (
    "tts-board-transform/v0"
)
TTS_HOST_CONTEXT_SCHEMA_VERSION: Final[Literal["tts-host-context/v0"]] = "tts-host-context/v0"
TTS_DIAGNOSTIC_LOS_PROBE_SCHEMA_VERSION: Final[Literal["tts-diagnostic-los-probe/v0"]] = (
    "tts-diagnostic-los-probe/v0"
)
TTS_BRIDGE_RESPONSE_SCHEMA_VERSION: Final[Literal["tts-bridge-response/v0"]] = (
    "tts-bridge-response/v0"
)

TtsObjectKind = Literal["attacker", "target", "terrain"]
TtsObjectProvenance = Literal["tagged", "selected", "manual", "unsupported"]


class TtsContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TtsVector3(TtsContractModel):
    x: float
    y: float
    z: float


class BattlefieldPoint(TtsContractModel):
    x: float = Field(ge=0.0)
    y: float = Field(ge=0.0)

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


class TtsBoardCalibrationPoint(TtsContractModel):
    label: str = Field(min_length=1)
    world: TtsVector3
    battlefield: BattlefieldPoint


class TtsBoardTransform(TtsContractModel):
    schema_version: Literal["tts-board-transform/v0"] = TTS_BOARD_TRANSFORM_SCHEMA_VERSION
    tts_origin: TtsVector3
    battlefield_origin: BattlefieldPoint
    board_rotation_degrees_clockwise: float = 0.0
    tts_units_per_inch: float = Field(gt=0.0)
    board_width_inches: float = Field(gt=0.0)
    board_height_inches: float = Field(gt=0.0)
    round_trip_tolerance_inches: float = Field(gt=0.0)
    calibration_points: tuple[TtsBoardCalibrationPoint, ...] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_calibration_tolerance(self) -> TtsBoardTransform:
        if self.max_round_trip_error_inches() > self.round_trip_tolerance_inches:
            raise ValueError("calibration points exceed round-trip tolerance")
        return self

    def world_to_battlefield(self, world: TtsVector3) -> BattlefieldPoint:
        dx = (world.x - self.tts_origin.x) / self.tts_units_per_inch
        dz = (world.z - self.tts_origin.z) / self.tts_units_per_inch
        theta = radians(self.board_rotation_degrees_clockwise)
        local_x = dx * cos(theta) - dz * sin(theta)
        local_y = dx * sin(theta) + dz * cos(theta)
        return BattlefieldPoint(
            x=self.battlefield_origin.x + local_x,
            y=self.battlefield_origin.y + local_y,
        )

    def round_trip_error_inches(self, point: TtsBoardCalibrationPoint) -> float:
        resolved = self.world_to_battlefield(point.world)
        return hypot(resolved.x - point.battlefield.x, resolved.y - point.battlefield.y)

    def max_round_trip_error_inches(self) -> float:
        return max(self.round_trip_error_inches(point) for point in self.calibration_points)


class TtsObjectRef(TtsContractModel):
    guid: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    object_kind: TtsObjectKind
    tags: tuple[str, ...] = ()
    position: TtsVector3
    rotation: TtsVector3
    scale: TtsVector3
    provenance: TtsObjectProvenance


class TtsHostContext(TtsContractModel):
    schema_version: Literal["tts-host-context/v0"] = TTS_HOST_CONTEXT_SCHEMA_VERSION
    host_only: bool = True
    local_companion_required: bool = True
    live_tts_round_trip_observed: bool = False
    note: str = Field(min_length=1)


class TtsDiagnosticLosProbe(TtsContractModel):
    schema_version: Literal["tts-diagnostic-los-probe/v0"] = TTS_DIAGNOSTIC_LOS_PROBE_SCHEMA_VERSION
    probe_id: str = Field(min_length=1)
    source_guid: str = Field(min_length=1)
    target_guid: str = Field(min_length=1)
    start_world: TtsVector3
    end_world: TtsVector3
    hit: bool
    hit_guid: str | None = None
    authoritative: bool = False
    label: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_diagnostic_only(self) -> TtsDiagnosticLosProbe:
        if self.authoritative:
            raise ValueError("diagnostic LOS probe cannot be authoritative")
        return self


class TtsBoardSnapshot(TtsContractModel):
    schema_version: Literal["tts-board-snapshot/v0"] = TTS_BOARD_SNAPSHOT_SCHEMA_VERSION
    snapshot_id: str = Field(min_length=1)
    captured_at_epoch: float = Field(ge=0.0)
    source: str = Field(min_length=1)
    host_context: TtsHostContext
    transform: TtsBoardTransform
    objects: tuple[TtsObjectRef, ...]
    diagnostic_los: TtsDiagnosticLosProbe | None = None

    @model_validator(mode="after")
    def validate_required_object_roles(self) -> TtsBoardSnapshot:
        counts = self.object_counts()
        missing = [kind for kind in ("attacker", "target", "terrain") if counts[kind] < 1]
        if missing:
            raise ValueError("snapshot requires attacker, target, and terrain objects")
        return self

    def object_counts(self) -> dict[str, int]:
        counts = {"attacker": 0, "target": 0, "terrain": 0}
        for obj in self.objects:
            counts[obj.object_kind] += 1
        return counts


class TtsBridgeError(TtsContractModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    field_path: tuple[str, ...] = ()


class TtsBridgeResponse(TtsContractModel):
    schema_version: Literal["tts-bridge-response/v0"] = TTS_BRIDGE_RESPONSE_SCHEMA_VERSION
    ok: bool
    data: dict[str, object] = Field(default_factory=dict)
    error: TtsBridgeError | None = None

    @model_validator(mode="after")
    def validate_error_shape(self) -> TtsBridgeResponse:
        if self.ok and self.error is not None:
            raise ValueError("successful TTS bridge responses cannot include an error")
        if not self.ok and self.error is None:
            raise ValueError("failed TTS bridge responses require an error")
        return self
