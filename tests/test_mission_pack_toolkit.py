from __future__ import annotations

import inspect

from warhammer_companion.application.mission_pack import (
    PUBLIC_MISSION_SHEET_GID,
    PUBLIC_MISSION_SHEET_ID,
    PUBLIC_MISSION_SHEET_URL,
    _mission_pack_hash,
    _mission_source_refs,
    build_mission_pack_toolkit_result,
)
from warhammer_companion.domain.missions import MissionSourceRef
from warhammer_companion.ingestion.official_layout_metadata import (
    OFFICIAL_LAYOUT_PAGE_METADATA,
)


def test_mission_pack_deduplicates_primary_missions_from_layout_metadata() -> None:
    result = build_mission_pack_toolkit_result()

    expected_labels = sorted(
        {
            metadata.first_player.primary_mission
            for metadata in OFFICIAL_LAYOUT_PAGE_METADATA.values()
        }
        | {
            metadata.second_player.primary_mission
            for metadata in OFFICIAL_LAYOUT_PAGE_METADATA.values()
        }
    )
    labels = [mission.label for mission in result.payload.pack.primary_missions]

    assert labels == expected_labels
    assert "Battlefield Dominance" in labels
    assert "Sabotage" in labels


def test_mission_pack_uses_stable_ids_source_refs_and_page_anchors() -> None:
    result = build_mission_pack_toolkit_result()

    mission = next(
        mission
        for mission in result.payload.pack.primary_missions
        if mission.label == "Battlefield Dominance"
    )

    assert mission.mission_id == "primary-battlefield-dominance"
    assert mission.category == "primary"
    assert mission.readiness == "estimated"
    assert "event-companion-layout-metadata" in mission.source_ref_ids
    assert mission.source_anchors
    assert {anchor.page_number for anchor in mission.source_anchors} == {9, 10, 11}
    assert all(
        anchor.source_ref_id == "event-companion-layout-metadata"
        for anchor in mission.source_anchors
    )


def test_mission_pack_result_is_estimated_source_safe_and_non_recommending() -> None:
    result = build_mission_pack_toolkit_result()
    warning_text = " ".join(warning.detail for warning in result.warnings).lower()

    assert result.tool_id == "mission_pack"
    assert result.readiness == "estimated"
    assert not result.overlays
    assert not result.allows_recommendation_language()
    assert "source-pending" in warning_text
    assert "not fetched" in warning_text
    assert "not ingested" in warning_text


def test_public_sheet_is_recorded_as_untrusted_candidate_metadata_only() -> None:
    result = build_mission_pack_toolkit_result()

    sheet_source = next(
        source
        for source in result.payload.source_refs
        if source.source_ref_id == "public-mission-sheet-candidate"
    )

    assert sheet_source.url == PUBLIC_MISSION_SHEET_URL
    assert sheet_source.sheet_id == PUBLIC_MISSION_SHEET_ID
    assert sheet_source.gid == PUBLIC_MISSION_SHEET_GID == "1565185881"
    assert sheet_source.retrieval_status == "not_fetched"
    assert sheet_source.trust == "untrusted_candidate"
    assert sheet_source.content_hash is None
    assert any("not fetched" in warning.lower() for warning in sheet_source.warnings)


def test_mission_pack_payload_omits_card_images_and_full_text() -> None:
    result = build_mission_pack_toolkit_result()

    serialized = repr(result.payload).lower()

    for forbidden in (
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        "lh3.googleusercontent.com",
        "drive.google.com/uc",
    ):
        assert forbidden not in serialized
    assert "secondary mission" not in serialized
    assert "mission card" not in serialized
    assert max(len(mission.label) for mission in result.payload.pack.primary_missions) <= 40


def test_mission_pack_housekeeping_preserves_default_identity_and_public_signature() -> None:
    result = build_mission_pack_toolkit_result()

    assert result.input_hash == (
        "sha256:01f1430011d73eec7f009f95dc8a4e5671b581dcdf7ecfdd0097020a5eefd2bc"
    )
    assert result.result_id == "estimated:mission-pack:01f1430011d7"
    assert list(inspect.signature(build_mission_pack_toolkit_result).parameters) == ["metadata"]


def test_mission_pack_warnings_share_canonical_text_between_pack_and_toolkit() -> None:
    result = build_mission_pack_toolkit_result()

    toolkit_warning_details = tuple(warning.detail for warning in result.warnings)

    assert result.payload.pack.warnings == toolkit_warning_details


def test_mission_pack_hash_uses_canonical_source_refs() -> None:
    source_refs = _mission_source_refs()
    base_hash = _mission_pack_hash(OFFICIAL_LAYOUT_PAGE_METADATA, source_refs=source_refs)
    changed_refs = tuple(
        _source_ref_with_gid(source, "999")
        if source.source_ref_id == "public-mission-sheet-candidate"
        else source
        for source in source_refs
    )

    changed_hash = _mission_pack_hash(OFFICIAL_LAYOUT_PAGE_METADATA, source_refs=changed_refs)

    assert base_hash == build_mission_pack_toolkit_result().input_hash
    assert changed_hash != base_hash


def _source_ref_with_gid(source: MissionSourceRef, gid: str) -> MissionSourceRef:
    return MissionSourceRef(
        source_ref_id=source.source_ref_id,
        label=source.label,
        source_kind=source.source_kind,
        trust=source.trust,
        retrieval_status=source.retrieval_status,
        url=source.url,
        sheet_id=source.sheet_id,
        gid=gid,
        content_hash=source.content_hash,
        warnings=source.warnings,
    )
