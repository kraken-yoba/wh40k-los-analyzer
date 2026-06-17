from __future__ import annotations

from pathlib import Path

import requests
import typer

from warhammer_companion.ingestion.sources import OFFICIAL_SOURCES

cli = typer.Typer(help="Warhammer Tournament Companion utilities.")


@cli.command()
def download_sources(target_dir: Path = Path("data/raw")) -> None:
    """Download official source PDFs into a local, ignored data directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for source in OFFICIAL_SOURCES:
        target = target_dir / source.filename
        typer.echo(f"Downloading {source.label} -> {target}")
        with requests.get(source.url, stream=True, timeout=120) as response:
            response.raise_for_status()
            with target.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        handle.write(chunk)
    typer.echo("Done.")


@cli.command()
def list_sources() -> None:
    """Print the official source registry."""
    for source in OFFICIAL_SOURCES:
        typer.echo(f"{source.key}: {source.label}")
        typer.echo(f"  {source.url}")


def main() -> None:
    cli()
