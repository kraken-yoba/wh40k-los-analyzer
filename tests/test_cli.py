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


def test_validate_packets_fails_when_no_packets_exist(tmp_path: Path) -> None:
    paths = IngestionPaths(tmp_path / "data")
    runner = CliRunner()

    result = runner.invoke(cli, ["validate-packets", "--data-dir", str(paths.data_dir)])

    assert result.exit_code == 1
    assert "No packet JSON files found" in result.output
