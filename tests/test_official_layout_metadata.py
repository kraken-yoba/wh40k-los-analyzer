from __future__ import annotations

from itertools import pairwise

from warhammer_companion.ingestion.official_layout_metadata import (
    OFFICIAL_LAYOUT_PAGE_METADATA,
    official_layout_metadata_for_page,
)


def test_official_layout_metadata_covers_all_event_layout_pages() -> None:
    assert sorted(OFFICIAL_LAYOUT_PAGE_METADATA) == list(range(9, 54))


def test_official_layout_metadata_groups_each_matchup_into_three_variants() -> None:
    groups: dict[tuple[str, str, str, str], list[tuple[int, str]]] = {}
    for page, metadata in sorted(OFFICIAL_LAYOUT_PAGE_METADATA.items()):
        key = (
            metadata.first_player.force_disposition,
            metadata.first_player.primary_mission,
            metadata.second_player.force_disposition,
            metadata.second_player.primary_mission,
        )
        groups.setdefault(key, []).append((page, metadata.layout_variant))

    assert len(groups) == 15
    for variants in groups.values():
        assert [variant for _, variant in variants] == ["A", "B", "C"]
        assert [right - left for (left, _), (right, _) in pairwise(variants)] == [1, 1]


def test_official_layout_metadata_identifies_page_9_scenario() -> None:
    metadata = official_layout_metadata_for_page(9)

    assert metadata is not None
    assert metadata.source_page == 9
    assert metadata.layout_variant == "A"
    assert metadata.first_player.force_disposition == "Take and Hold"
    assert metadata.first_player.primary_mission == "Battlefield Dominance"
    assert metadata.second_player.force_disposition == "Take and Hold"
    assert metadata.second_player.primary_mission == "Battlefield Dominance"


def test_official_layout_metadata_identifies_final_priority_assets_variant() -> None:
    metadata = official_layout_metadata_for_page(53)

    assert metadata is not None
    assert metadata.source_page == 53
    assert metadata.layout_variant == "C"
    assert metadata.first_player.force_disposition == "Priority Assets"
    assert metadata.first_player.primary_mission == "Sabotage"
    assert metadata.second_player.force_disposition == "Priority Assets"
    assert metadata.second_player.primary_mission == "Sabotage"
