# Official Ingestion Work Log

## 2026-06-17

### Setup

- Active repo path corrected to `C:\Users\Conferences and AI\Documents\Warhammer tournament companion`.
- Official PDFs downloaded to ignored `data/raw/`:
  - `terrain-area-footprints.pdf`
  - `event-companion.pdf`
  - `core-rules.pdf`
- Rendered inspection PNGs under ignored `data/cache/pdf-pages/`.

### Source Observations

- `terrain-area-footprints.pdf` has 3 pages. Text is minimal (`x2`, `x4`, `x4`), so extraction must be visual/vector-based.
- Terrain footprint pages contain green cut-line outlines around terrain photos. These are the primary footprint extraction signal.
- `event-companion.pdf` has 93 pages. Layout pages begin at printed page 9 and continue through printed page 53 based on extracted layout text.
- Event layout pages show a board rectangle, grid, coloured deployment zones, grey terrain footprints, green/yellow terrain features, layout labels, and measurement annotations.
- The Event Companion text states missions use rectangular battlefields 44 inches by 60 inches.

### Tooling Notes

- Dedicated Browser plugin runtime is not exposed in this session (`tool_search` found no browser tool). Live route checks and in-app browser user evidence are available; browser automation will be revisited if a Browser tool becomes available.
- Subagent consultants are being used:
  - Architecture consultant returned a module/task breakdown.
  - Adversarial reviewer returned acceptance tests and blocking risks.
  - PDF/CV extraction consultant is still pending at the time this entry was written.

### Design Choices

- Keep `MapPacket` as the runtime contract for viewer, heatmap, and LOS checker.
- Persist generated official packets as JSON under `data/processed/map-packets/`.
- Keep sample packets as fallback only; generated official packets should appear first once available.
- Store extraction confidence/provenance in ingestion reports and packet source strings for the MVP. A richer domain provenance model may follow once extractor quality stabilizes.
- Generate visual review overlays for official extraction rather than hiding CV uncertainty.

### Checkpoints

- Task 1 packet JSON repository committed as `2a44674`.
- Task 2 source manifest committed as `20fa2ad`.
- Task 3 PDF/coordinate primitives: controller verification passed; two rounds of subagent review attempts failed with backend `404 Not Found` before producing review findings, so Task 3 received inline spec/code review before commit.
- Task 4 footprint extraction uses vector-first extraction for official PDF pages. The terrain footprint PDF exposes five large green vector paths across pages 1-3; tiny single-item green path fragments are ignored. Raster green-contour extraction remains as a fallback for pages without vector templates.
- Task 4 code review found and fixed two fallback P1s: raster fallback now derives pixels-per-inch from render DPI unless explicitly calibrated, and vector-first extraction now falls back page-by-page instead of dropping raster-only pages when any vector page succeeds.
- Task 4 official smoke extracts 5 templates from `terrain-area-footprints.pdf` and writes `data/processed/footprint-library.json` plus review overlays for pages 1-3.
- Task 5 layout extraction uses vector-first board/deployment/grey-terrain extraction from `event-companion.pdf`. Dense/light terrain features are raster HSV candidates clipped to each grey footprint because green/yellow vector fills on layout pages are mostly labels/icons rather than reliable feature geometry.
- Task 5 official page-9 smoke detects board `(127.99, 277.77, 468.15, 740.18)`, 2 deployment zones, 16 terrain areas, and raster dense/light feature candidates.
- Task 5 official aggregate smoke over pages 9-53 detects 45 layouts; every layout has 2 deployment zones, 16 terrain areas, and at least one raster feature candidate.
- Task 6 packet builder converts extracted layouts into `MapPacket` JSON, using grey terrain footprints as LOS-blocking terrain areas and raster dense candidates as dense blockers. Light feature candidates stay in layout extraction artifacts/reports for review rather than becoming LOS blockers in the MVP packet.
- Task 6 official page-9 smoke wrote one valid packet under `data/processed/map-packets/` and `data/processed/ingestion-report.json`.
- Task 7 wires processed packet JSON into the Python web app with sample fallback, synchronous official ingestion from Map Data Management, generated-packet deletion, latest ingestion report display, and CLI `ingest-official` / `validate-packets` commands.
- Task 8 full official ingest generated 45 packets from Event Companion pages 9-53 in 124.51 seconds. `validate-packets` reports all 45 packets valid.
- Task 8 official page-9 LOS performance after packet simplification and numeric ray/segment intersections: 176 heatmap visibility polygons in 12.792 seconds; single-base LOS coverage in 0.071 seconds.
- Task 8 in-app browser verification used `http://127.0.0.1:8001`: Map Data showed the 45-packet report, official page-9 heatmap rendered a raster overlay, and LOS checker click-to-place moved the base to `29.92,25.20` with a fresh binary coverage raster and no console errors.

