# Official Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an official-PDF ingestion path that downloads/caches Games Workshop source PDFs, extracts official terrain/layout geometry into persisted `MapPacket` JSON files, and makes those packets usable in the existing map viewer, LOS heatmap, and LOS checker.

**Architecture:** Keep `MapPacket` as the durable runtime contract. Isolate PDF/CV/provenance logic under `warhammer_companion.ingestion`, persist generated packet JSON under `data/processed/map-packets`, and load those packets through a file-backed repository with the sample packet retained only as fallback.

**Tech Stack:** Python 3.12, PyMuPDF, OpenCV, NumPy, Pillow, Shapely, Pydantic, FastAPI/Jinja, Typer, pytest, ruff, mypy.

---

## Acceptance Criteria

- Official source PDFs are downloaded to `data/raw` and recorded in a manifest with URL, byte size, SHA256, content type when available, and page count.
- The terrain-footprint PDF produces a footprint library artifact with extracted green-outline polygons, source page, source bbox, snapped approximate dimensions, and warnings/confidence.
- The Event Companion PDF produces official-derived map packets for layout pages with board transform, deployment zones, terrain areas, dense/light terrain features, page provenance, and validation warnings.
- Generated packet JSON files round-trip through the repository and appear in `/map-data`, `/viewer`, `/heatmap`, and `/los-checker`.
- Visual review overlays are generated for each extracted layout page, showing source board image plus extracted polygons.
- The UI copy and pipeline status distinguish this as an MVP CV extraction with confidence/warnings, not a final rules oracle.
- Verification includes unit tests, type/lint checks, official-PDF integration smoke, live localhost route checks, and best-available browser evidence.

## Files

- Create `src/warhammer_companion/domain/packet_io.py`
- Modify `src/warhammer_companion/domain/repository.py`
- Create `src/warhammer_companion/ingestion/artifacts.py`
- Create `src/warhammer_companion/ingestion/pdf.py`
- Create `src/warhammer_companion/ingestion/coordinates.py`
- Create `src/warhammer_companion/ingestion/manifest.py`
- Create `src/warhammer_companion/ingestion/footprints.py`
- Create `src/warhammer_companion/ingestion/layouts.py`
- Create `src/warhammer_companion/ingestion/packet_builder.py`
- Modify `src/warhammer_companion/ingestion/pipeline.py`
- Modify `src/warhammer_companion/cli.py`
- Modify `src/warhammer_companion/web/server.py`
- Modify `src/warhammer_companion/web/templates/map_data.html`
- Add focused tests under `tests/`
- Add generated-work log at `docs/work-log/official-ingestion.md`

## Task 1: Packet Persistence And File Repository

**Files:**
- Create: `src/warhammer_companion/domain/packet_io.py`
- Modify: `src/warhammer_companion/domain/repository.py`
- Test: `tests/test_packet_repository.py`

- [ ] Write failing tests for JSON round trip, file-backed listing, unknown packet errors, and sample fallback.
- [ ] Implement `load_packet`, `write_packet`, and `load_packet_directory` using Pydantic JSON.
- [ ] Implement `MapRepository` protocol, `StaticMapRepository`, and `FileBackedMapRepository`.
- [ ] Run `pytest tests/test_packet_repository.py -q`.
- [ ] Commit: `Add packet JSON repository`.

## Task 2: Source Manifest And Artifact Paths

**Files:**
- Create: `src/warhammer_companion/ingestion/artifacts.py`
- Create: `src/warhammer_companion/ingestion/manifest.py`
- Modify: `src/warhammer_companion/cli.py`
- Test: `tests/test_source_manifest.py`

- [ ] Write failing tests for artifact path defaults and manifest generation from local PDF files.
- [ ] Implement `IngestionPaths`, `SourceManifestEntry`, and `write_source_manifest`.
- [ ] Extend downloader to write `data/processed/source-manifest.json`.
- [ ] Run `pytest tests/test_source_manifest.py -q`.
- [ ] Commit: `Record official source manifest`.

## Task 3: PDF And Coordinate Primitives

**Files:**
- Create: `src/warhammer_companion/ingestion/pdf.py`
- Create: `src/warhammer_companion/ingestion/coordinates.py`
- Test: `tests/test_pdf_primitives.py`
- Test: `tests/test_coordinates.py`

