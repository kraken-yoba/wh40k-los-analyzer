from __future__ import annotations

import pytest

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.domain.repository import StaticMapRepository
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.official_layout_metadata import official_layout_metadata_for_page
from warhammer_companion.los.geometry import (
    clamp_base_center,
    visibility_polygon_from_base,
    visibility_rays_from_base,
)
from warhammer_companion.los.movement import movement_envelope, swept_base_path
from warhammer_companion.los.threat import threat_projection_regions
from warhammer_companion.rendering.svg import render_map_svg
from warhammer_companion.sample_data import SAMPLE_PACKETS
from warhammer_companion.web import server


def test_service_groups_official_packets_by_dispositions_and_layout_variant() -> None:
    packets = [
        SAMPLE_PACKETS[0].model_copy(
            update={
                "id": f"official-event-companion-page-{page}",
                "name": f"Official Page {page}",
                "layout_metadata": official_layout_metadata_for_page(page),
            }
        )
        for page in range(9, 12)
    ]
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(list(reversed(packets))),
        codex_backend=server.codex_backend,
    )

    groups = service.packet_select_groups()

    assert [group.label for group in groups] == ["Take and Hold vs Take and Hold"]
    assert [option.id for option in groups[0].options] == [
        "official-event-companion-page-9",
        "official-event-companion-page-10",
        "official-event-companion-page-11",
    ]
    assert groups[0].options[0].label == (
        "Layout A - Take and Hold vs Take and Hold (Battlefield Dominance vs Battlefield Dominance)"
    )


def test_service_resolves_packet_from_player_dispositions_and_layout() -> None:
    packets = [
        SAMPLE_PACKETS[0].model_copy(
            update={
                "id": f"official-event-companion-page-{page}",
                "name": f"Official Page {page}",
                "layout_metadata": official_layout_metadata_for_page(page),
            }
        )
        for page in range(9, 54)
    ]
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(list(reversed(packets))),
        codex_backend=server.codex_backend,
    )

    selector = service.packet_selector_state(
        player_a="Take and Hold",
        player_b="Reconnaissance",
        layout_variant="C",
    )

    assert selector.player_a_options == [
        "Take and Hold",
        "Purge the Foe",
        "Disruption",
        "Reconnaissance",
        "Priority Assets",
    ]
    assert selector.player_b_options == [
        "Take and Hold",
        "Purge the Foe",
        "Disruption",
        "Reconnaissance",
        "Priority Assets",
    ]
    assert [option.variant for option in selector.layout_options] == ["A", "B", "C"]
    assert selector.selected_packet_id == "official-event-companion-page-20"
    assert (
        service.resolve_packet_id(
            player_a="Priority Assets",
            player_b="Priority Assets",
            layout_variant="B",
        )
        == "official-event-companion-page-52"
    )


def test_heatmap_state_clamps_and_caches_rendered_svg() -> None:
    render_calls: list[tuple[str, str, str, int]] = []

    class CountingService(WarhammerCompanionService):
        def _render_heatmap_svg(
            self,
            packet_id: str,
            zone_id: str,
            source: str,
            offset_inches: int,
        ) -> str:
            render_calls.append((packet_id, zone_id, source, offset_inches))
            return '<svg class="map-svg" role="img" aria-label="cached map"></svg>'

    service = CountingService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )

    first_state = service.heatmap_state(
        packet_id=SAMPLE_PACKETS[0].id,
        zone_id="attacker",
        source="edge",
        offset_inches=99,
    )
    second_state = service.heatmap_state(
        packet_id=SAMPLE_PACKETS[0].id,
        zone_id="attacker",
        source="edge",
        offset_inches=99,
    )
    service.clear_caches()
    third_state = service.heatmap_state(
        packet_id=SAMPLE_PACKETS[0].id,
        zone_id="attacker",
        source="edge",
        offset_inches=99,
    )

    assert first_state.selected_offset_inches == 12
    assert second_state.map_svg == first_state.map_svg
    assert third_state.map_svg == first_state.map_svg
    assert render_calls == [
        (SAMPLE_PACKETS[0].id, "attacker", "edge", 12),
        (SAMPLE_PACKETS[0].id, "attacker", "edge", 12),
    ]


def test_hidden_coverage_state_selects_terrain_and_detection_range() -> None:
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )
    terrain_area = SAMPLE_PACKETS[0].terrain_areas[0]

    state = service.hidden_coverage_state(
        packet_id=SAMPLE_PACKETS[0].id,
        terrain_area_id=terrain_area.id,
        detection_range=18,
    )

    assert state.packet.id == SAMPLE_PACKETS[0].id
    assert state.selected_terrain_area_id == terrain_area.id
    assert state.selected_detection_range == 18
    assert state.detection_range_options == [12, 15, 18]
    assert state.terrain_options[0].id == terrain_area.id
    assert state.terrain_options[0].label == terrain_area.label
    assert 'class="hidden-coverage-image"' in state.map_svg
    assert 'class="selected-terrain-area"' in state.map_svg


