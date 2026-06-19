from __future__ import annotations

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.domain.repository import StaticMapRepository
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.official_layout_metadata import official_layout_metadata_for_page
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
