# Warhammer 40k LOS Analyzer

Local Python tooling for deterministic visual analysis of Warhammer 40k table layouts, terrain footprints, deployment zones, and base-aware 2D line of sight.

## Status

This repository is in infrastructure setup. The next implementation milestone is the deterministic data spine: source manifests, canonical geometry schemas, synthetic fixtures, validation records, and stable exports.

## Source Policy

Official Warhammer PDFs and rules text are third-party source material and are not redistributed by this repository. The app stores source URLs and hashes in manifests, while downloaded PDFs and rendered pages stay in a local gitignored cache.

## Planned Stack

- Python 3.12 local web app with FastAPI, Jinja2, Pydantic, PyMuPDF, OpenCV, Shapely, pytest, Ruff, mypy, and Python Playwright.
- Browser GUI served by FastAPI using templates, CSS, vanilla JavaScript, SVG, and Canvas.
- Public-safe GitHub Actions for linting, typing, unit tests, and synthetic fixtures.

## Development Commands

```powershell
.\scripts\verify.cmd
.\scripts\dev.cmd
```

Additional gates are split so public CI stays copyright-safe:

```powershell
.\scripts\verify-public.cmd
.\scripts\verify-gui.cmd
.\scripts\verify-full-local.cmd
```

The full official-PDF regression gate requires a local pinned PDF cache and is intentionally separate from public-safe CI. Use `verify-full-local.cmd -RequireOfficialPdfRegression` once the official-cache regression harness exists.
