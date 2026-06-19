from __future__ import annotations

from pathlib import Path

from warhammer_companion.ingestion.artifacts import IngestionPaths

APP_AUTHOR = "WarhammerTournamentCompanion"
APP_NAME = "WarhammerTournamentCompanion"


def development_ingestion_paths(root: Path | None = None) -> IngestionPaths:
    """Return the repo-local data paths used by source checkouts and tests."""

    return IngestionPaths(root or Path("data"))
