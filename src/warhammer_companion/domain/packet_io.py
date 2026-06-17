from __future__ import annotations

from os import PathLike
from pathlib import Path

from warhammer_companion.domain.models import MapPacket

PacketPath = str | PathLike[str]


def load_packet(path: PacketPath) -> MapPacket:
    return MapPacket.model_validate_json(Path(path).read_text(encoding="utf-8"))


def write_packet(packet: MapPacket, path: PacketPath) -> None:
    packet_path = Path(path)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(f"{packet.model_dump_json(indent=2)}\n", encoding="utf-8")


def load_packet_directory(directory: PacketPath) -> list[MapPacket]:
    packet_directory = Path(directory)
    if not packet_directory.exists():
        return []
    if not packet_directory.is_dir():
        raise NotADirectoryError(str(packet_directory))

    packets = [load_packet(path) for path in packet_directory.glob("*.json")]
    return sorted(packets, key=lambda packet: packet.name)
