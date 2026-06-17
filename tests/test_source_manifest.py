from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import fitz

from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.manifest import SourceManifestEntry, write_source_manifest
from warhammer_companion.ingestion.sources import OfficialSource


def _write_pdf(path: Path, page_count: int) -> None:
    document = fitz.open()
    try:
        for _ in range(page_count):
            document.new_page()
        document.save(path)
    finally:
        document.close()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_ingestion_paths_default_to_ignored_data_directories() -> None:
    paths = IngestionPaths()

    assert paths.data_dir == Path("data")
    assert paths.raw_dir == Path("data/raw")
    assert paths.processed_dir == Path("data/processed")
    assert paths.source_manifest_path == Path("data/processed/source-manifest.json")
    assert paths.map_packets_dir == Path("data/processed/map-packets")


def test_write_source_manifest_records_local_pdf_metadata(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "processed" / "source-manifest.json"
    raw_dir.mkdir()
    pdf_path = raw_dir / "local-source.pdf"
    _write_pdf(pdf_path, page_count=3)
    source = OfficialSource(
        key="local_source",
        label="Local Source",
        url="https://example.com/local-source.pdf",
        filename=pdf_path.name,
        purpose="Exercise source manifest generation.",
    )

    entries = write_source_manifest([source], raw_dir, manifest_path)

    assert entries == [
        SourceManifestEntry(
            source_key="local_source",
            label="Local Source",
            url="https://example.com/local-source.pdf",
            filename="local-source.pdf",
            local_path=str(pdf_path),
            byte_size=pdf_path.stat().st_size,
            sha256=_sha256(pdf_path),
            pdf_page_count=3,
            content_type=None,
        )
    ]
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload == {
        "sources": [
            {
                "source_key": "local_source",
                "label": "Local Source",
                "url": "https://example.com/local-source.pdf",
                "filename": "local-source.pdf",
                "local_path": str(pdf_path),
                "byte_size": pdf_path.stat().st_size,
                "sha256": _sha256(pdf_path),
                "pdf_page_count": 3,
                "content_type": None,
            }
        ]
    }


def test_cli_module_invocation_runs_typer_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "warhammer_companion.cli", "download-sources", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Download official source PDFs" in result.stdout
