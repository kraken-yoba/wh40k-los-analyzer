from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IngestionPaths:
    data_dir: Path = Path("data")

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def source_manifest_path(self) -> Path:
        return self.processed_dir / "source-manifest.json"

    @property
    def map_packets_dir(self) -> Path:
        return self.processed_dir / "map-packets"
