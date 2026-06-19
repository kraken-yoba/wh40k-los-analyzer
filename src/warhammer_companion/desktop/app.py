from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any

from warhammer_companion import __version__
from warhammer_companion.application.paths import default_desktop_ingestion_paths
from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.domain.repository import FileBackedMapRepository
from warhammer_companion.integrations.codex_backend import CodexBackend
from warhammer_companion.sample_data import SAMPLE_PACKETS


def build_desktop_service() -> WarhammerCompanionService:
    paths = default_desktop_ingestion_paths()
    repository = FileBackedMapRepository(paths.map_packets_dir, fallback=SAMPLE_PACKETS)
    return WarhammerCompanionService(
        paths=paths,
        repository=repository,
        codex_backend=CodexBackend(),
    )


def smoke_test_summary(service: WarhammerCompanionService | None = None) -> dict[str, Any]:
    service = service or build_desktop_service()
    viewer = service.viewer_state()
    heatmap = service.heatmap_state(
        packet_id=viewer.packet.id,
        zone_id="attacker",
        source="edge",
        offset_inches=0,
    )
    los = service.los_checker_state(packet_id=viewer.packet.id)
    return {
        "status": "ok",
        "packet_id": viewer.packet.id,
        "packet_count": len(service.repository.list_packets()),
        "viewer_svg": "<svg" in viewer.map_svg,
        "heatmap_svg": "<svg" in heatmap.map_svg,
        "los_svg": "<svg" in los.map_svg,
        "dense_features": len(viewer.packet.dense_features),
        "light_features": len(viewer.packet.light_features),
        "deployment_zones": len(viewer.packet.deployment_zones),
    }


def run_gui(service: WarhammerCompanionService | None = None) -> int:
    from warhammer_companion.desktop.main_window import MainWindow

    qt_widgets = importlib.import_module("PySide6.QtWidgets")
    application_type = qt_widgets.QApplication
    app = application_type(sys.argv)
    app.setApplicationName("Warhammer Tournament Companion")
    app.setOrganizationName("WarhammerTournamentCompanion")
    window = MainWindow(service or build_desktop_service())
    window.show()
    return int(app.exec())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="warhammer-companion-desktop")
    parser.add_argument(
        "--smoke-test", action="store_true", help="Run a non-GUI desktop smoke test."
    )
    parser.add_argument("--version", action="store_true", help="Print the app version and exit.")
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0
    if args.smoke_test:
        print(json.dumps(smoke_test_summary(), sort_keys=True))
        return 0
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
