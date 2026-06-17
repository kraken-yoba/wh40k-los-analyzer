# Warhammer Tournament Companion

Python-only MVP for Warhammer 40,000 terrain/map analysis, focused first on line-of-sight tooling.

The MVP is a lightweight server-rendered web app. It deliberately avoids frontend JavaScript so the core product remains portable to a later standalone Python desktop app.

## Current Scope

- Internal map model for a 44" x 60" battlefield.
- Terrain footprints, dense terrain features, and deployment zones.
- Server-rendered map viewer.
- LOS heatmap generated from a deployment zone.
- Base-aware LOS checker that places a model base and renders visibility rays.
- Official source registry for Games Workshop PDFs.
- Python package, CLI, tests, linting, and docs.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m warhammer_companion.app
```

Then open:

```text
http://127.0.0.1:8000
```

## Source Documents

Official PDFs are not committed. Download them into `data/raw/`:

```powershell
.\.venv\Scripts\python -m warhammer_companion.cli download-sources
```

The source URLs are recorded in `src/warhammer_companion/ingestion/sources.py`.

## Architecture

The app separates the durable domain engine from the temporary web shell:

- `domain/`: map packet models and geometry-neutral domain types.
- `los/`: visibility and heatmap algorithms.
- `rendering/`: SVG generation for maps and overlays.
- `ingestion/`: official source registry and future PDF/CV extraction pipeline.
- `web/`: server-rendered pages and forms.

This keeps the LOS and ingestion engine reusable when the MVP becomes a standalone app.

