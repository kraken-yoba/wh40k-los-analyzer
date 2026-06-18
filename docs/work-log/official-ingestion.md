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

### Codex Backend And Known Feature Catalog Slice

- Replaced the external ChatGPT subscription placeholder with a real Codex account/backend integration boundary using the `openai-codex` Python SDK.
- Settings now separates the app's Python ingestion backend from the Codex account backend. The app reads sanitized SDK/runtime/account status and exposes server-rendered POST actions for browser login, device-code login, and logout.
- The Codex backend uses the packaged `openai-codex-cli-bin` runtime supplied by `openai-codex`, not a globally installed `codex` executable. This is required for standalone downloads/releases.
- Codex state defaults to the OS user-data directory (`%LOCALAPPDATA%\WarhammerTournamentCompanion\codex-home` on Windows); packaged builds can override this with `WARHAMMER_COMPANION_CODEX_HOME`.
- Credentials remain owned by Codex local auth storage. The app does not read, render, copy, or persist `auth.json`, access tokens, API keys, or ChatGPT browser-session data.
- Added a known dense terrain feature catalog with versioning, stable type IDs, representative top-down image assets, display names, descriptions, blocker templates, typical positions, default wall sides, and classification hints.
- Initial catalog entries cover L-shaped ruined walls, U-shaped ruined walls, perimeter ruined walls, armoured containers, generic solid LOS blockers, and horizontal floor/platform review features.
- Visual categorizer requests now identify the provider as `codex_visual_classifier`, include the catalog version and known type options, and require each result to echo a deterministic feature digest.
- Visual categorizer results may now supply `type_id` and footprint position. Catalog type IDs resolve into deterministic feature profiles and default blocker templates; the LOS engine still consumes deterministic geometry, not free-form model output.
- Hardened result application: stale geometry digests are ignored, conflicting duplicate rows are ignored, low-confidence rows remain ignored, and all such refusals are reported in ingestion output.
- No temporary TypeScript or JavaScript component was introduced. This slice stayed Python-only because server-rendered controls are sufficient for Codex account actions and artifact-driven categorizer workflow. Future temporary TypeScript exceptions must be isolated, documented with a specific justification, and removable without changing the Python domain model.
- Added `docs/packaging.md` with the Codex runtime packaging contract and the temporary TypeScript exception policy.
- Codex state handling now supports standalone OS user-data defaults, explicit `WARHAMMER_COMPANION_CODEX_HOME` packager overrides, and portable state directories for Codex desktop/sandboxed development runs.
- Verification after the slice:
  - `.\.venv\Scripts\python.exe -m ruff format --check src tests`
  - `.\.venv\Scripts\python.exe -m ruff check src tests`
  - `.\.venv\Scripts\mypy.exe src`
  - `.\.venv\Scripts\python.exe -m pytest -q` (`120 passed`)
  - `.\.venv\Scripts\python.exe -m warhammer_companion.cli ingest-official --page 9`
  - `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets`
- Browser verification used `http://127.0.0.1:8031`: Settings showed `Codex SDK ready`, packaged runtime `openai-codex-cli-bin` `0.137.0a4`, state under an app-owned Codex home, and server-rendered `Start Codex login` / `Device code` controls; Map Data, LOS Heatmap, and LOS Checker rendered the official page-9 packet with no captured console warnings/errors.

### Local Catalog Classifier Application Slice

