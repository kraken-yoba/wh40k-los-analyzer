from __future__ import annotations

from warhammer_companion.domain.models import OfficialLayoutMetadata, OfficialLayoutSide

_LAYOUT_VARIANTS = ("A", "B", "C")
_LAYOUT_SERIES: tuple[tuple[int, str, str, str, str], ...] = (
    (
        9,
        "Take and Hold",
        "Battlefield Dominance",
        "Take and Hold",
        "Battlefield Dominance",
    ),
    (12, "Take and Hold", "Immovable Object", "Purge the Foe", "Unstoppable Force"),
    (15, "Take and Hold", "Determined Acquisition", "Disruption", "Death Trap"),
    (18, "Take and Hold", "Purge and Secure", "Reconnaissance", "Reconnaissance Sweep"),
    (21, "Take and Hold", "Inescapable Dominion", "Priority Assets", "Secure Asset"),
    (24, "Purge the Foe", "Meatgrinder", "Purge the Foe", "Meatgrinder"),
    (27, "Purge the Foe", "Punishment", "Disruption", "Delaying Action"),
    (30, "Purge the Foe", "Consecrate", "Reconnaissance", "Triangulation"),
    (33, "Purge the Foe", "Destroyer's Wrath", "Priority Assets", "Vital Link"),
    (36, "Disruption", "Outmanoeuvre", "Disruption", "Outmanoeuvre"),
    (39, "Disruption", "Smoke and Mirrors", "Reconnaissance", "Surveil the Foe"),
    (42, "Disruption", "Locate and Deny", "Priority Assets", "Extract Relic"),
    (45, "Reconnaissance", "Gather Intel", "Reconnaissance", "Gather Intel"),
    (48, "Reconnaissance", "Search and Scour", "Priority Assets", "Vanguard Operation"),
    (51, "Priority Assets", "Sabotage", "Priority Assets", "Sabotage"),
)


def official_layout_metadata_for_page(page_number: int) -> OfficialLayoutMetadata | None:
    return OFFICIAL_LAYOUT_PAGE_METADATA.get(page_number)


def _metadata(
    page_number: int,
    layout_variant: str,
    first_disposition: str,
    first_mission: str,
    second_disposition: str,
    second_mission: str,
) -> OfficialLayoutMetadata:
    return OfficialLayoutMetadata(
        source_page=page_number,
        layout_variant=layout_variant,
        first_player=OfficialLayoutSide(
            force_disposition=first_disposition,
            primary_mission=first_mission,
        ),
        second_player=OfficialLayoutSide(
            force_disposition=second_disposition,
            primary_mission=second_mission,
        ),
    )


OFFICIAL_LAYOUT_PAGE_METADATA: dict[int, OfficialLayoutMetadata] = {
    start_page + offset: _metadata(
        start_page + offset,
        variant,
        first_disposition,
        first_mission,
        second_disposition,
        second_mission,
    )
    for start_page, first_disposition, first_mission, second_disposition, second_mission in (
        _LAYOUT_SERIES
    )
    for offset, variant in enumerate(_LAYOUT_VARIANTS)
}
