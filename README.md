# Warhammer 40k LOS Analyzer

Local tooling for deterministic visual analysis of Warhammer 40k table layouts, terrain footprints, deployment zones, and base-aware 2D line of sight.

## Status

This repository is in infrastructure setup. The extraction and LOS engines are planned but not implemented yet.

## Source Policy

Official Warhammer PDFs and rules text are third-party source material and are not redistributed by this repository. The app stores source URLs and hashes in manifests, while downloaded PDFs and rendered pages stay in a local gitignored cache.

## Planned Stack

- Python 3.12 backend with FastAPI, Pydantic, PyMuPDF, OpenCV, Shapely, pytest, Ruff, and mypy.
- TypeScript frontend with React, Vite, Zod, Vitest, and Playwright.
- Public-safe GitHub Actions for linting, typing, unit tests, and synthetic fixtures.

## Development Commands

```powershell
.\scripts\verify.ps1
```

The full official-PDF regression gate requires a local pinned PDF cache and is intentionally separate from public-safe CI.
