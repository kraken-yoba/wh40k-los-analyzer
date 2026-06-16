# Browser Evidence

Browser-plugin workflow evidence for fixture-backed GUI slices.

Positive workflow run: 2026-06-16 on `http://127.0.0.1:8000`.
Reviewer-fix regression run: 2026-06-16 on `http://127.0.0.1:8765`.
Official extraction readiness run: 2026-06-16 on `http://127.0.0.1:18765`.

| Workflow | Fixture/Input | Endpoint/State | Playwright Test | Browser Evidence | Status |
| --- | --- | --- | --- | --- | --- |
| Dashboard loads offline | Synthetic fixture set | `/` | `backend/tests/test_gui.py` | DOM rendered heading, controls, sources, validation, LOS, and analysis panels | Pass |
| Source manifest status | Synthetic manifest | `/api/sources` | `backend/tests/test_data_spine_api.py` | Browser showed terrain layouts, Event Companion, and core rules as `hash_match` | Pass |
| Extraction inspection | Event Companion page 9 from local hash-matched cache | `/api/layouts/event-companion-page-9` | `backend/tests/domain/test_event_companion_extraction.py`, `backend/tests/test_data_spine_api.py` | Browser loaded `Layout A`, rendered extraction/warning records, and listed 45 extracted Event Companion layouts | Pass |
| PDF underlay and overlays | Synthetic rendered page | Pending | Pending | Pending | Pending |
| Feature provenance | Synthetic terrain feature | Pending | Pending | Pending | Pending |
| Accepted warning state | Synthetic warning fixture | Pending | Pending | Pending | Pending |
| Layout and deployment selection | Synthetic layout set | `/api/layouts`, `/api/layouts/synthetic-alpha` | `backend/tests/test_data_spine_api.py` | Browser selected `Synthetic Alpha` and rendered validation record `synthetic_fixture` | Pass |
| Point LOS click | Synthetic blocker layout | `/api/layouts/synthetic-alpha/los` | `backend/tests/test_los_api.py` | Canvas click workflow selected two board points and populated LOS JSON | Pass |
| Base-aware LOS | Synthetic blocker layout | `/api/layouts/synthetic-alpha/los` | `backend/tests/test_los_api.py` | Click workflow returned `method: disk-sample-v1`, `sample_count: 289`, `visible: true` | Pass |
| Invalid base-center click | Synthetic blocker layout | `/api/layouts/synthetic-alpha/los` | `backend/tests/test_los_api.py`, `backend/tests/test_gui.py` | Illegal source click rendered `Error: source base center is not legal` in the LOS panel | Pass |
| Unreviewed official-layout LOS block | Event Companion page 9 from local hash-matched cache | `/api/layouts/event-companion-page-9/los` | `backend/tests/test_data_spine_api.py` | Map click rendered blocked readiness error with `placement_proxy_not_los_ready`, `terrain_measurement_crosscheck_pending`, and `terrain_label_review_required` | Pass |
| Firing-lane heatmap | Synthetic source region | `/api/layouts/synthetic-alpha/heatmap` | `backend/tests/test_analysis_api.py` | Heatmap button returned 15 heatmap cells and drew the heatmap overlay state | Pass |
| Deployment exposure | Synthetic deployment region | `/api/layouts/synthetic-alpha/exposure` | `backend/tests/test_analysis_api.py` | Exposure button returned reachable cells with exposed flags | Pass |
| Terrain contribution metrics | Synthetic terrain feature | `/api/layouts/synthetic-alpha/terrain/ruin-a/coverage` | `backend/tests/test_analysis_api.py` | Terrain button returned `coverage_delta: 1` and a changed target cell | Pass |
| Export bundle | Synthetic analysis state | GUI export state | `backend/tests/test_gui.py` | Export button returned layout id, hash, selected points, and heatmap state | Pass |

Responsive check: a temporary 390x844 viewport had `scrollWidth` 375, and all controls plus the canvas stayed inside the viewport width.

Browser console: no error-level logs after LOS clicks, analysis button workflows, or invalid base-center error handling.
