from __future__ import annotations

from collections.abc import Iterable
from os import PathLike
from pathlib import Path
from typing import Protocol

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.domain.packet_io import load_packet_directory
from warhammer_companion.sample_data import SAMPLE_PACKETS

PacketDirectory = str | PathLike[str]
PacketDirectorySignature = tuple[tuple[str, int, int], ...]


class MapRepository(Protocol):
    def list_packets(self) -> list[MapPacket]: ...

    def get_packet(self, packet_id: str) -> MapPacket: ...

    def default_packet(self) -> MapPacket: ...


class StaticMapRepository:
    """Repository backed by an in-memory collection of map packets."""

    def __init__(self, packets: Iterable[MapPacket]) -> None:
        self._packets: dict[str, MapPacket] = {}
        for packet in packets:
            if packet.id in self._packets:
                raise ValueError(f"Duplicate map packet id: {packet.id}")
            self._packets[packet.id] = packet

    def list_packets(self) -> list[MapPacket]:
        return sorted(self._packets.values(), key=lambda packet: packet.name)

    def get_packet(self, packet_id: str) -> MapPacket:
        try:
            return self._packets[packet_id]
        except KeyError as exc:
            raise KeyError(f"Unknown map packet: {packet_id}") from exc

    def default_packet(self) -> MapPacket:
        packets = self.list_packets()
        if not packets:
            raise RuntimeError("No map packets are available.")
        return packets[0]


class FileBackedMapRepository:
    """Repository backed by processed packet JSON files, with optional fallback packets."""

    def __init__(
        self,
        directory: PacketDirectory,
        fallback: Iterable[MapPacket] | None = None,
    ) -> None:
        self._directory = Path(directory)
        self._fallback = list(fallback) if fallback is not None else []
        self._signature = self._directory_signature()
        self._repository = self._load_repository()

    def list_packets(self) -> list[MapPacket]:
        self._reload_if_changed()
        return self._repository.list_packets()

    def get_packet(self, packet_id: str) -> MapPacket:
        self._reload_if_changed()
        return self._repository.get_packet(packet_id)

    def default_packet(self) -> MapPacket:
        self._reload_if_changed()
        return self._repository.default_packet()

    def reload(self) -> None:
        self._signature = self._directory_signature()
        self._repository = self._load_repository()

    def _reload_if_changed(self) -> None:
        signature = self._directory_signature()
        if signature == self._signature:
            return
        self._signature = signature
        self._repository = self._load_repository()

    def _load_repository(self) -> StaticMapRepository:
        packets = load_packet_directory(self._directory)
        if not packets:
            packets = self._fallback
        return StaticMapRepository(packets)

    def _directory_signature(self) -> PacketDirectorySignature:
        if not self._directory.exists():
            return ()
        return tuple(
            (path.name, path.stat().st_mtime_ns, path.stat().st_size)
            for path in sorted(self._directory.glob("*.json"))
            if path.is_file()
        )


class InMemoryMapRepository(StaticMapRepository):
    """Compatibility wrapper for current web code."""

    def __init__(self) -> None:
        super().__init__(SAMPLE_PACKETS)
