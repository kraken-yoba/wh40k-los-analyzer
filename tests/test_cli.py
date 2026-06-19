from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from warhammer_companion.cli import cli
from warhammer_companion.domain.packet_io import write_packet
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_validate_packets_reports_valid_generated_packets(tmp_path: Path) -> None:
    paths = IngestionPaths(tmp_path / "data")
    write_packet(SAMPLE_PACKETS[0], paths.map_packets_dir / "sample-layout-a.json")
    runner = CliRunner()

    result = runner.invoke(cli, ["validate-packets", "--data-dir", str(paths.data_dir)])

    assert result.exit_code == 0
    assert "sample-layout-a: valid" in result.output


def test_validate_packets_accepts_explicit_packet_directory(tmp_path: Path) -> None:
    packet_dir = tmp_path / "seed-packets"
    write_packet(SAMPLE_PACKETS[0], packet_dir / "sample-layout-a.json")
    runner = CliRunner()

    result = runner.invoke(cli, ["validate-packets", "--packet-dir", str(packet_dir)])

    assert result.exit_code == 0
    assert "sample-layout-a: valid" in result.output


def test_validate_packets_fails_when_no_packets_exist(tmp_path: Path) -> None:
    paths = IngestionPaths(tmp_path / "data")
    runner = CliRunner()

    result = runner.invoke(cli, ["validate-packets", "--data-dir", str(paths.data_dir)])

    assert result.exit_code == 1
    assert "No packet JSON files found" in result.output


def test_rules_pack_outputs_core_rules_summary() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["rules-pack"])

    assert result.exit_code == 0
    assert "wh40k-11e-core-2026-06-01" in result.output
    assert "core-rules-2026-06-01" in result.output
    assert "Benefit of Cover" in result.output
    assert "trusted" in result.output
