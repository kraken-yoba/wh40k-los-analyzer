from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

from warhammer_companion.ingestion.artifacts import IngestionPaths

APP_AUTHOR = "WarhammerTournamentCompanion"
APP_NAME = "WarhammerTournamentCompanion"


def development_ingestion_paths(root: Path | None = None) -> IngestionPaths:
    """Return the repo-local data paths used by source checkouts and tests."""

    return IngestionPaths(root or Path("data"))


def packaged_data_root() -> Path:
    """Return a user-writable app data root for installed desktop builds."""

    try:
        platformdirs = importlib.import_module("platformdirs")
        user_data_path = cast(Callable[..., Path], platformdirs.user_data_path)
        root = user_data_path(APP_NAME, APP_AUTHOR, ensure_exists=True)
    except ImportError:
        root = _fallback_user_data_root()
        root.mkdir(parents=True, exist_ok=True)
    return root


def packaged_ingestion_paths() -> IngestionPaths:
    return IngestionPaths(packaged_data_root() / "data")


def default_desktop_ingestion_paths() -> IngestionPaths:
    if getattr(sys, "frozen", False):
        return packaged_ingestion_paths()
    return development_ingestion_paths()


def _fallback_user_data_root() -> Path:
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"
    return base / APP_NAME
