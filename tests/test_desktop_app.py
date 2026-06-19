from __future__ import annotations

import json

from warhammer_companion.desktop.app import main, smoke_test_summary


def test_desktop_smoke_summary_renders_core_states() -> None:
    summary = smoke_test_summary()

    assert summary["status"] == "ok"
    assert summary["packet_count"] >= 1
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


def test_desktop_version_entrypoint(capsys) -> None:
    exit_code = main(["--version"])

    assert exit_code == 0
    assert capsys.readouterr().out.strip()
