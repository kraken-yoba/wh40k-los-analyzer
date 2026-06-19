from __future__ import annotations

from pathlib import Path
from typing import Annotated

import requests
import typer

from warhammer_companion.domain.packet_io import load_packet_directory
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.manifest import write_source_manifest
from warhammer_companion.ingestion.packet_builder import run_official_ingestion, validate_packet
from warhammer_companion.ingestion.sources import OFFICIAL_SOURCES
from warhammer_companion.rules.core_rules import build_core_rules_pack

cli = typer.Typer(help="Warhammer Tournament Companion utilities.")
DEFAULT_DATA_DIR = IngestionPaths().data_dir
DEFAULT_RAW_DIR = IngestionPaths().raw_dir
DataDirOption = Annotated[
    Path,
    typer.Option(
        "--data-dir",
        help="Data directory containing raw official PDFs and processed outputs.",
    ),
]
PacketDirOption = Annotated[
    Path | None,
    typer.Option(
        "--packet-dir",
        help=(
            "Validate packet JSON from this directory instead of the processed "
            "map packet directory under --data-dir."
        ),
    ),
]
IngestionPageOption = Annotated[
    list[int] | None,
    typer.Option(
        "--page",
        "-p",
        help="Event Companion page to ingest. Repeat for a subset smoke run.",
    ),
]
ClassifyFeaturesOption = Annotated[
    bool,
    typer.Option(
        "--classify-features/--skip-classifier",
        help=(
            "Generate local catalog classifier results before packet projection. "
            "Use --skip-classifier to preserve hand-authored visual results."
        ),
    ),
]


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


@cli.command("rules-pack")
def rules_pack() -> None:
    pack = build_core_rules_pack()
    typer.echo(f"{pack.rules_pack_id}: {pack.readiness.value}")
    for source in pack.source_documents:
        typer.echo(
            f"  source {source.source_ref.source_document_id}: {source.source_ref.local_filename}"
        )
    typer.echo("  concepts:")
    for concept in pack.concept_mappings:
        typer.echo(f"  - {concept.display_label} ({concept.concept_id})")


@cli.command()
def ingest_official(
    data_dir: DataDirOption = DEFAULT_DATA_DIR,
    page: IngestionPageOption = None,
    classify_features: ClassifyFeaturesOption = True,
) -> None:
    """Extract official PDFs and generate processed map packet JSON."""
    report = run_official_ingestion(
        paths=IngestionPaths(data_dir),
        layout_pages=page,
        classify_features=classify_features,
    )
    typer.echo(
        f"Generated {report.packet_count} packet(s) from {report.layout_count} layout(s) "
        f"in {report.duration_seconds:.2f}s."
    )
    typer.echo(f"Map packets -> {report.map_packets_dir}")
    typer.echo(f"Ingestion report -> {IngestionPaths(data_dir).ingestion_report_path}")


@cli.command()
def validate_packets(
    data_dir: DataDirOption = DEFAULT_DATA_DIR,
    packet_dir: PacketDirOption = None,
) -> None:
    """Validate generated map packet JSON against LOS ingestion invariants."""
    paths = IngestionPaths(data_dir)
    target_dir = packet_dir or paths.map_packets_dir
    packets = load_packet_directory(target_dir)
    if not packets:
        typer.echo(f"No packet JSON files found in {target_dir}")
        raise typer.Exit(1)

    has_errors = False
    for packet in packets:
        result = validate_packet(packet)
        if result.valid:
            typer.echo(f"{packet.id}: valid")
            continue
        has_errors = True
        typer.echo(f"{packet.id}: invalid")
        for error in result.errors:
            typer.echo(f"  - {error}")
    if has_errors:
        raise typer.Exit(1)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