- [ ] Write failing tests using synthetic PDFs/images for page rendering, page count extraction, board coordinate transforms, y-axis inversion, and 0.25-inch snapping.
- [ ] Implement `RenderedPage`, `render_pdf_page`, `pdf_page_count`, `page_text`, `BoardTransform`, `image_to_board_point`, `image_contour_to_board_polygon`, and `snap_polygon`.
- [ ] Run the focused tests.
- [ ] Commit: `Add PDF and coordinate primitives`.

## Task 4: Terrain Footprint Library Extraction

**Files:**
- Create: `src/warhammer_companion/ingestion/footprints.py`
- Test: `tests/test_footprints.py`

- [ ] Write failing tests using synthetic green-outline images for contour extraction, polygon simplification, bbox provenance, dimension snapping, and confidence warnings.
- [ ] Implement green-outline segmentation and contour-to-template extraction.
- [ ] Write footprint library JSON to `data/processed/footprint-library.json`.
- [ ] Generate official review image overlays under `data/processed/review/footprints/`.
- [ ] Run focused tests plus official extraction smoke on `data/raw/terrain-area-footprints.pdf`.
- [ ] Commit: `Extract official footprint library`.

## Task 5: Event Companion Layout Extraction

**Files:**
- Create: `src/warhammer_companion/ingestion/layouts.py`
- Test: `tests/test_layout_extraction.py`

- [ ] Write failing tests using a synthetic 44x60 board image with red/blue zones and grey/green/yellow terrain features.
- [ ] Implement board rectangle detection, deployment colour extraction, terrain-area segmentation, dense/light feature segmentation, page title extraction, layout ID extraction, and board transform construction.
- [ ] Generate review overlays under `data/processed/review/layouts/`.
- [ ] Run focused tests plus official layout-page smoke on Event Companion page 9.
- [ ] Commit: `Extract official layout geometry`.

## Task 6: Official Packet Builder And Validation

**Files:**
- Create: `src/warhammer_companion/ingestion/packet_builder.py`
- Modify: `src/warhammer_companion/ingestion/pipeline.py`
- Test: `tests/test_packet_builder.py`
- Test: `tests/test_official_pipeline.py`

- [ ] Write failing tests that build a `MapPacket` from extracted layout geometry and reject invalid board bounds, empty deployment zones, duplicate IDs, and invalid polygons.
- [ ] Implement `build_map_packet`, `validate_packet`, and `run_official_ingestion`.
- [ ] Persist packet JSON files under `data/processed/map-packets/`.
- [ ] Produce `data/processed/ingestion-report.json` with counts, warnings, timings, and artifact paths.
- [ ] Run focused tests plus official ingestion smoke.
- [ ] Commit: `Build official map packets`.

## Task 7: CLI And Web Integration

**Files:**
- Modify: `src/warhammer_companion/cli.py`
- Modify: `src/warhammer_companion/web/server.py`
- Modify: `src/warhammer_companion/web/templates/map_data.html`
- Test: `tests/test_web_ingestion.py`

- [ ] Write failing tests for CLI `ingest-official`, CLI `validate-packets`, file-backed repository use in web routes, and cache clearing after ingestion.
- [ ] Implement CLI commands.
- [ ] Wire the web app to `FileBackedMapRepository(data/processed/map-packets, fallback=SAMPLE_PACKETS)`.
- [ ] Make `/map-data/ingest` run ingestion synchronously for the local MVP, reload repository, and clear heatmap cache.
- [ ] Display latest ingestion report counts/warnings and packet source in Map Data Management.
- [ ] Run focused tests.
- [ ] Commit: `Wire official ingestion into web app`.

## Task 8: Browser And Live Verification

**Files:**
- Create or update: `docs/work-log/official-ingestion.md`

- [ ] Restart localhost server from the corrected project path.
- [ ] Use the Browser plugin if available; otherwise record that no dedicated Browser runtime is exposed and use live HTTP/DOM checks plus the user-opened in-app browser for manual inspection.
- [ ] Verify `/map-data` lists generated official packets and ingestion status.
- [ ] Verify `/viewer`, `/heatmap`, and `/los-checker` can load at least one official packet.
- [ ] Record performance timings for official packet heatmap and LOS checker routes.
- [ ] Run full `ruff format --check`, `ruff check`, `pytest`, and `mypy`.
- [ ] Commit: `Document official ingestion verification`.

## Exit Gate

Do not mark the goal complete until:

- All tasks are committed.
- Full verification is green.
- At least one official-derived packet is loaded by all user-facing screens.
- Official extraction artifacts and visual overlays exist.
- The work log records known CV limitations and next review needs.
- An adversarial review pass has no unresolved P0/P1 blockers.