def test_los_checker_toolkit_result_wraps_analysis_before_svg_projection() -> None:
    packet = SAMPLE_PACKETS[0]
    before = packet.model_dump()
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )

    result = service.los_checker_toolkit_result(
        packet_id=SAMPLE_PACKETS[0].id,
        x=22.0,
        y=10.0,
        base=1.57,
    )

    assert result.tool_id == "los_checker"
    assert result.readiness == "estimated"
    assert result.payload.packet is SAMPLE_PACKETS[0]
    assert result.overlays
    assert result.overlays[0].layer_kind == "line_of_sight_coverage"
    assert not result.allows_recommendation_language()
    assert packet.model_dump() == before


def test_los_checker_toolkit_identity_includes_inputs_and_packet_content() -> None:
    packet = SAMPLE_PACKETS[0]
    changed_packet = packet.model_copy(update={"name": f"{packet.name} revised"})
    original_service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository([packet]),
        codex_backend=server.codex_backend,
    )
    changed_service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository([changed_packet]),
        codex_backend=server.codex_backend,
    )

    original = original_service.los_checker_toolkit_result(packet_id=packet.id, x=22.0, y=10.0)
    moved = original_service.los_checker_toolkit_result(packet_id=packet.id, x=23.0, y=10.0)
    changed = changed_service.los_checker_toolkit_result(
        packet_id=changed_packet.id,
        x=22.0,
        y=10.0,
    )

    original_suffix = original.input_hash.removeprefix("sha256:")[:12]
    assert original.input_hash != moved.input_hash
    assert original.input_hash != changed.input_hash
    assert original.result_id.endswith(original_suffix)
    assert original.overlays[0].layer_id.endswith(original_suffix)


def test_los_checker_state_matches_direct_legacy_rendering_path() -> None:
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )
    packet = SAMPLE_PACKETS[0]
    center = clamp_base_center(packet, (22.0, 10.0), 1.57)
    coverage_polygon = visibility_polygon_from_base(packet, center, 1.57)
    rays = visibility_rays_from_base(packet, center, 1.57)
    expected_svg = render_map_svg(
        packet,
        coverage_polygon=coverage_polygon,
        rays=rays,
        base_center=center,
        base_diameter=1.57,
    )

    state = service.los_checker_state(packet_id=packet.id, x=22.0, y=10.0, base=1.57)

    assert state.packet is packet
    assert state.x == center[0]
    assert state.y == center[1]
    assert state.base == 1.57
    assert state.map_svg == expected_svg


def test_movement_reach_toolkit_result_wraps_analysis_before_svg_projection() -> None:
    packet = SAMPLE_PACKETS[0]
    before = packet.model_dump()
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )

    result = service.movement_reach_toolkit_result(
        packet_id=packet.id,
        start_x=16.0,
        start_y=10.0,
        target_x=22.0,
        target_y=10.0,
        base=1.57,
        move=6.0,
        mode="normal",
    )

    assert result.tool_id == "movement_reach"
    assert result.readiness == "estimated"
    assert result.payload.packet is packet
    assert result.overlays
    assert result.overlays[0].layer_kind == "movement_envelope"
    assert result.payload.endpoint.estimated_reachable
    assert not result.allows_recommendation_language()
    assert packet.model_dump() == before


def test_movement_reach_state_matches_direct_rendering_path() -> None:
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )
    packet = SAMPLE_PACKETS[0]
    envelope = movement_envelope(
        packet,
        start_center=(16.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
    )
    movement_path = swept_base_path(
        start_center=(16.0, 10.0),
        target_center=(22.0, 10.0),
        base_diameter=1.57,
    )
    expected_svg = render_map_svg(
        packet,
        movement_envelope=envelope,
        movement_path=movement_path,
        movement_start_center=(16.0, 10.0),
        movement_target_center=(22.0, 10.0),
        movement_base_diameter=1.57,
    )

    state = service.movement_reach_state(
        packet_id=packet.id,
        start_x=16.0,
        start_y=10.0,
        target_x=22.0,
        target_y=10.0,
        base=1.57,
        move=6.0,
        mode="normal",
    )

    assert state.packet is packet
    assert state.start_x == 16.0
    assert state.target_x == 22.0
    assert state.mode == "normal"
    assert state.endpoint_estimated_reachable
    assert state.map_svg == expected_svg


def test_threat_range_toolkit_result_wraps_analysis_before_svg_projection() -> None:
    packet = SAMPLE_PACKETS[0]
    before = packet.model_dump()
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )

    result = service.threat_range_toolkit_result(
        packet_id=packet.id,
        source_x=16.0,
        source_y=10.0,
        target_x=24.0,
        target_y=10.0,
        base=1.57,
        move=6.0,
        threat=2.0,
        mode="2d6-move-plus-range",
    )

    assert result.tool_id == "threat_range"
    assert result.readiness == "estimated"
    assert result.payload.packet is packet
    assert result.overlays
    assert result.overlays[0].layer_kind == "threat_projection"
    assert result.payload.target_probability > 0.0
    assert not result.allows_recommendation_language()
    assert packet.model_dump() == before