- Added a deterministic local catalog classifier that consumes the same `visual-categorizer-request.json` contract as the future Codex visual model path and writes `visual-categorizer-results.json` with provider `local_catalog_classifier`.
- The classifier is a bootstrap pass, not a substitute for future visual-model review. It uses footprint geometry, fill ratio, aspect ratio, and current heuristic profile to separate likely horizontal floor/platform patches from wall/container LOS blockers.
- Web-triggered ingestion now runs the local classifier by default; the CLI defaults to `--classify-features` and keeps `--skip-classifier` for preserving hand-authored or externally reviewed categorizer results.
- Map Data now labels the operation as `Ingest + Classify` and reports when a categorizer request exists but no results were applied, so stale fallback geometry is visible to the user.
- Re-ingested official Event Companion page 9 with classifier results. The ingestion report shows 31 classifier results present and 31 applied from `data/processed/review/visual-categorizer-results.json`.
- The page-9 classifier split the 31 dense candidates into 11 `floor-or-platform` review features, 6 `ruined-wall-l`, 5 `ruined-wall-u`, 5 `armoured-container`, and 4 `solid-los-blocker` results.
- Verification after the slice:
  - `.\.venv\Scripts\python.exe -m ruff format --check src tests`
  - `.\.venv\Scripts\python.exe -m ruff check src tests`
  - `.\.venv\Scripts\mypy.exe src`
  - `.\.venv\Scripts\python.exe -m pytest -q` (`125 passed`)
  - `.\.venv\Scripts\python.exe -m warhammer_companion.cli ingest-official --page 9 --classify-features`
  - `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets`
- Browser follow-up found that the already-running `8031` server could keep serving a stale in-memory packet after CLI re-ingestion. File-backed repositories now auto-refresh when packet JSON files change, and the viewer reports dense blockers, light/review features, and floor/platform review counts separately.
- Fresh browser verification on `http://127.0.0.1:8037` showed official page 9 with 36 dense blockers, 26 light/review features, 11 floor/platform review features, and LOS checker coverage rendered from the same refreshed packet.

### Official Feature Label Slice

- Event Companion dense-feature labels `AB`, `CD`, `EF`, and `GH` are now extracted from PDF text as deterministic source data after terrain areas are found. Label-backed dense features replace raster dense candidates on the same footprint, while light/review features are preserved.
- Official label templates currently map `AB`, `EF`, and `GH` to standard L-shaped ruined wall blockers and `CD` to a standard U-shaped ruined wall blocker. The label selects the type, while the nearest raster dense component on the same terrain footprint anchors placement when available. Label position remains the fallback anchor.
- Anchor position inside the terrain footprint determines wall-side orientation, so mirrored footprints such as terrain areas 1 and 6 produce mirrored standard blockers instead of irregular raster fragments.
- Visual categorizer requests now carry `official_feature_code` and current wall sides. The local catalog classifier treats official codes as authoritative and echoes the extracted wall sides instead of reinterpreting those features from noisy raster geometry. Feature digests include official code, current profile, and wall sides so stale categorizer artifacts are invalidated when label-derived interpretation changes.
- Packet projection now unions L-shaped and U-shaped wall sides into one continuous blocker polygon per standard feature. Full perimeter walls remain separate side strips because the current packet model does not encode polygon holes.
- Re-ingested official Event Companion page 9 with classifier results. The layout library contains eight official label-backed features: terrain areas 1 and 6 each have two `EF`/`GH` L-shaped blockers, terrain areas 3 and 11 have one `AB` L-shaped blocker each, and terrain areas 5 and 13 have one `CD` U-shaped blocker each.
- The regenerated page-9 packet validates and contains 14 dense blockers total: six `ruined_wall_l`, two `ruined_wall_u`, five `container_or_solid`, and one `solid_los_blocker`.
- Verification after the slice:
  - `.\.venv\Scripts\python.exe -m ruff format --check src tests`
  - `.\.venv\Scripts\python.exe -m ruff check src tests`
  - `.\.venv\Scripts\mypy.exe src`
  - `.\.venv\Scripts\python.exe -m pytest -q` (`129 passed`)
  - `.\.venv\Scripts\python.exe -m warhammer_companion.cli ingest-official --page 9 --classify-features`
  - `.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets`
- Browser verification used `http://127.0.0.1:8038`: Map Viewer showed 14 dense blockers, LOS Checker rendered the same 14 blockers with one raster coverage image, one model base, 5 visible rays, and 29 blocked rays, and LOS Heatmap rendered the same blocker mix with one heatmap raster image. No browser warning/error logs were captured during those checks.
