from __future__ import annotations

from pathlib import Path

import requests
import typer

from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.manifest import write_source_manifest
from warhammer_companion.ingestion.sources import OFFICIAL_SOURCES

cli = typer.Typer(help="Warhammer Tournament Companion utilities.")
DEFAULT_RAW_DIR = IngestionPaths().raw_dir


@cli.command()
def download_sources(target_dir: Path = DEFAULT_RAW_DIR) -> None:
    """Download official source PDFs into a local, ignored data directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    content_types: dict[str, str | None] = {}
    for source in OFFICIAL_SOURCES:
        target = target_dir / source.filename
        typer.echo(f"Downloading {source.label} -> {target}")
        with requests.get(source.url, stream=True, timeout=120) as response:
            response.raise_for_status()
            content_types[source.key] = response.headers.get("content-type")
            with target.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        handle.write(chunk)
    manifest_path = IngestionPaths(target_dir.parent).source_manifest_path
    write_source_manifest(
        OFFICIAL_SOURCES,
        target_dir,
        manifest_path,
        content_types=content_types,
    )
    typer.echo(f"Wrote source manifest -> {manifest_path}")
    typer.echo("Done.")


@cli.command()
def list_sources() -> None:
    """Print the official source registry."""
    for source in OFFICIAL_SOURCES:
        typer.echo(f"{source.key}: {source.label}")
        typer.echo(f"  {source.url}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
