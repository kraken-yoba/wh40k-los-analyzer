from __future__ import annotations

from warhammer_companion.application.movement_reach import build_movement_reach_toolkit_result
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_movement_reach_toolkit_result_is_estimated_and_non_recommending() -> None:
    result = build_movement_reach_toolkit_result(
        SAMPLE_PACKETS[0],
        start_center=(16.0, 10.0),
        target_center=(22.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
        mode="normal",
    )

    assert result.tool_id == "movement_reach"
    assert result.readiness == "estimated"
    assert not result.allows_recommendation_language()
    assert len(result.overlays) == 1
    assert result.overlays[0].layer_kind == "movement_envelope"
    assert result.payload.mode == "normal"
    assert result.payload.endpoint.estimated_reachable
    warning_text = " ".join(warning.detail.lower() for warning in result.warnings)
    assert "estimated 2d geometry" in warning_text
    for forbidden in ("legal", " safe", "recommended", "optimal", "likely"):
        assert forbidden not in warning_text


def test_movement_reach_toolkit_blocks_invalid_manual_inputs_without_overlays() -> None:
    result = build_movement_reach_toolkit_result(
        SAMPLE_PACKETS[0],
        start_center=(16.0, 10.0),
        target_center=(22.0, 10.0),
        base_diameter=0.0,
        move_distance=6.0,
        mode="normal",
    )

    assert result.readiness == "blocked"
    assert not result.overlays
    assert result.block_reasons
    assert result.block_reasons[0].reason_id == "invalid-base-diameter"


def test_movement_reach_toolkit_blocks_non_positive_movement_without_overlays() -> None:
    result = build_movement_reach_toolkit_result(
        SAMPLE_PACKETS[0],
        start_center=(16.0, 10.0),
        target_center=(22.0, 10.0),
        base_diameter=1.57,
        move_distance=0.0,
        mode="normal",
    )

    assert result.readiness == "blocked"
    assert not result.overlays
    assert {reason.reason_id for reason in result.block_reasons} == {"invalid-move-distance"}


def test_movement_reach_toolkit_identity_includes_packet_and_manual_inputs() -> None:
    packet = SAMPLE_PACKETS[0]
    changed_packet = packet.model_copy(update={"name": f"{packet.name} revised"})
    base = build_movement_reach_toolkit_result(
        packet,
        start_center=(16.0, 10.0),
        target_center=(22.0, 10.0),
        base_diameter=1.57,
        move_distance=6.0,
        mode="normal",
    )

    variants = [
        build_movement_reach_toolkit_result(
            changed_packet,
            start_center=(16.0, 10.0),
            target_center=(22.0, 10.0),
            base_diameter=1.57,
            move_distance=6.0,
            mode="normal",
        ),
        build_movement_reach_toolkit_result(
            packet,
            start_center=(17.0, 10.0),
            target_center=(22.0, 10.0),
            base_diameter=1.57,
            move_distance=6.0,
            mode="normal",
        ),
        build_movement_reach_toolkit_result(
            packet,
            start_center=(16.0, 10.0),
            target_center=(23.0, 10.0),
            base_diameter=1.57,
            move_distance=6.0,
            mode="normal",
        ),
        build_movement_reach_toolkit_result(
            packet,
            start_center=(16.0, 10.0),
            target_center=(22.0, 10.0),
            base_diameter=2.0,
            move_distance=6.0,
            mode="normal",
        ),
        build_movement_reach_toolkit_result(
            packet,
            start_center=(16.0, 10.0),
            target_center=(22.0, 10.0),
            base_diameter=1.57,
            move_distance=7.0,
            mode="normal",
        ),
        build_movement_reach_toolkit_result(
            packet,
            start_center=(16.0, 10.0),
            target_center=(22.0, 10.0),
            base_diameter=1.57,
            move_distance=6.0,
            mode="advance",
        ),
    ]

    hashes = {base.input_hash, *(variant.input_hash for variant in variants)}
    assert len(hashes) == 1 + len(variants)
    suffix = base.input_hash.removeprefix("sha256:")[:12]
    assert base.result_id.endswith(suffix)
    assert base.overlays[0].layer_id.endswith(suffix)
