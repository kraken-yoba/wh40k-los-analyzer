# Next Design Iteration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add public GitHub publishing, deployment-edge heatmaps with whole-inch offset controls, richer light/dense feature classification, and LOS semantics where dense features still block when a base touches a footprint.

**Architecture:** Keep the MVP Python-first: LOS geometry stays in `los/geometry.py`, extraction in `ingestion/layouts.py`, packet normalization in `ingestion/packet_builder.py`, and Jinja views in `web/templates`. Heatmaps will sample a derived line geometry rather than full deployment-zone interiors; dense feature metadata will remain heuristic and reviewable.

**Tech Stack:** Python 3.12, FastAPI/Jinja, Shapely, OpenCV, PyMuPDF, pytest, ruff, mypy.

---

### Task 1: GitHub Remote And Baseline Push

**Files:**
- Modify: local git config only.
- Verify: GitHub remote `origin`.

- [x] **Step 1: Set public origin**

```bash
git remote add origin https://github.com/kraken-yoba/wh40k-los-analyzer.git
```

- [x] **Step 2: Fetch remote refs**

```bash
git fetch origin
```

- [x] **Step 3: Push current progress branch**

```bash
git push -u origin codex/official-ingestion
```

Expected: branch `codex/official-ingestion` exists on the public repository.

### Task 2: Deployment Edge Heatmap Sampling

**Files:**
- Modify: `src/warhammer_companion/los/geometry.py`
- Modify: `src/warhammer_companion/web/server.py`
- Modify: `src/warhammer_companion/web/templates/heatmap.html`
- Modify: `src/warhammer_companion/web/static/style.css`
- Test: `tests/test_los_geometry.py`
- Test: `tests/test_web_server.py`

- [x] **Step 1: Write failing geometry tests**

Add tests that call a new function:

```python
polygons = heatmap_visibility_polygons_from_deployment_edge(
    packet,
    "attacker",
    offset_inches=0,
)
assert polygons
assert all(item.origin[1] >= packet.deployment_zone("attacker").polygon().bounds[3] - 0.1 for item in polygons)
```

Add a second test with `offset_inches=6` and assert attacker origins move toward the board center by about 6 inches.

- [x] **Step 2: Implement edge sampling**

Add `heatmap_visibility_polygons_from_deployment_edge(packet, deployment_zone_id, offset_inches=0, sample_step=2.0)`.
Derive the edge as the deployment-zone boundary segment closest to the board centerline:
- bottom deployment: top edge, offset increases y
- top deployment: bottom edge, offset decreases y
- left/right zones: use the side facing board center

Clamp generated origins inside the board and skip points that fall inside blockers.

- [x] **Step 3: Wire heatmap mode and offset into web route**

Extend `_cached_heatmap_svg(packet_id, zone_id, source, offset_inches)` and `/heatmap` query params:
- `source=edge` by default
- `source=interior` keeps the old interior sampling for comparison
- `offset_inches` integer 0 through 12, default 0

- [x] **Step 4: Add heatmap controls**

In `heatmap.html`, add a segmented/native select control for source and a range slider with whole-inch snap labels for offset.

- [x] **Step 5: Verify**

```bash
.\.venv\Scripts\python.exe -m pytest tests\test_los_geometry.py tests\test_web_server.py -q
```

Expected: new tests pass and old heatmap tests still pass.

### Task 3: Dense Feature Extraction Metadata

**Files:**
- Modify: `src/warhammer_companion/domain/models.py`
- Modify: `src/warhammer_companion/ingestion/layouts.py`
- Modify: `src/warhammer_companion/ingestion/packet_builder.py`
- Modify: `src/warhammer_companion/rendering/svg.py`
- Modify: `src/warhammer_companion/web/static/style.css`
- Test: `tests/test_layout_extraction.py`
- Test: `tests/test_packet_builder.py`
- Test: `tests/test_rendering_svg.py`

- [x] **Step 1: Write failing extraction/classification tests**

Add synthetic layout fixtures with dense green rectangles and light yellow rectangles. Assert:
- dense features carry `feature_type == "dense"`
- light features carry `feature_type == "light"`
- dense packet features carry a `profile` such as `wall_section`, `container`, or `solid_mass`
- rendered SVG uses distinct CSS classes for dense and light review overlays.

- [x] **Step 2: Add feature profile field**

Add optional `feature_profile: str | None` to `LayoutElement` and `DenseTerrainFeature`.

- [x] **Step 3: Classify dense profiles heuristically**

Use simple geometry heuristics:
- long thin dense polygon: `wall_section`
- compact rectangular dense polygon with area above threshold: `container_or_solid`
- otherwise: `dense_obstacle`

Keep confidence/warnings explicit because this is heuristic machine vision.

- [x] **Step 4: Preserve light features as review metadata**

Do not make light features LOS blockers. Ensure layout library and review overlays visibly differentiate light vs dense features.

- [x] **Step 5: Verify**

```bash
.\.venv\Scripts\python.exe -m pytest tests\test_layout_extraction.py tests\test_packet_builder.py tests\test_rendering_svg.py -q
```

Expected: dense/light distinction and dense profile metadata are covered.

### Task 4: Dense Blockers Remain Active When Touching Footprints

**Files:**
- Modify: `src/warhammer_companion/los/geometry.py`
- Test: `tests/test_los_geometry.py`

- [x] **Step 1: Write failing LOS rule test**

Create or modify a packet where base touches a terrain area with a dense feature behind the contact point. Assert:

```python
touching_polygon = visibility_polygon_from_base(packet, center=touching, base_diameter=1.57)
assert not touching_polygon.covers(Point(target_behind_dense_feature))
```

- [x] **Step 2: Update blocker logic**

In `_blockers_for_base`, remove touched terrain area footprints from blockers but keep dense features even when their `terrain_area_id` is touched.

- [x] **Step 3: Verify**

```bash
.\.venv\Scripts\python.exe -m pytest tests\test_los_geometry.py -q
```

Expected: touched footprint is transparent, dense feature still blocks.

### Task 5: Official Ingestion And Browser QA

**Files:**
- Modify: `docs/work-log/official-ingestion.md`

- [x] **Step 1: Run checks**

```bash
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q
```

- [x] **Step 2: Run official smoke**

```bash
.\.venv\Scripts\python.exe -m warhammer_companion.cli ingest-official --page 9
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets
```

- [ ] **Step 3: Browser test**

Use the in-app Browser against the live FastAPI server:
- `/heatmap?packet_id=official-event-companion-page-9&zone_id=attacker&source=edge&offset_inches=6`
- `/los-checker?packet_id=official-event-companion-page-9`

Verify page identity, nonblank map, no console warnings/errors, heatmap raster present, and LOS checker base interaction still rerenders coverage.

- [ ] **Step 4: Commit and push**

Commit atomic checkpoints and push:

```bash
git push
```