### Next Design Iteration

- Public Git remote configured as `https://github.com/kraken-yoba/wh40k-los-analyzer.git`; branch `codex/official-ingestion` pushed to the public repository.
- Heatmap generation now defaults to sampling the deployment-zone front edge, with a whole-inch 0-12 inch offset control for adversarial movement simulation. The previous full-zone interior sampling remains available as a comparison mode.
- LOS checker blocker semantics now remove only touched terrain footprint blockers. Dense features remain LOS-blocking even when the model base touches their parent terrain footprint.
- The web MVP now uses no custom frontend JavaScript. LOS base placement remains server-rendered through numeric form controls; true drag-to-place behavior is deferred unless a later standalone/Python GUI surface provides it without adding a JS app layer.
- Terrain feature extraction now stores `feature_profile` metadata on raster features. Dense features are heuristically classified as `ruined_wall_section`, `container_or_solid`, `solid_los_blocker`, or `unknown_dense`; light features are kept as non-blocking `light_area` review/display metadata.
- Full verification passed after implementation:
  - `.\.venv\Scripts\python.exe -m ruff format --check src tests`
  - `.\.venv\Scripts\python.exe -m ruff check src tests`
  - `.\.venv\Scripts\python.exe -m mypy src`
  - `.\.venv\Scripts\python.exe -m pytest -q`
- Full official ingestion rerun generated 45 packet(s) from Event Companion pages 9-53 in 114.23 seconds.
- `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets` reported all 45 generated official packets valid.
- Official page-9 regenerated JSON includes dense feature profiles and non-blocking `light_features`; generated data remains ignored under `data/processed/`.

### Exit Criteria

- Source manifest with hashes/page counts exists.
- Footprint library JSON exists.
- Official-derived packet JSON exists.
- At least one official-derived packet loads in `/map-data`, `/viewer`, `/heatmap`, and `/los-checker`.
- Visual overlays exist for footprint and layout extraction.
- Full verifier set passes.

## 2026-06-18

### Terrain Feature Categorizer Slice

- Reviewed core-rules terrain categories against the Event Companion pack behavior: feature categories are exposed, light, and dense; dense examples include buildings, ruins, armoured containers, and woods. Event layouts mark dense features green and light features yellow.
- Added a visual categorizer artifact boundary for dense terrain features. Official ingestion now writes `data/processed/review/visual-categorizer-request.json` with dense feature IDs, source page/bbox, current heuristic profile, footprint geometry, and allowed profile options.
- Kept ChatGPT subscription login as an external browser/account state. The app does not store ChatGPT credentials and does not treat a ChatGPT subscription as an API key. Instead, ChatGPT visual review can produce `data/processed/review/visual-categorizer-results.json`, which ingestion applies deterministically.
- Added dense feature profiles for `ruined_wall_l`, `ruined_wall_u`, `ruined_wall_perimeter`, and `floor_or_platform`.
- Packet projection now treats `floor_or_platform` as non-blocking review geometry and projects categorized ruin-wall profiles as narrow wall strips, so horizontal floors/platforms are no longer LOS blockers once categorized.
- Containers, solid blockers, unknown dense candidates, and uncategorized dense candidates remain LOS blockers by default. This keeps the conservative fallback until visual categorizer results are supplied.
- Adversarial review caught two categorizer hardening issues after the first pass: stale visual categorizer result IDs now report unmatched counts instead of "applied", and `wall_sides` is honored only for wall-side-capable ruin profiles with valid side counts.
- Verification after the slice:
  - `.\.venv\Scripts\python.exe -m ruff format --check src tests`
  - `.\.venv\Scripts\python.exe -m ruff check src tests`
  - `.\.venv\Scripts\python.exe -m mypy src`
  - `.\.venv\Scripts\python.exe -m pytest -q` (`98 passed`)
  - `.\.venv\Scripts\python.exe -m warhammer_companion.cli ingest-official --page 9`
  - `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets`
- In-app browser verification on `http://127.0.0.1:8008` passed for Settings, Map Data, LOS Heatmap, and LOS Checker. Settings showed the external ChatGPT login link; Map Data showed the visual categorizer request but no results row when no results file existed; official page-9 heatmap and LOS checker rendered nonblank maps with no captured console warnings/errors.
