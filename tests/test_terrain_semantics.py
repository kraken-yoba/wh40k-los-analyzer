from __future__ import annotations

from warhammer_companion.application.terrain_semantics import build_terrain_semantics_result
from warhammer_companion.domain.base_sizes import BaseGeometry, BaseSizeRecord
from warhammer_companion.domain.board_state import map_packet_digest
from warhammer_companion.domain.semantics import (
    SemanticsValidationRecord,
    report_semantics_readiness,
)
from warhammer_companion.domain.terrain_semantics import TerrainSemanticsIndex
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_terrain_semantics_index_adapts_packet_without_mutating_it() -> None:
    packet = SAMPLE_PACKETS[0]
    before = packet.model_dump()

    index = TerrainSemanticsIndex.from_packet(
        packet,
        source_ref_ids=("map-packet:sample-layout-a",),
    )

    assert packet.model_dump() == before
    assert len(index.areas) == len(packet.terrain_areas)
    assert len(index.dense_features) == len(packet.dense_features)
    assert len(index.light_features) == len(packet.light_features)
    assert index.packet_id == packet.id
    assert index.packet_digest == map_packet_digest(packet)
    assert index.source_ref_ids == ("map-packet:sample-layout-a",)
    assert index.readiness_report().readiness == "estimated"
    assert not index.readiness_report().allows_trusted_claims()


def test_dense_feature_semantics_preserve_current_los_blocker_flags() -> None:
    packet = SAMPLE_PACKETS[0]
    before_blockers = [blocker.wkt for blocker in packet.blockers()]

    index = TerrainSemanticsIndex.from_packet(packet)

    dense_by_id = {record.element_id: record for record in index.dense_features}
    assert [blocker.wkt for blocker in packet.blockers()] == before_blockers
    for feature in packet.dense_features:
        assert dense_by_id[feature.id].blocks_los_2d == feature.blocks_los
        assert dense_by_id[feature.id].geometry.equals_exact(feature.polygon(), 1e-9)


def test_unknown_terrain_traits_and_vertical_assumptions_prevent_trusted_claims() -> None:
    index = TerrainSemanticsIndex.from_packet(SAMPLE_PACKETS[0])
    report = index.readiness_report(require_vertical_profile=True)

    warning_ids = {warning.warning_id for warning in report.warnings}
    assert "terrain-traits-source-pending" in warning_ids
    assert "vertical-profile-source-pending" in warning_ids
    assert not report.allows_trusted_claims()


def test_terrain_semantics_result_blocks_incompatible_source_pack() -> None:
    result = build_terrain_semantics_result(
        SAMPLE_PACKETS[0],
        source_pack_version="rules-pack-a",
        source_pack_compatible=False,
    )

    assert result.readiness == "blocked"
    assert result.is_blocked
    assert not result.overlays
    assert any(reason.reason_id == "incompatible-source-pack" for reason in result.block_reasons)
    assert not result.allows_recommendation_language()


def test_terrain_semantics_result_blocks_stale_source_freshness() -> None:
    result = build_terrain_semantics_result(
        SAMPLE_PACKETS[0],
        source_pack_version="rules-pack-a",
        source_freshness="stale",
    )

    assert result.readiness == "blocked"
    assert result.is_blocked
    assert not result.overlays
    assert any(reason.reason_id == "stale-source-pack" for reason in result.block_reasons)
    assert not result.allows_recommendation_language()


