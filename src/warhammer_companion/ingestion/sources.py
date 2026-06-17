from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfficialSource:
    key: str
    label: str
    url: str
    filename: str
    purpose: str


OFFICIAL_SOURCES = (
    OfficialSource(
        key="terrain_footprints",
        label="Warhammer 40,000 Terrain Area Footprints",
        url=(
            "https://assets.warhammer-community.com/"
            "eng_12-06_warhammer40000_terrainareafootprints-biavo5zf9f-gxdahkydbj.pdf"
        ),
        filename="terrain-area-footprints.pdf",
        purpose="Extract canonical footprint shapes and dimensions.",
    ),
    OfficialSource(
        key="event_companion",
        label="Warhammer 40,000 Event Companion",
        url=(
            "https://assets.warhammer-community.com/"
            "eng_12-06_warhammer40000_event_companion-s3bfb5f9s1-ivswuij3fo.pdf"
        ),
        filename="event-companion.pdf",
        purpose="Extract official map layouts and deployment information.",
    ),
    OfficialSource(
        key="core_rules",
        label="Warhammer 40,000 Core Rules",
        url=(
            "https://assets.warhammer-community.com/"
            "eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf"
        ),
        filename="core-rules.pdf",
        purpose="Ground terrain and visibility rule profiles.",
    ),
)
