from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

from shapely.geometry.base import BaseGeometry

ToolkitReadiness = Literal["trusted", "estimated", "degraded", "blocked"]


@dataclass(frozen=True, slots=True)
class ToolkitAssumption:
    assumption_id: str
    detail: str
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolkitWarning:
    warning_id: str
    detail: str
    source_ref_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MapOverlayLayer:
    layer_id: str
    layer_kind: str
    geometry: BaseGeometry
    units: str
    style_token: str
    label: str
    readiness: ToolkitReadiness
    source_ref_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.readiness not in get_args(ToolkitReadiness):
            raise ValueError(f"Unknown toolkit readiness: {self.readiness}")

    @property
    def is_empty(self) -> bool:
        return self.geometry.is_empty
