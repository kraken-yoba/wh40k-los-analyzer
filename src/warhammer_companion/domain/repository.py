from __future__ import annotations

from warhammer_companion.domain.models import MapPacket
from warhammer_companion.sample_data import SAMPLE_PACKETS


class InMemoryMapRepository:
    """Temporary repository boundary until packet persistence is designed."""

    def __init__(self) -> None:
        self._packets: dict[str, MapPacket] = {packet.id: packet for packet in SAMPLE_PACKETS}

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
