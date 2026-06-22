from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

from warhammer_companion import __version__
from warhammer_companion.application.paths import default_desktop_ingestion_paths
from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.packet_io import load_packet_directory
from warhammer_companion.domain.repository import FileBackedMapRepository
from warhammer_companion.integrations.codex_backend import CodexBackend
from warhammer_companion.sample_data import SAMPLE_PACKETS

EXPECTED_OFFICIAL_PACKET_COUNT = 45
REQUIRED_OFFICIAL_PACKET_IDS = {
    "official-event-companion-page-9",
    "official-event-companion-page-53",
}


def build_desktop_service() -> WarhammerCompanionService:
    paths = default_desktop_ingestion_paths()
    repository = FileBackedMapRepository(
        paths.map_packets_dir,
        fallback=packaged_seed_packets(),
        merge_fallback=True,
    )
    return WarhammerCompanionService(
        paths=paths,
        repository=repository,
        codex_backend=CodexBackend(),
    )


def packaged_seed_packet_dir() -> Path:
    frozen_bundle_root = getattr(sys, "_MEIPASS", None)
    if frozen_bundle_root:
        return Path(frozen_bundle_root) / "warhammer_companion" / "seed_data" / "map-packets"
    return Path(__file__).resolve().parents[1] / "seed_data" / "map-packets"


def load_packaged_seed_packets() -> list[MapPacket]:
    return load_packet_directory(packaged_seed_packet_dir())


def packaged_seed_packets() -> list[MapPacket]:
    packets = load_packaged_seed_packets()
    return packets or SAMPLE_PACKETS


def smoke_test_summary(service: WarhammerCompanionService | None = None) -> dict[str, Any]:
    service = service or build_desktop_service()
    packets = service.repository.list_packets()
    packet_ids = {packet.id for packet in packets}
    bundled_seed_packets = load_packaged_seed_packets()
    viewer = service.viewer_state()
    heatmap = service.heatmap_state(
        packet_id=viewer.packet.id,
        zone_id="attacker",
        source="edge",
        offset_inches=0,
    )
    los = service.los_checker_state(packet_id=viewer.packet.id)
    movement_reach = service.movement_reach_state(packet_id=viewer.packet.id)
    threat_range = service.threat_range_state(packet_id=viewer.packet.id)
    hidden_coverage = service.hidden_coverage_state(packet_id=viewer.packet.id)
    return {
        "status": "ok",
        "packet_id": viewer.packet.id,
        "packet_count": len(packets),
        "bundled_seed_packet_count": len(bundled_seed_packets),
        "bundled_seed_packet_dir": str(packaged_seed_packet_dir()),
        "official_packet_count": len(
            [packet for packet in packets if packet.id.startswith("official-event-companion-page-")]
        ),
        "required_official_packets_present": REQUIRED_OFFICIAL_PACKET_IDS <= packet_ids,
        "viewer_svg": "<svg" in viewer.map_svg,
        "heatmap_svg": "<svg" in heatmap.map_svg,
        "los_svg": "<svg" in los.map_svg,
        "movement_reach_svg": "<svg" in movement_reach.map_svg,
        "threat_range_svg": "<svg" in threat_range.map_svg,
        "hidden_coverage_svg": "<svg" in hidden_coverage.map_svg,
        "dense_features": len(viewer.packet.dense_features),
        "light_features": len(viewer.packet.light_features),
        "deployment_zones": len(viewer.packet.deployment_zones),
    }


def official_data_available(summary: dict[str, Any]) -> bool:
    return (
        summary.get("official_packet_count", 0) >= EXPECTED_OFFICIAL_PACKET_COUNT
        and summary.get("required_official_packets_present") is True
    )


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
    parser.add_argument(
        "--require-official-data",
        action="store_true",
        help="Fail smoke test unless bundled official packets are available.",
    )
    parser.add_argument(
        "--smoke-output",
        type=Path,
        help="Write smoke-test JSON to this path instead of relying on console output.",
    )
    parser.add_argument("--version", action="store_true", help="Print the app version and exit.")
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0
    if args.smoke_test:
        summary = smoke_test_summary()
        summary_json = json.dumps(summary, sort_keys=True)
        if args.smoke_output:
            args.smoke_output.parent.mkdir(parents=True, exist_ok=True)
            args.smoke_output.write_text(f"{summary_json}\n", encoding="utf-8")
        else:
            print(summary_json)
        if args.require_official_data and not official_data_available(summary):
            return 2
        return 0
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
