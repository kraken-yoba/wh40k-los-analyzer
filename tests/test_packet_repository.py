from __future__ import annotations

from pathlib import Path

import pytest

from warhammer_companion.domain.packet_io import (
    load_packet,
    load_packet_directory,
    write_packet,
)
from warhammer_companion.domain.repository import (
    FileBackedMapRepository,
    StaticMapRepository,
)
from warhammer_companion.sample_data import SAMPLE_PACKETS


def test_packet_json_round_trips_through_pydantic(tmp_path: Path) -> None:
    packet = SAMPLE_PACKETS[0]
    packet_path = tmp_path / "sample-layout-a.json"

    write_packet(packet, packet_path)

    assert load_packet(packet_path) == packet


def test_load_packet_directory_returns_packets_sorted_by_name(tmp_path: Path) -> None:
    alpha_packet = SAMPLE_PACKETS[0].model_copy(update={"id": "alpha", "name": "Alpha"})
    beta_packet = SAMPLE_PACKETS[0].model_copy(update={"id": "beta", "name": "Beta"})
    write_packet(beta_packet, tmp_path / "beta.json")
    write_packet(alpha_packet, tmp_path / "alpha.json")

    packets = load_packet_directory(tmp_path)

    assert [packet.id for packet in packets] == ["alpha", "beta"]


def test_file_backed_repository_lists_and_fetches_packets(tmp_path: Path) -> None:
    packet = SAMPLE_PACKETS[0].model_copy(update={"id": "official-a", "name": "Official A"})
    write_packet(packet, tmp_path / "official-a.json")

    repository = FileBackedMapRepository(tmp_path)

    assert repository.list_packets() == [packet]
    assert repository.default_packet() == packet
    assert repository.get_packet("official-a") == packet


def test_unknown_packets_raise_clear_key_errors(tmp_path: Path) -> None:
    packet = SAMPLE_PACKETS[0]
    write_packet(packet, tmp_path / "sample-layout-a.json")
    file_repository = FileBackedMapRepository(tmp_path)
    static_repository = StaticMapRepository([packet])

    with pytest.raises(KeyError, match="Unknown map packet: missing"):
        file_repository.get_packet("missing")
    with pytest.raises(KeyError, match="Unknown map packet: missing"):
        static_repository.get_packet("missing")


def test_file_backed_repository_uses_fallback_when_no_packets_exist(tmp_path: Path) -> None:
    repository = FileBackedMapRepository(tmp_path, fallback=SAMPLE_PACKETS)

    assert repository.list_packets() == SAMPLE_PACKETS
    assert repository.default_packet() == SAMPLE_PACKETS[0]


def test_file_backed_repository_auto_refreshes_when_packet_files_change(tmp_path: Path) -> None:
    repository = FileBackedMapRepository(tmp_path, fallback=SAMPLE_PACKETS)
    packet = SAMPLE_PACKETS[0].model_copy(update={"id": "official-a", "name": "Official A"})

    write_packet(packet, tmp_path / "official-a.json")

    assert repository.list_packets() == [packet]


def test_duplicate_packet_ids_raise_clear_errors() -> None:
    duplicate = SAMPLE_PACKETS[0].model_copy(update={"name": "Duplicate"})

    with pytest.raises(ValueError, match="Duplicate map packet id: sample-layout-a"):
        StaticMapRepository([SAMPLE_PACKETS[0], duplicate])


def test_load_packet_directory_returns_empty_list_for_missing_directory(tmp_path: Path) -> None:
    missing_directory = tmp_path / "processed" / "map-packets"

    assert load_packet_directory(missing_directory) == []
