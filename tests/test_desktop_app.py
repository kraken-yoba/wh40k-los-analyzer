from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from warhammer_companion.desktop.app import (
    main,
    official_data_available,
    packaged_seed_packet_dir,
    packaged_seed_packets,
    smoke_test_summary,
)
from warhammer_companion.domain.damage import (
    DEFAULT_DAMAGE_PROFILE_INPUT,
    DEFAULT_TARGET_PROFILE_INPUT,
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
    assert summary["hidden_coverage_svg"]
    assert summary["movement_reach_svg"]
    assert summary["threat_range_svg"]
    assert summary["deployment_exposure_svg"]
    assert summary["damage_profile_estimate"]
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


def test_desktop_viewer_screen_renders_map_pixmap() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())

    viewer = window.stack.widget(2)
    pixmap = viewer.map.rendered_pixmap()

    assert pixmap is not None
    assert not pixmap.isNull()
    assert pixmap.width() > 528
    assert pixmap.height() > 720
    assert viewer.map.image_label.width() == 528
    assert viewer.map.image_label.height() == 720
    window.close()
    app.processEvents()


def test_desktop_hidden_coverage_screen_renders_map_pixmap() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]

    assert "Hidden Coverage" in labels
    hidden_screen = window.stack.widget(labels.index("Hidden Coverage"))
    pixmap = hidden_screen.map.rendered_pixmap()

    assert pixmap is not None
    assert not pixmap.isNull()
    assert pixmap.width() > 528
    assert pixmap.height() > 720
    window.close()
    app.processEvents()


def test_desktop_movement_reach_screen_renders_map_pixmap() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]

    assert "Movement Reach" in labels
    movement_screen = window.stack.widget(labels.index("Movement Reach"))
    pixmap = movement_screen.map.rendered_pixmap()

    assert pixmap is not None
    assert not pixmap.isNull()
    assert pixmap.width() > 528
    assert pixmap.height() > 720
    window.close()
    app.processEvents()


def test_desktop_threat_range_screen_renders_map_pixmap() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]

    assert "Threat Range" in labels
    threat_screen = window.stack.widget(labels.index("Threat Range"))
    pixmap = threat_screen.map.rendered_pixmap()

    assert pixmap is not None
    assert not pixmap.isNull()
    assert pixmap.width() > 528
    assert pixmap.height() > 720
    status_text = threat_screen.status_label.text()
    assert "Source-backed rules pending" in status_text
    assert "No recommendations" in status_text
    window.close()
    app.processEvents()


def test_desktop_deployment_exposure_screen_renders_map_pixmap() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]

    assert "Deployment Exposure" in labels
    deployment_screen = window.stack.widget(labels.index("Deployment Exposure"))
    pixmap = deployment_screen.map.rendered_pixmap()

    assert pixmap is not None
    assert not pixmap.isNull()
    assert pixmap.width() > 528
    assert pixmap.height() > 720
    status_text = deployment_screen.status_label.text()
    assert "not a placement planner" in status_text
    assert "Not exposed under selected assumptions" in status_text
    window.close()
    app.processEvents()


def test_desktop_damage_profile_screen_reports_manual_estimate() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]

    assert "Damage Profile" in labels
    damage_screen = window.stack.widget(labels.index("Damage Profile"))
    status_text = damage_screen.status_label.text()

    assert damage_screen.attacks_input.value() == DEFAULT_DAMAGE_PROFILE_INPUT.attacks
    assert damage_screen.hit_input.value() == DEFAULT_DAMAGE_PROFILE_INPUT.hit_target
    assert damage_screen.wound_input.value() == DEFAULT_DAMAGE_PROFILE_INPUT.wound_target
    assert damage_screen.save_input.value() == DEFAULT_DAMAGE_PROFILE_INPUT.save_target
    assert (
        damage_screen.damage_input.value() == DEFAULT_DAMAGE_PROFILE_INPUT.damage_per_unsaved_wound
    )
    assert damage_screen.wounds_input.value() == DEFAULT_TARGET_PROFILE_INPUT.wounds_per_model
    assert damage_screen.models_input.value() == DEFAULT_TARGET_PROFILE_INPUT.model_count
    assert "Manual estimate" in status_text
    assert "Expected damage" in status_text
    assert "not roster-derived" in status_text
    assert "effective save supplied by user" in status_text
    window.close()
    app.processEvents()
