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
    assert summary["deployment_scorecard_estimate"]
    assert summary["damage_profile_estimate"]
    assert summary["mission_pack_estimate"]
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


def test_desktop_line_of_sight_screen_renders_both_modes() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]

    assert "Line of Sight" in labels
    assert "LOS Heatmap" not in labels
    assert "LOS Checker" not in labels
    los_screen = window.stack.widget(labels.index("Line of Sight"))

    los_screen.mode_combo.setCurrentIndex(los_screen.mode_combo.findData("heatmap"))
    los_screen.refresh()
    heatmap_pixmap = los_screen.map.rendered_pixmap()
    assert heatmap_pixmap is not None
    assert not heatmap_pixmap.isNull()

    los_screen.mode_combo.setCurrentIndex(los_screen.mode_combo.findData("checker"))
    los_screen.x_input.setValue(30.5)
    los_screen.y_input.setValue(24.0)
    los_screen.refresh()
    checker_pixmap = los_screen.map.rendered_pixmap()
    assert checker_pixmap is not None
    assert not checker_pixmap.isNull()

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


def test_desktop_movement_reach_screen_reports_profile_sensitive_status() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]
    movement_screen = window.stack.widget(labels.index("Movement Reach"))

    movement_screen.start_x_input.setValue(14.0)
    movement_screen.start_y_input.setValue(32.75)
    movement_screen.target_x_input.setValue(22.5)
    movement_screen.target_y_input.setValue(32.75)
    movement_screen.move_input.setValue(9.0)

    profile_ids = {
        movement_screen.profile_combo.itemData(index)
        for index in range(movement_screen.profile_combo.count())
    }
    assert profile_ids >= {
        "ground-non-mobile",
        "ground-mobile",
        "fly-take-to-skies",
        "fly-hover-take-to-skies",
    }

    movement_screen.profile_combo.setCurrentIndex(
        movement_screen.profile_combo.findData("ground-non-mobile")
    )
    movement_screen.refresh()
    non_mobile_status = movement_screen.status_label.text()
    assert "Ground non-mobile" in non_mobile_status
    assert "outside the estimated route distance" in non_mobile_status

    movement_screen.profile_combo.setCurrentIndex(
        movement_screen.profile_combo.findData("ground-mobile")
    )
    movement_screen.refresh()
    mobile_status = movement_screen.status_label.text()
    assert "Ground mobile / infantry" in mobile_status
    assert "route-connected under selected assumptions" in mobile_status

    movement_screen.profile_combo.setCurrentIndex(
        movement_screen.profile_combo.findData("fly-take-to-skies")
    )
    movement_screen.refresh()
    penalized_fly_status = movement_screen.status_label.text()
    assert "Fly: Take to the Skies" in penalized_fly_status
    assert "Effective movement: 7.00 in" in penalized_fly_status
    assert "outside the estimated route distance" in penalized_fly_status

    movement_screen.profile_combo.setCurrentIndex(
        movement_screen.profile_combo.findData("fly-hover-take-to-skies")
    )
    movement_screen.refresh()
    hover_fly_status = movement_screen.status_label.text()
    assert "Fly: Hover / no-cost Take to the Skies" in hover_fly_status
    assert "Effective movement: 9.00 in" in hover_fly_status
    assert "route-connected under selected assumptions" in hover_fly_status

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


def test_desktop_threat_range_screen_supports_deployment_zone_source() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]
    threat_screen = window.stack.widget(labels.index("Threat Range"))

    assert threat_screen.source_mode_combo.findData("deployment-zone") >= 0
    assert not threat_screen.source_x_input.isHidden()
    assert threat_screen.source_deployment_zone_combo.isHidden()
    threat_screen.source_mode_combo.setCurrentIndex(
        threat_screen.source_mode_combo.findData("deployment-zone")
    )
    assert threat_screen.source_x_input.isHidden()
    assert threat_screen.source_y_input.isHidden()
    assert not threat_screen.source_deployment_zone_combo.isHidden()
    threat_screen.source_deployment_zone_combo.setCurrentIndex(
        threat_screen.source_deployment_zone_combo.findData("attacker")
    )
    threat_screen.mode_combo.setCurrentIndex(threat_screen.mode_combo.findData("raw-range"))
    threat_screen.refresh()

    status_text = threat_screen.status_label.text()
    pixmap = threat_screen.map.rendered_pixmap()
    assert "Attacker deployment zone" in status_text
    assert pixmap is not None
    assert not pixmap.isNull()

    threat_screen.source_mode_combo.setCurrentIndex(
        threat_screen.source_mode_combo.findData("point")
    )
    assert not threat_screen.source_x_input.isHidden()
    assert threat_screen.source_deployment_zone_combo.isHidden()

    window.close()
    app.processEvents()


