from __future__ import annotations

import hashlib
import importlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

from warhammer_companion.ingestion.sources import OfficialSource


@dataclass(frozen=True)
class SourceManifestEntry:
    source_key: str
    label: str
    url: str
    filename: str
    local_path: str
    byte_size: int
    sha256: str
    pdf_page_count: int
    content_type: str | None = None


def write_source_manifest(
    sources: Iterable[OfficialSource],
    raw_dir: Path,
    manifest_path: Path,
    content_types: Mapping[str, str | None] | None = None,
) -> list[SourceManifestEntry]:
    entries = [
        _entry_for_source(source, raw_dir / source.filename, content_types) for source in sources
    ]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"sources": [asdict(entry) for entry in entries]}
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return entries


def _entry_for_source(
    source: OfficialSource,
    local_path: Path,
    content_types: Mapping[str, str | None] | None,
) -> SourceManifestEntry:
    return SourceManifestEntry(
        source_key=source.key,
        label=source.label,
        url=source.url,
        filename=source.filename,
        local_path=str(local_path),
        byte_size=local_path.stat().st_size,
        sha256=_sha256(local_path),
        pdf_page_count=_pdf_page_count(local_path),
        content_type=None if content_types is None else content_types.get(source.key),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pdf_page_count(path: Path) -> int:
    fitz = cast(Any, importlib.import_module("fitz"))
    document = fitz.open(path)
    try:
        return int(document.page_count)
    finally:
        document.close()
