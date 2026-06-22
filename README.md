# Warhammer Tournament Companion

Python-first MVP for Warhammer 40,000 terrain/map analysis, focused first on line-of-sight tooling.

The MVP is a lightweight server-rendered web app with a development PySide6 desktop shell. LOS,
ingestion, geometry, rendering, and toolkit state are Python-owned so the core product remains
portable between web and standalone desktop app surfaces. The current web MVP uses no custom
frontend JavaScript.

## Current Scope

- Internal map model for a 44" x 60" battlefield.
- Terrain footprints, dense terrain features, and deployment zones.
- Server-rendered map viewer.
- LOS heatmap generated from a deployment zone.
- Base-aware LOS checker that places a model base and renders visibility rays.
- Movement reach, hidden coverage, threat range, deployment exposure, deployment scorecard,
  manual damage profile diagnostics, mission-pack provenance records, and a labels-only Team
  Pairing Matrix dossier.
- Official source registry for Games Workshop PDFs.
- Python package, CLI, desktop smoke test, tests, linting, and docs.

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

Useful toolkit routes:

- `/viewer`
- `/heatmap`
- `/los-checker`
- `/movement-reach`
- `/hidden-coverage`
- `/threat-range`
- `/deployment-exposure`
- `/deployment-scorecard`
- `/damage-profile`
- `/mission-pack`
- `/team-pairing`

Desktop smoke:

```powershell
.\.venv\Scripts\python -m warhammer_companion.desktop.app --smoke-test
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
- `application/`: reusable workflow and toolkit state services.
- `los/`: visibility and heatmap algorithms.
- `rendering/`: SVG generation for maps and overlays.
- `ingestion/`: official source registry and future PDF/CV extraction pipeline.
- `web/`: server-rendered pages and forms.
- `desktop/`: PySide6 screens backed by the shared application services.

This keeps the LOS, ingestion, geometry, rendering, and toolkit engine reusable across web and
desktop surfaces.