def test_desktop_threat_range_screen_reports_profile_sensitive_probability() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]
    threat_screen = window.stack.widget(labels.index("Threat Range"))

    threat_screen.source_x_input.setValue(14.0)
    threat_screen.source_y_input.setValue(32.75)
    threat_screen.target_x_input.setValue(22.5)
    threat_screen.target_y_input.setValue(32.75)
    threat_screen.move_input.setValue(9.0)
    threat_screen.threat_input.setValue(0.5)

    profile_ids = {
        threat_screen.profile_combo.itemData(index)
        for index in range(threat_screen.profile_combo.count())
    }
    assert profile_ids >= {
        "ground-non-mobile",
        "ground-mobile",
        "fly-take-to-skies",
        "fly-hover-take-to-skies",
    }

    threat_screen.profile_combo.setCurrentIndex(
        threat_screen.profile_combo.findData("ground-non-mobile")
    )
    threat_screen.refresh()
    non_mobile_status = threat_screen.status_label.text()
    assert "Ground non-mobile" in non_mobile_status
    assert "Target point probability: 0.0%" in non_mobile_status

    threat_screen.profile_combo.setCurrentIndex(
        threat_screen.profile_combo.findData("ground-mobile")
    )
    threat_screen.refresh()
    mobile_status = threat_screen.status_label.text()
    assert "Ground mobile / infantry" in mobile_status
    assert "Target point probability: 100.0%" in mobile_status

    threat_screen.profile_combo.setCurrentIndex(
        threat_screen.profile_combo.findData("fly-take-to-skies")
    )
    threat_screen.refresh()
    penalized_fly_status = threat_screen.status_label.text()
    assert "Fly: Take to the Skies" in penalized_fly_status
    assert "Effective movement: 7.00 in" in penalized_fly_status
    assert "Target point probability: 0.0%" in penalized_fly_status

    threat_screen.profile_combo.setCurrentIndex(
        threat_screen.profile_combo.findData("fly-hover-take-to-skies")
    )
    threat_screen.refresh()
    hover_fly_status = threat_screen.status_label.text()
    assert "Fly: Hover / no-cost Take to the Skies" in hover_fly_status
    assert "Effective movement: 9.00 in" in hover_fly_status
    assert "Target point probability: 100.0%" in hover_fly_status

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


def test_desktop_deployment_screens_report_enemy_profile_sensitive_probability() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]

    exposure_screen = window.stack.widget(labels.index("Deployment Exposure"))
    _configure_desktop_deployment_profile_case(exposure_screen)
    _assert_enemy_profile_status_changes(exposure_screen)

    scorecard_screen = window.stack.widget(labels.index("Deployment Scorecard"))
    _configure_desktop_deployment_profile_case(scorecard_screen)
    _assert_enemy_profile_status_changes(scorecard_screen)

    window.close()
    app.processEvents()


def test_desktop_deployment_scorecard_screen_reports_components_and_blockers() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    service = build_desktop_service()
    window = MainWindow(service)
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]

    assert "Deployment Scorecard" in labels
    scorecard_screen = window.stack.widget(labels.index("Deployment Scorecard"))
    status_text = scorecard_screen.status_label.text()
    component_text = scorecard_screen.component_list_label.text()

    assert "Deployment Scorecard" in labels
    assert "source-pending" in status_text.lower()
    assert "Mission readiness" in component_text
    assert "Turn order assumption" in component_text
    pixmap = scorecard_screen.map.rendered_pixmap()
    assert pixmap is not None
    assert not pixmap.isNull()

    blocked_state = service.deployment_scorecard_state(turn_order="alpha-strike")
    scorecard_screen._set_state(blocked_state)  # noqa: SLF001

    assert "blocked" in scorecard_screen.status_label.text().lower()
    assert "invalid-turn-order" in scorecard_screen.status_label.text()
    assert "Turn order must be going-first or going-second" in (
        scorecard_screen.component_list_label.text()
    )
    assert 'class="safe-zone-outline"' not in blocked_state.map_svg
    assert 'class="coverage-image"' not in blocked_state.map_svg
    assert 'class="threat-projection-image"' not in blocked_state.map_svg
    window.close()
    app.processEvents()


