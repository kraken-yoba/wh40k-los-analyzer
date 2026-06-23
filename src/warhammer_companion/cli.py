from __future__ import annotations

from pathlib import Path
from typing import Annotated

import requests
import typer

from warhammer_companion.application.tts_external_editor import (
    TtsExternalEditorClient,
    render_lua_probe_template,
    resolve_reviewed_lua_template,
)
from warhammer_companion.domain.packet_io import load_packet_directory
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.ingestion.manifest import write_source_manifest
from warhammer_companion.ingestion.packet_builder import run_official_ingestion, validate_packet
from warhammer_companion.ingestion.sources import OFFICIAL_SOURCES

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
TtsScriptFileOption = Annotated[
    Path,
    typer.Option(
        "--script-file",
        help="Reviewed Lua template file to execute through the TTS External Editor API.",
    ),
]
TtsReceiptOption = Annotated[
    str,
    typer.Option(
        "--receipt",
        help="Short sanitized receipt id used to distinguish the TTS-originated request.",
    ),
]
CompanionBaseUrlOption = Annotated[
    str,
    typer.Option(
        "--companion-base-url",
        help="Local companion base URL substituted into the reviewed Lua template.",
    ),
]
TtsExternalEditorHostOption = Annotated[
    str,
    typer.Option(
        "--host",
        help="TTS External Editor API host.",
    ),
]
TtsExternalEditorPortOption = Annotated[
    int,
    typer.Option(
        "--port",
        help="TTS External Editor API port.",
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


@cli.command()
def tts_execute_lua(
    script_file: TtsScriptFileOption,
    receipt: TtsReceiptOption,
    companion_base_url: CompanionBaseUrlOption = "http://127.0.0.1:8000",
    host: TtsExternalEditorHostOption = "127.0.0.1",
    port: TtsExternalEditorPortOption = 39999,
) -> None:
    """Execute a reviewed Lua proof template through TTS's External Editor API."""
    try:
        reviewed_script_file = resolve_reviewed_lua_template(
            script_file,
            project_root=Path.cwd(),
        )
        script = render_lua_probe_template(
            reviewed_script_file,
            companion_base_url=companion_base_url,
            receipt=receipt,
        )
        TtsExternalEditorClient(host=host, port=port).execute_lua(script)
    except (OSError, ValueError) as exc:
        typer.echo(f"TTS External Editor proof failed: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(
        f"Sent TTS External Editor Execute Lua message to {host}:{port} with receipt {receipt}. "
        "Verify the companion receipt before treating the proof as live."
    )


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
