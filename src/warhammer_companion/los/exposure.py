from __future__ import annotations

from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from warhammer_companion.domain.deployment_geometry import smooth_deployment_footprint
from warhammer_companion.domain.exposure import ExposureMode
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.los.movement import (
    base_center_region,
    dense_movement_collision_regions,
)


def allowed_deployment_center_region(
    packet: MapPacket,
    *,
    deployment_zone_id: str,
    base_radius: float,
) -> BaseGeometry:
    if base_radius < 0:
        raise ValueError("base_radius must be non-negative")
    zone = packet.deployment_zone(deployment_zone_id)
    zone_polygon = Polygon(smooth_deployment_footprint(zone.footprint))
    zone_centers = zone_polygon.buffer(-base_radius).buffer(0) if base_radius > 0 else zone_polygon
    if zone_centers.is_empty:
        return Polygon()
    return zone_centers.intersection(base_center_region(packet, base_radius)).buffer(0)


def exposure_risk_region(
    *,
    threat_region: BaseGeometry,
    los_region: BaseGeometry,
    exposure_mode: ExposureMode,
) -> BaseGeometry:
    if exposure_mode == "threat-only":
        return threat_region.buffer(0)
    if exposure_mode == "los-only":
        return los_region.buffer(0)
    if exposure_mode == "threat-and-los":
        return threat_region.intersection(los_region).buffer(0)
    return unary_union([threat_region, los_region]).buffer(0)


def candidate_staging_center_region(
    packet: MapPacket,
    *,
    deployment_zone_id: str,
    base_radius: float,
    risk_region: BaseGeometry,
) -> BaseGeometry:
    allowed_region = allowed_deployment_center_region(
        packet,
        deployment_zone_id=deployment_zone_id,
        base_radius=base_radius,
    )
    if allowed_region.is_empty:
        return allowed_region
    dense_collision = dense_movement_collision_regions(packet, base_radius)
    candidate_region = allowed_region.difference(dense_collision)
    if not risk_region.is_empty:
        candidate_region = candidate_region.difference(risk_region.buffer(base_radius))
    return candidate_region.buffer(0)