def _configure_desktop_deployment_profile_case(screen) -> None:
    screen.friendly_x_input.setValue(22.5)
    screen.friendly_y_input.setValue(32.75)
    screen.enemy_x_input.setValue(14.0)
    screen.enemy_y_input.setValue(32.75)
    screen.enemy_move_input.setValue(9.0)
    screen.enemy_threat_input.setValue(0.5)
    screen.enemy_mode_combo.setCurrentIndex(
        screen.enemy_mode_combo.findData("fixed-move-plus-range")
    )
    screen.exposure_mode_combo.setCurrentIndex(screen.exposure_mode_combo.findData("threat-only"))

    profile_ids = {
        screen.enemy_profile_combo.itemData(index)
        for index in range(screen.enemy_profile_combo.count())
    }
    assert profile_ids >= {
        "ground-non-mobile",
        "ground-mobile",
        "fly-take-to-skies",
        "fly-hover-take-to-skies",
    }


def _assert_enemy_profile_status_changes(screen) -> None:
    screen.enemy_profile_combo.setCurrentIndex(
        screen.enemy_profile_combo.findData("ground-non-mobile")
    )
    screen.refresh()
    non_mobile_status = screen.status_label.text()
    assert "Ground non-mobile" in non_mobile_status
    assert "Threat probability at center: 0.0%" in non_mobile_status

    screen.enemy_profile_combo.setCurrentIndex(screen.enemy_profile_combo.findData("ground-mobile"))
    screen.refresh()
    mobile_status = screen.status_label.text()
    assert "Ground mobile / infantry" in mobile_status
    assert "Threat probability at center: 100.0%" in mobile_status

    screen.enemy_profile_combo.setCurrentIndex(
        screen.enemy_profile_combo.findData("fly-take-to-skies")
    )
    screen.refresh()
    penalized_fly_status = screen.status_label.text()
    assert "Fly: Take to the Skies" in penalized_fly_status
    assert "Enemy effective movement: 7.00 in" in penalized_fly_status
    assert "Threat probability at center: 0.0%" in penalized_fly_status

    screen.enemy_profile_combo.setCurrentIndex(
        screen.enemy_profile_combo.findData("fly-hover-take-to-skies")
    )
    screen.refresh()
    hover_fly_status = screen.status_label.text()
    assert "Fly: Hover / no-cost Take to the Skies" in hover_fly_status
    assert "Enemy effective movement: 9.00 in" in hover_fly_status
    assert "Threat probability at center: 100.0%" in hover_fly_status


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


def test_desktop_mission_pack_screen_reports_source_safe_summary() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]

    assert "Mission Pack" in labels
    mission_screen = window.stack.widget(labels.index("Mission Pack"))
    status_text = mission_screen.status_label.text()
    mission_text = mission_screen.mission_list_label.text()

    assert "Source-pending" in status_text
    assert "not fetched" in status_text
    assert "Battlefield Dominance" in mission_text
    assert "Sabotage" in mission_text
    window.close()
    app.processEvents()


def test_desktop_team_pairing_screen_reports_degraded_matrix_and_blockers() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import Qt  # type: ignore[import-not-found]
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from warhammer_companion.desktop.app import build_desktop_service
    from warhammer_companion.desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(build_desktop_service())
    labels = [window.nav.item(index).text() for index in range(window.nav.count())]

    assert "Team Pairing" in labels
    pairing_screen = window.stack.widget(labels.index("Team Pairing"))
    status_text = pairing_screen.status_label.text()
    matrix_text = pairing_screen.matrix_detail_label.text()
    warning_text = pairing_screen.warning_label.text()
    range_text = pairing_screen.range_label.text()

    assert "degraded" in status_text.lower()
    assert "source-pending" in warning_text.lower()
    assert "unavailable" in warning_text.lower()
    assert "Alpha" in matrix_text
    assert "Gamma" in matrix_text
    assert "damage-output" in matrix_text
    assert "unsupported-data" in matrix_text
    assert "not_available" in matrix_text
    assert "not pair-specific" in matrix_text
    assert "Shared expected damage" in range_text
    assert pairing_screen.matrix_detail_label.textFormat() == Qt.TextFormat.PlainText
    assert pairing_screen.warning_label.textFormat() == Qt.TextFormat.PlainText
    assert pairing_screen.range_label.textFormat() == Qt.TextFormat.PlainText

    pairing_screen.friendly_lists_input.setPlainText("<script>alert(1)</script>")
    pairing_screen.opponent_lists_input.setPlainText("Gamma")
    pairing_screen.refresh()

    assert "<script>alert(1)</script>" in pairing_screen.matrix_detail_label.text()
    assert pairing_screen.matrix_detail_label.textFormat() == Qt.TextFormat.PlainText

    pairing_screen.friendly_lists_input.setPlainText("")
    pairing_screen.opponent_lists_input.setPlainText("Gamma")
    pairing_screen.refresh()

    assert "blocked" in pairing_screen.status_label.text().lower()
    assert "missing-friendly-lists" in pairing_screen.warning_label.text()
    assert "damage-output" not in pairing_screen.matrix_detail_label.text()
    window.close()
    app.processEvents()