def test_threat_range_state_matches_direct_rendering_path() -> None:
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )
    packet = SAMPLE_PACKETS[0]
    regions = threat_projection_regions(
        packet,
        source_center=(16.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
        threat_range=2.0,
        mode="2d6-move-plus-range",
    )
    expected_svg = render_map_svg(
        packet,
        threat_regions=regions,
        threat_source_center=(16.0, 10.0),
        threat_target_point=(24.0, 10.0),
        threat_base_diameter=1.57,
    )

    state = service.threat_range_state(
        packet_id=packet.id,
        source_x=16.0,
        source_y=10.0,
        target_x=24.0,
        target_y=10.0,
        base=1.57,
        move=6.0,
        threat=2.0,
        mode="2d6-move-plus-range",
    )

    assert state.packet is packet
    assert state.source_x == 16.0
    assert state.target_x == 24.0
    assert state.mode == "2d6-move-plus-range"
    assert state.measurement_convention == "source-base-edge-to-target-point"
    assert state.target_probability > 0.0
    assert state.map_svg == expected_svg


def test_deployment_exposure_toolkit_result_wraps_analysis_before_svg_projection() -> None:
    packet = SAMPLE_PACKETS[0]
    before = packet.model_dump()
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )

    result = service.deployment_exposure_toolkit_result(
        packet_id=packet.id,
        deployment_zone_id="attacker",
        friendly_x=10.0,
        friendly_y=5.0,
        friendly_base=1.57,
        enemy_x=38.0,
        enemy_y=52.0,
        enemy_base=1.57,
        enemy_move=0.0,
        enemy_threat=1.0,
        enemy_mode="raw-range",
        exposure_mode="threat-and-los",
    )

    assert result.tool_id == "deployment_exposure"
    assert result.readiness == "estimated"
    assert result.payload.packet is packet
    assert [overlay.layer_kind for overlay in result.overlays] == [
        "deployment_candidate_staging",
        "enemy_threat_projection",
        "enemy_los_projection",
    ]
    assert result.payload.placement.not_exposed_under_assumptions
    assert not result.allows_recommendation_language()
    assert packet.model_dump() == before


def test_deployment_exposure_state_renders_candidate_threat_los_and_base_overlays() -> None:
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )

    state = service.deployment_exposure_state(
        packet_id=SAMPLE_PACKETS[0].id,
        deployment_zone_id="attacker",
        friendly_x=10.0,
        friendly_y=5.0,
        friendly_base=1.57,
        enemy_x=38.0,
        enemy_y=52.0,
        enemy_base=1.57,
        enemy_move=0.0,
        enemy_threat=1.0,
        enemy_mode="raw-range",
        exposure_mode="threat-and-los",
    )

    assert state.packet.id == SAMPLE_PACKETS[0].id
    assert state.deployment_zone_id == "attacker"
    assert state.not_exposed_under_assumptions
    assert state.threat_probability_at_center == 0.0
    assert "not a placement planner" in " ".join(state.warning_details).lower()
    assert 'class="safe-zone-outline"' in state.map_svg
    assert 'class="coverage-image"' in state.map_svg
    assert 'class="threat-projection-image"' in state.map_svg
    assert 'class="model-base"' in state.map_svg
    assert 'class="threat-source-base"' in state.map_svg


@pytest.mark.parametrize(
    ("mode", "expected_los", "expected_threat"),
    [
        ("threat-only", False, True),
        ("los-only", True, False),
        ("threat-or-los", True, True),
        ("threat-and-los", True, True),
    ],
)
def test_deployment_exposure_state_renders_component_overlays_by_mode(
    mode: str,
    expected_los: bool,
    expected_threat: bool,
) -> None:
    service = WarhammerCompanionService(
        paths=IngestionPaths(),
        repository=StaticMapRepository(SAMPLE_PACKETS),
        codex_backend=server.codex_backend,
    )

    state = service.deployment_exposure_state(
        packet_id=SAMPLE_PACKETS[0].id,
        deployment_zone_id="attacker",
        friendly_x=10.0,
        friendly_y=5.0,
        friendly_base=1.57,
        enemy_x=38.0,
        enemy_y=52.0,
        enemy_base=1.57,
        enemy_move=6.0,
        enemy_threat=2.0,
        enemy_mode="fixed-move-plus-range",
        exposure_mode=mode,
    )

    assert ('class="coverage-image"' in state.map_svg) is expected_los
    assert ('class="threat-projection-image"' in state.map_svg) is expected_threat
