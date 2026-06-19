from __future__ import annotations

import json
import sys
from pathlib import Path

from warhammer_companion.desktop.app import (
    main,
    official_data_available,
    packaged_seed_packet_dir,
    packaged_seed_packets,
    smoke_test_summary,
)


def test_desktop_smoke_summary_renders_core_states() -> None:
    summary = smoke_test_summary()

    assert summary["status"] == "ok"
    assert summary["packet_count"] == 45
    assert summary["bundled_seed_packet_count"] == 45
    assert summary["official_packet_count"] == 45
    assert summary["required_official_packets_present"] is True
    assert official_data_available(summary)
    assert summary["packet_id"] == "official-event-companion-page-9"
    assert summary["viewer_svg"]
    assert summary["heatmap_svg"]
    assert summary["los_svg"]
    assert summary["deployment_zones"] == 2


def test_desktop_smoke_test_entrypoint_outputs_json(capsys) -> None:
    exit_code = main(["--smoke-test"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ok"
    assert output["viewer_svg"]


def test_desktop_smoke_test_can_require_official_data(capsys) -> None:
    exit_code = main(["--smoke-test", "--require-official-data"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["official_packet_count"] == 45


def test_desktop_smoke_test_can_write_output_file(tmp_path: Path) -> None:
    smoke_output = tmp_path / "smoke.json"

    exit_code = main(
        [
            "--smoke-test",
            "--require-official-data",
            "--smoke-output",
            str(smoke_output),
        ]
    )

    assert exit_code == 0
    output = json.loads(smoke_output.read_text(encoding="utf-8"))
    assert output["bundled_seed_packet_count"] == 45


def test_official_data_available_rejects_sample_fallback() -> None:
    assert not official_data_available(
        {
            "official_packet_count": 0,
            "required_official_packets_present": False,
        }
    )


def test_desktop_version_entrypoint(capsys) -> None:
    exit_code = main(["--version"])

    assert exit_code == 0
    assert capsys.readouterr().out.strip()


def test_desktop_seed_packets_include_official_layouts() -> None:
    packets = packaged_seed_packets()
    packet_ids = {packet.id for packet in packets}

    assert len(packets) == 45
    assert "official-event-companion-page-9" in packet_ids
    assert "official-event-companion-page-53" in packet_ids


def test_desktop_seed_packet_dir_uses_pyinstaller_bundle_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert packaged_seed_packet_dir() == (
        tmp_path / "warhammer_companion" / "seed_data" / "map-packets"
    )