def test_trusted_semantics_require_source_refs_passed_validation_and_current_compatibility() -> (
    None
):
    trusted_record = BaseSizeRecord(
        record_id="trusted-base",
        label="Trusted base",
        source_kind="profile_pack",
        geometry=BaseGeometry.round(diameter_inches=1.57),
        readiness="trusted",
        source_ref_ids=("profile-pack:base-size",),
        freshness="current",
        compatibility="compatible",
        validation_records=(
            SemanticsValidationRecord(
                validator_id="base-pack-review",
                status="passed",
                detail="Base profile validation passed.",
                source_ref_ids=("profile-pack:base-size",),
            ),
        ),
    )
    missing_source = BaseSizeRecord(
        record_id="trusted-base-without-source",
        label="Trusted base without source",
        source_kind="profile_pack",
        geometry=BaseGeometry.round(diameter_inches=1.57),
        readiness="trusted",
        source_ref_ids=(),
        freshness="current",
        compatibility="compatible",
        validation_records=trusted_record.validation_records,
    )
    missing_validation = BaseSizeRecord(
        record_id="trusted-base-without-validation",
        label="Trusted base without validation",
        source_kind="profile_pack",
        geometry=BaseGeometry.round(diameter_inches=1.57),
        readiness="trusted",
        source_ref_ids=("profile-pack:base-size",),
        freshness="current",
        compatibility="compatible",
        validation_records=(),
    )
    stale = BaseSizeRecord(
        record_id="trusted-stale-base",
        label="Trusted stale base",
        source_kind="profile_pack",
        geometry=BaseGeometry.round(diameter_inches=1.57),
        readiness="trusted",
        source_ref_ids=("profile-pack:base-size",),
        freshness="stale",
        compatibility="compatible",
        validation_records=trusted_record.validation_records,
    )
    incompatible = BaseSizeRecord(
        record_id="trusted-incompatible-base",
        label="Trusted incompatible base",
        source_kind="profile_pack",
        geometry=BaseGeometry.round(diameter_inches=1.57),
        readiness="trusted",
        source_ref_ids=("profile-pack:base-size",),
        freshness="current",
        compatibility="incompatible",
        validation_records=trusted_record.validation_records,
    )

    assert report_semantics_readiness(base_records=(trusted_record,)).allows_trusted_claims()
    assert report_semantics_readiness(base_records=(missing_source,)).readiness == "degraded"
    assert not report_semantics_readiness(base_records=(missing_source,)).allows_trusted_claims()
    assert report_semantics_readiness(base_records=(missing_validation,)).readiness == "degraded"
    assert not report_semantics_readiness(
        base_records=(missing_validation,)
    ).allows_trusted_claims()
    assert report_semantics_readiness(base_records=(stale,)).readiness == "blocked"
    assert report_semantics_readiness(base_records=(incompatible,)).readiness == "blocked"


def test_mixed_trusted_records_require_each_record_to_have_source_and_validation() -> None:
    validation = SemanticsValidationRecord(
        validator_id="base-pack-review",
        status="passed",
        detail="Base profile validation passed.",
        source_ref_ids=("profile-pack:base-size",),
    )
    valid_trusted = BaseSizeRecord(
        record_id="trusted-base",
        label="Trusted base",
        source_kind="profile_pack",
        geometry=BaseGeometry.round(diameter_inches=1.57),
        readiness="trusted",
        source_ref_ids=("profile-pack:base-size",),
        freshness="current",
        compatibility="compatible",
        validation_records=(validation,),
    )
    invalid_trusted = BaseSizeRecord(
        record_id="trusted-without-own-proof",
        label="Trusted without own proof",
        source_kind="profile_pack",
        geometry=BaseGeometry.round(diameter_inches=1.26),
        readiness="trusted",
        source_ref_ids=(),
        freshness="current",
        compatibility="compatible",
        validation_records=(),
    )

    report = report_semantics_readiness(base_records=(valid_trusted, invalid_trusted))

    assert report.readiness == "degraded"
    assert not report.allows_trusted_claims()
    warning_ids = {warning.warning_id for warning in report.warnings}
    assert "trusted-source-refs-missing" in warning_ids
    assert "trusted-validation-missing" in warning_ids


def test_terrain_semantics_result_hash_changes_with_packet_or_source_version() -> None:
    packet = SAMPLE_PACKETS[0]
    renamed_packet = packet.model_copy(update={"name": f"{packet.name} revised"})

    original = build_terrain_semantics_result(
        packet,
        source_pack_version="rules-pack-a",
    )
    changed_packet = build_terrain_semantics_result(
        renamed_packet,
        source_pack_version="rules-pack-a",
    )
    changed_source = build_terrain_semantics_result(
        packet,
        source_pack_version="rules-pack-b",
    )

    assert original.readiness == "estimated"
    assert changed_packet.readiness == "estimated"
    assert changed_source.readiness == "estimated"
    assert original.input_hash != changed_packet.input_hash
    assert original.input_hash != changed_source.input_hash


def test_terrain_semantics_result_hash_changes_with_source_refs_or_freshness() -> None:
    packet = SAMPLE_PACKETS[0]

    source_a = build_terrain_semantics_result(
        packet,
        source_ref_ids=("map-packet:source-a",),
        source_pack_version="rules-pack-a",
        source_freshness="unknown",
    )
    source_b = build_terrain_semantics_result(
        packet,
        source_ref_ids=("map-packet:source-b",),
        source_pack_version="rules-pack-a",
        source_freshness="unknown",
    )
    current = build_terrain_semantics_result(
        packet,
        source_ref_ids=("map-packet:source-a",),
        source_pack_version="rules-pack-a",
        source_freshness="current",
    )

    assert source_a.input_hash != source_b.input_hash
    assert source_a.input_hash != current.input_hash
