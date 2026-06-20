from __future__ import annotations

import hashlib

from warhammer_companion.application.los_toolkit import build_los_checker_toolkit_result
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_build_los_checker_toolkit_result_preserves_phase_2_contract() -> None:
    packet = SAMPLE_PACKETS[0]
    before = packet.model_dump()

    result = build_los_checker_toolkit_result(
        packet,
        center=(22.0, 10.0),
        base_diameter=1.57,
    )

    expected_hash = _expected_los_input_hash(
        packet_digest=result.payload.board_state.packet_digest,
        center=(22.0, 10.0),
        base_diameter=1.57,
    )
    suffix = expected_hash.removeprefix("sha256:")[:12]
    assert result.tool_id == "los_checker"
    assert result.result_id == f"{packet.id}:los-checker:{suffix}"
    assert result.input_hash == expected_hash
    assert result.readiness == "estimated"
    assert result.assumptions[0].assumption_id == "two-dimensional-los"
    assert result.assumptions[0].detail == (
        "LOS uses current two-dimensional dense terrain geometry."
    )
    warning_ids = {warning.warning_id for warning in result.warnings}
    assert warning_ids == {"missing-units", "source-backed-los-mechanics-pending"}
    assert any(
        warning.detail == "LOS output is diagnostic until source-backed visibility mechanics exist."
        for warning in result.warnings
    )
    assert result.payload.packet is packet
    assert result.payload.center == (22.0, 10.0)
    assert result.payload.base_diameter == 1.57
    assert result.payload.rays
    assert result.payload.board_state.packet_digest.startswith("sha256:")
    overlay = result.overlays[0]
    assert overlay.layer_id == f"{packet.id}:los-coverage:{suffix}"
    assert overlay.layer_kind == "line_of_sight_coverage"
    assert overlay.geometry is result.payload.coverage_polygon
    assert overlay.units == "battlefield_inches"
    assert overlay.style_token == "los-coverage-estimated"
    assert overlay.label == "Estimated LOS coverage"
    assert overlay.readiness == "estimated"
    assert not result.allows_recommendation_language()
    assert packet.model_dump() == before


def _expected_los_input_hash(
    *,
    packet_digest: str,
    center: tuple[float, float],
    base_diameter: float,
) -> str:
    payload = (
        "los-checker-toolkit/v0|los_checker|"
        f"{packet_digest}|{center[0]:.6f}|{center[1]:.6f}|{base_diameter:.6f}"
    )
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
