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

### Exit Criteria

- Source manifest with hashes/page counts exists.
- Footprint library JSON exists.
- Official-derived packet JSON exists.
- At least one official-derived packet loads in `/map-data`, `/viewer`, `/heatmap`, and `/los-checker`.
- Visual overlays exist for footprint and layout extraction.
- Full verifier set passes.
