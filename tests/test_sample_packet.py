from __future__ import annotations

from shapely.validation import explain_validity

from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_sample_packets_have_valid_polygons() -> None:
    for packet in SAMPLE_PACKETS:
        for terrain in packet.terrain_areas:
            polygon = terrain.polygon()
            assert polygon.is_valid, explain_validity(polygon)
            assert polygon.area > 0
        for feature in packet.dense_features:
            polygon = feature.polygon()
            assert polygon.is_valid, explain_validity(polygon)
            assert polygon.area > 0
        for zone in packet.deployment_zones:
            polygon = zone.polygon()
            assert polygon.is_valid, explain_validity(polygon)
            assert polygon.area > 0
