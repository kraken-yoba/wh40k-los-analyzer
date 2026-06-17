# Warhammer 40k LOS Analyzer

Local Python tooling for deterministic visual analysis of Warhammer 40k table layouts, terrain footprints, deployment zones, and base-aware 2D line of sight.

## Status

This repository contains a working Python-only local web app for fixture-backed base-aware 2D LOS analysis plus official-PDF extraction evidence.

Implemented now:

- FastAPI-served GUI with layout/source status, validation records, click-on-map LOS, firing-lane heatmaps, deployment exposure, terrain contribution metrics, and export state.
- Deterministic canonical geometry models, validation records, source manifests, stable layout hashing, and JSON schema export.
- Hash-pinned source downloader for the official PDFs listed in the public-safe manifest, with verified local gitignored cache writes.
- Base-aware 2D LOS using deterministic disk sampling.
- Event Companion vector extraction for board, deployment zones, terrain placement candidates, and terrain category markers.
- Terrain Area Footprints vector extraction for footprint outlines, normalized footprint templates, provisional terrain-placement matches, and provisional Dense/Solid wall/blocker segments from matched footprint fragments.
- Core Rules terrain-semantics evidence that hash-checks the rules PDF, verifies short section anchors, and surfaces paraphrased LOS implications for Dense/Solid, Light/Exposed, and future 3D scope.
- Deterministic raster/CV sanity reports that compare extracted Event Companion geometry against rendered PDF page shapes and expose advisory vision-review status.
- Official extracted layouts remain warning-state by default; the local GUI can explicitly accept warnings for auditable degraded analysis without marking the geometry as clean.

Not implemented yet:

- Review-accepted LOS-ready official wall/blocker semantics for production analysis.
- Live vision-model advisory review of the deterministic CV sanity report. The current app prepares deterministic visual evidence and keeps model output out of canonical geometry.
- Full 3D-aware LOS. The current scope is base-aware 2D; future builds can add height/3D semantics after the deterministic 2D extraction chain is accepted.

## Source Policy

Official Warhammer PDFs and rules text are third-party source material and are not redistributed by this repository. The app stores source URLs and hashes in manifests, while downloaded PDFs and rendered pages stay in a local gitignored cache.

## Stack

- Python 3.12 local web app with FastAPI, Jinja2, Pydantic, PyMuPDF, OpenCV, Shapely, pytest, Ruff, mypy, and Python Playwright.
- Browser GUI served by FastAPI using templates, CSS, vanilla JavaScript, SVG, and Canvas.
- Public-safe GitHub Actions for linting, typing, unit tests, and synthetic fixtures.

## Development Commands

```powershell
.\scripts\verify.cmd
.\scripts\dev.cmd
```

The dev server defaults to `http://127.0.0.1:8765` to avoid common local ports.
Set `FORTYK_LOS_PORT` when another Codex thread or local app is already using that port:

```powershell
$env:FORTYK_LOS_PORT = "8766"
.\scripts\dev.cmd
```

Additional gates are split so public CI stays copyright-safe:

```powershell
.\scripts\verify-public.cmd
.\scripts\verify-gui.cmd
.\scripts\verify-full-local.cmd
```

Official PDF binaries are gitignored. Tests that depend on the pinned local PDF cache are marked optional and skip when `data/pdfs/*.pdf` is absent. With the local cache present, `.\scripts\verify.cmd` also runs the official hash-pinned extraction regressions.

## Local Official PDF Cache

Populate the local gitignored cache from the pinned official source manifest:

```powershell
.\scripts\download-sources.cmd
```

The downloader writes only under `data/pdfs`, skips already hash-matched files, streams downloads to temporary `.part` files with a size cap, revalidates redirect targets, and refuses to publish a download whose SHA-256 differs from the manifest. To download one document, pass its manifest id:

```powershell
.\scripts\download-sources.cmd --document-id event-companion-2026-06-12
```

The expected cache paths are:

```text
data/pdfs/terrainareafootprints.pdf
data/pdfs/event_companion.pdf
data/pdfs/core_rules.pdf
```

Expected URLs and SHA-256 hashes are stored in `fixtures/source_manifest.official.json`.
