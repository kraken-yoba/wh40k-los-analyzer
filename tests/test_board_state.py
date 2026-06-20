from __future__ import annotations

from warhammer_companion.domain.board_state import (
    BoardModel,
    BoardState,
    BoardUnit,
    map_packet_digest,
)
from warhammer_companion.los.geometry import visibility_polygon_from_base
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_board_state_from_packet_keeps_map_packet_layout_only() -> None:
    packet = SAMPLE_PACKETS[0]
    before = packet.model_dump()

    state = BoardState.from_packet(packet, state_id="state-page-9")

    assert state.packet is packet
    assert state.state_id == "state-page-9"
    assert state.readiness == "estimated"
    assert state.units == ()
    assert state.packet_digest == map_packet_digest(packet)
    assert state.warnings
    assert packet.model_dump() == before
    assert not hasattr(packet, "rules_pack")
    assert not hasattr(packet, "units")


def test_board_state_reports_missing_model_positions_and_base_sizes() -> None:
    packet = SAMPLE_PACKETS[0]
    unit = BoardUnit(
        unit_id="unit-1",
        label="Unit 1",
        controller="friendly",
        models=(
            BoardModel(model_id="m1", base_diameter=1.57, position=None),
            BoardModel(model_id="m2", base_diameter=None, position=(10.0, 10.0)),
        ),
    )

    state = BoardState.from_packet(packet, state_id="state-with-gaps", units=(unit,))

    assert state.readiness == "estimated"
    warning_text = " ".join(warning.detail for warning in state.warnings)
    assert "position" in warning_text
    assert "base size" in warning_text


def test_board_state_reports_units_without_models() -> None:
    packet = SAMPLE_PACKETS[0]
    unit = BoardUnit(
        unit_id="unit-1",
        label="Unit 1",
        controller="friendly",
        models=(),
    )

    state = BoardState.from_packet(packet, state_id="state-with-empty-unit", units=(unit,))

    assert state.readiness == "estimated"
    assert any("models" in warning.detail for warning in state.warnings)


def test_map_packet_digest_changes_when_packet_content_changes() -> None:
    packet = SAMPLE_PACKETS[0]
    renamed_packet = packet.model_copy(update={"name": f"{packet.name} revised"})

    assert map_packet_digest(renamed_packet) != map_packet_digest(packet)


def test_board_state_with_model_data_remains_estimated_until_rules_are_source_backed() -> None:
    packet = SAMPLE_PACKETS[0]
    unit = BoardUnit(
        unit_id="unit-1",
        label="Unit 1",
        controller="friendly",
        models=(BoardModel(model_id="m1", base_diameter=1.57, position=(22.0, 10.0)),),
    )

    state = BoardState.from_packet(packet, state_id="state-with-models", units=(unit,))

    assert state.readiness == "estimated"
    assert any("source-backed mechanics" in warning.detail for warning in state.warnings)


def test_phase_2_contracts_do_not_change_existing_los_geometry() -> None:
    packet = SAMPLE_PACKETS[0]

    before = visibility_polygon_from_base(packet, center=(22.0, 10.0), base_diameter=1.57)
    state = BoardState.from_packet(packet, state_id="state-los-regression")
    after = visibility_polygon_from_base(state.packet, center=(22.0, 10.0), base_diameter=1.57)

    assert after.equals_exact(before, tolerance=1e-9)
