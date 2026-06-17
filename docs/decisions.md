# Decision Log

## 2026-06-16: Python-Only Local Web App

Decision: Use a Python-only local web application for the first release. FastAPI serves APIs, templates, static CSS, and vanilla JavaScript. No Node, npm, React, Vite, or TypeScript build chain is required.

Reasoning: The hardest parts of the product are deterministic PDF extraction, computer vision, geometry, and validation, all of which are Python-centered. Removing Node reduces tooling burden, CI complexity, lockfile maintenance, and security surface while preserving the ability to build a capable local GUI with HTML, CSS, JavaScript, SVG, Canvas, and Python Playwright.

Consequences:

- Python/Pydantic schemas are the single source of truth.
- GUI tests use Python Playwright.
- Browser-side code should stay small and focused on interaction/rendering.
- If browser-side complexity grows later, a separate build tool can be reconsidered with a concrete reason.

## 2026-06-16: Public Repository Source-PDF Policy

Decision: Do not commit official Warhammer PDF binaries or rendered official PDF page images to the public repository.

Reasoning: The official PDFs and rules text are third-party material. The public repository can safely commit source URLs, hashes, schema contracts, synthetic fixtures, and copyright-safe golden outputs. Full official-PDF regression remains a local or manually cached gate.

Consequences:

- CI must be public-safe by default.
- The full release gate must support a local pinned cache.
- Extraction tests need synthetic fixtures plus optional official-PDF regression tests.

## 2026-06-16: Synthetic Data Spine Before Official PDF Extraction

Decision: Implement canonical schemas, deterministic serialization, synthetic fixtures, validation records, and geometry regression tests before extracting the official PDFs.

Reasoning: The official PDFs are the hardest and least controllable input. A synthetic data spine gives the extraction and LOS reviewers fixed ground truth before computer vision heuristics enter the system, and it lets GUI workflows be tested without depending on third-party files.

Consequences:

- The first behavior-bearing implementation slice is schema/manifest/canonical serialization.
- Synthetic fixtures are required before official-cache regression tests.
- Official-PDF extraction cannot be treated as accepted until it round-trips into the same canonical models and validator.

## 2026-06-16: Base-Aware LOS Contract

Decision: Treat first-release LOS as base-aware 2D line of sight in board-inch coordinates. Base-aware visibility must use a documented deterministic disk-to-disk approximation or exact analytic method, and tests must cover tangent, endpoint, overlap, board clipping, and sealed-gap cases.

Reasoning: This keeps the simulator aligned with the current product scope while avoiding an implicit "center point only" model. It also separates the geometry contract from future 3D terrain-height interpretation.

Consequences:

- Geometry tolerances and display resolution tolerances must be separate configuration values.
- Heatmaps are point-sampled over valid base-center positions unless the UI explicitly labels a different model.
- Future builds can move toward full 3D-aware LOS after the 2D rules, provenance, and reviewer gates are stable.

## 2026-06-16: Fixture-First UX Evidence

Decision: Build GUI workflows first against synthetic canonical fixtures and maintain a browser evidence matrix for every supported workflow.

Reasoning: Official extraction may produce warning and review states. The UX needs to make those states visible, testable, and exportable before the app is connected to brittle real-PDF inputs.

Consequences:

- Each GUI workflow must map to a fixture, endpoint test, Browser-plugin check, and evidence note.
- Layout QA and warning review are first-class views, not hidden debug surfaces.
- Strategy views must show degraded status when accepted warnings or uncertain extraction records affect the result.

## 2026-06-16: Canonical Inputs Must Be Strict

Decision: Canonical layout and source-manifest models reject non-finite numbers, invalid/simple-polygon failures, duplicate IDs, blockers outside referenced footprints, untrusted source URLs, unsafe cache paths, malformed hashes, mutable post-validation state, and unsupported schema versions.

Reasoning: LOS algorithms should consume trusted canonical geometry instead of defensively guessing what malformed inputs mean. Blocking bad canonical inputs early also makes reviewer findings reproducible through focused tests.

Consequences:

- Canonical model collections are immutable tuples after validation.
- Source PDF cache paths must stay relative under `data/pdfs`.
- Official source URLs are restricted to HTTPS assets from `assets.warhammer-community.com`.
- Schema files must be regenerated whenever Pydantic model contracts change.

## 2026-06-16: Event Companion Vector Extraction First

Decision: Use the Event Companion layout pages as the first official automatic extraction source for board geometry, deployment zones, layout page inventory, and terrain placement candidates.

Reasoning: The Event Companion map pages expose board outlines, deployment areas, grid lines, terrain placement shapes, markers, and measurement text as extractable PDF vectors/text. The terrain footprint PDF mostly contains image cutouts plus green outline paths and no useful text. Event Companion vectors therefore provide the most deterministic path into board-inch placement candidates before adding raster/CV matching against the detailed terrain footprint sheet.

Consequences:

- First official extraction should parse Event Companion pages into canonical layouts and validation records, but mark them as warning-state candidates.
- Terrain placements can be extracted from gray vector shapes on the map pages, with coordinates calibrated from the board rectangle.
- Deployment-zone depths can be cross-checked against printed inch annotations; full terrain offset measurement cross-checks remain pending.
- Extracted Event Companion placements must not emit LOS blockers or be analyzed as real opaque walls until official footprint outlines and wall semantics are validated.
- Browser and reviewer evidence must distinguish vector-extracted official map placement candidates from later detailed wall-shape enrichment.

## 2026-06-16: Terrain Footprint PDF Outlines Are Evidence, Not Blockers

Decision: Extract the large green vector outlines from the official Terrain Area Footprints PDF as deterministic footprint-outline evidence, but do not convert them into LOS blockers by default.

Reasoning: The outline PDF provides stable vector geometry for footprint shapes, but it does not by itself establish wall opacity, internal wall segments, or how each outline should be transformed onto every Event Companion terrain placement. Treating outlines as evidence keeps the extraction useful while preserving the review gate for gameplay semantics.

Consequences:

- Cached official-footprint regression tests must pin the PDF SHA-256 and expected outline counts/bounds.
- Event Companion layouts remain blocked for analysis until footprint outlines are mapped, reviewed, and wall semantics are represented explicitly.
- Future extraction work should align these outlines to Event Companion placement rectangles before adding wall/blocker geometry.

## 2026-06-16: Footprint Template Matching Is Provisional Evidence

Decision: Normalize Terrain Area Footprints outlines and contained green fragments into template evidence, then match Event Companion terrain placements to templates by deterministic aspect-ratio scoring only as provisional candidates.

Reasoning: Template matching improves the extraction evidence chain without pretending that footprint outlines define walls or opaque LOS blockers. Aspect-ratio matching is deterministic and testable, but official labels are incomplete or ambiguous and the PDF does not encode wall opacity semantics.

Consequences:

- Footprint matches can add validation records, but they cannot unblock official-layout LOS analysis by themselves.
- Ambiguous template scores, weak aspect matches, fallback labels, and slash labels must remain `needs_review`.
- `extract_event_companion_layout(..., footprint_templates=...)` keeps official layouts warning-state. Later work may emit blocker candidates only when they remain review-gated.

## 2026-06-16: Footprint Fragment Walls Are Provisional Blocker Candidates

Decision: Convert matched Terrain Area Footprints fragment paths into deterministic board-inch wall segments only for Event Companion terrain placements classified as Dense, but keep those segments provisional and analysis-blocked until review.

Reasoning: The official footprint PDF exposes stable green internal fragment paths that are useful wall/blocker evidence once a footprint template is matched to an Event Companion terrain placement. The Event Companion key distinguishes Dense and Light terrain, and the Core Rules' Dense/Solid semantics are the direct 2D LOS wall relevance for this first pass. The match itself can still be ambiguous or label-weak, and the PDF does not explicitly encode every gameplay opacity detail, so generated wall segments must improve inspection without unblocking official-layout LOS.

Consequences:

- Template matches record whether reciprocal aspect matching requires a 90 degree rotation before fragment points are transformed into board inches.
- Fragment-derived wall segments are generated only for Dense terrain features, validated inside the referenced terrain footprint, and surfaced in layout payloads and the GUI as provisional blockers.
- Cubic Bezier fragment commands are tessellated into deterministic path samples rather than treating control points as wall vertices.
- Official extracted layouts keep `terrain_footprint_blocker_review_required` warnings, so LOS/heatmap/exposure endpoints still fail closed until the review workflow accepts the geometry.

## 2026-06-16: Rules Semantics Are Source-Anchored Evidence, Not A Rules Engine

Decision: Use the hash-matched Core Rules PDF to verify short section anchors for LOS-relevant terrain semantics, then expose only paraphrased engine implications in the API and GUI.

Reasoning: The app needs to explain why Dense/Solid terrain receives provisional wall candidates while Light and Exposed terrain do not. The public repo must not redistribute official rules text, and the first release is not attempting a full Warhammer rules engine.

Consequences:

- `/api/rules/terrain-semantics` returns unavailable evidence for missing or hash-mismatched rules PDFs.
- Hash-matched rules evidence verifies section anchors for visibility, terrain categories, movement, terrain visibility, Obscuring, and Solid without embedding long copied rule text.
- The GUI Rules panel distinguishes Dense/Solid wall relevance from Light/Exposed terrain context and records that full 3D-aware LOS remains future scope.
- Rules evidence supports review and user understanding, but it does not itself unblock provisional official geometry.

## 2026-06-16: Visual Sanity Is Deterministic CV First

Decision: Add an advisory Event Companion visual sanity report that renders the PDF page, segments raster evidence for board, deployment zones, and terrain features, and compares those shapes against canonical extraction geometry in board-inch residuals. Live vision-model review is a later advisory consumer of this deterministic report, not a source of canonical geometry.

Reasoning: The user explicitly required robust deterministic computer vision and only advisory vision-model verification. A deterministic raster alignment report gives repeatable evidence that the extracted map shape resembles the source PDF image, while avoiding nondeterministic model output in the extraction pipeline.

Consequences:

- The visual sanity endpoint can pass or warn independently of layout readiness; it does not accept review warnings or unblock LOS analysis.
- Vision status is exposed as `not_run` until a credential-gated model verifier is added.
- Browser evidence and tests must verify the Sanity panel separately from canonical extraction and LOS analysis.

## 2026-06-16: Accepted Warnings Keep Analysis Degraded

Decision: Let the local GUI accept validation warnings in memory so reviewers can intentionally run analysis on warning-state extracted layouts, while preserving degraded status in validation records and analysis responses.

Reasoning: Official extraction still contains provisional footprint and wall semantics. A fail-closed default protects users from accidental overtrust, but the product also needs an auditable path to inspect strategy views once those warnings are consciously accepted. Keeping acceptance local and visible makes the workflow reversible by refresh/restart and avoids writing review decisions into the official PDF cache.

Consequences:

- Clean layouts keep the existing API response shape; degraded analysis responses include `validation_state`.
- Acceptance requests must include the current visible layout hash and are rejected if the layout snapshot has changed.
- Accepted warnings unblock LOS, heatmap, exposure, and terrain metrics only after every warning on the layout is accepted.
- Layouts with accepted warnings keep `validation_status: warning` and show `accepted_with_warnings` in the GUI.

## 2026-06-16: Bounded Interactive Analysis Work

Decision: Cap sampled analysis regions and pairwise LOS workloads before running heatmap, exposure, or terrain-coverage analysis.

Reasoning: API callers can control finite positive grid steps. Without explicit work limits, very small steps can allocate large sample grids and trigger excessive CPU work even though the numeric inputs pass finite-value validation. The local app should fail closed with a client error rather than freezing the analysis process.

Consequences:

- `analysis.py` enforces maximum region samples and maximum LOS pair evaluations.
- FastAPI analysis endpoints convert `AnalysisRequestTooLarge` into HTTP 422 responses.
- Oversized work has domain and API regression coverage.

## 2026-06-16: Minimal Dependency Trust Base

Decision: Remove dependencies that are not directly used or justified by the runtime/test suite.

Reasoning: The security scan found `httpx2` in `pyproject.toml` and `uv.lock` even though no code imports it. Keeping unused public packages expands the install trust base and creates avoidable supply-chain exposure.

Consequences:

- `httpx2`, `httpcore2`, and `truststore` are absent from the lockfile.
- Future dependency additions should be tied to concrete imports, tests, or documented tool requirements.

## 2026-06-17: Source Acquisition Is Hash-Gated And Local

Decision: Provide an official-source downloader that reads only the committed source manifest, writes only under the gitignored `data/pdfs` cache, and publishes a file only after its SHA-256 matches the manifest.

Reasoning: The product should be able to acquire the official PDFs automatically, but the public repository must not redistribute third-party PDF binaries or trust arbitrary network responses. Hash-gated local acquisition keeps the workflow reproducible while preserving the copyright and supply-chain boundary.

Consequences:

- The downloader skips files that already match the manifest hash.
- Missing or hash-mismatched cache files are refreshed from the pinned official URL.
- Redirect targets are revalidated against the approved official asset host before any response body is read.
- Response bodies are streamed to temporary `.part` files with an explicit size cap rather than read fully into memory.
- A downloaded payload with the wrong hash is not moved into place, temporary `.part` files are removed, and any existing local cache file is preserved for inspection.
- Public CI remains network-free; users run `scripts\download-sources.cmd` locally to populate the optional official-PDF cache.

## 2026-06-17: Snapped Footprints And Automatic Geometry Review

Decision: Treat Event Companion terrain placement rectangles as grid-snapped footprint polygons, reject overlapping placement candidates automatically, and auto-accept deterministic geometry warnings only when the snapped placements, printed measurement checks, official template matches, and Dense wall fragments pass the local checks.

Reasoning: The official layouts are deterministic: terrain footprints are intended as non-overlapping inch-grid placements, and the printed offset annotations provide independent measurement evidence. Requiring users to manually accept normal extraction warnings makes the app harder to use and does not improve geometry quality. The safer boundary is deterministic extraction plus explicit unresolved warnings only when checks actually fail.

Consequences:

- Event Companion terrain footprints are snapped to the 1-inch board grid before canonical layout creation.
- Overlapping snapped terrain candidates are removed by a stable confidence score; the layout records how many were removed.
- Snapped feature offsets are cross-checked against printed inch annotations when those annotations are available.
- Dense terrain footprint fragment paths are rendered as solid 2D LOS wall segments only after their footprint-template match is an accepted deterministic candidate; Light, Exposed, and Unknown terrain remain non-blocking context.
- Warning records resolved by deterministic checks are emitted with `review_status: accepted`, so LOS, heatmap, exposure, and terrain-coverage analysis can run without a manual GUI accept step.
- Ambiguous, weak, or low-confidence template matches remain `needs_review`, do not generate wall blockers, and keep official-layout analysis blocked until a future deterministic disambiguation pass resolves them. The legacy accept endpoint remains for compatibility and debugging, but the GUI no longer exposes manual warning-acceptance controls.

## 2026-06-17: Footprint Normalization Is Evidence-Only

Decision: Add terrain footprint normalization as a deterministic evidence report that extracts per-layout canonical footprint size options from snapped canonical terrain geometry, detects terrain footprint elements separately from the rendered Event Companion page image, and matches each raster element to the closest size option with 90 degree rotation allowed. Canonical size options collapse rotated equivalents, so `8x12` and `12x8` are one option.

Reasoning: GW layouts appear to reuse standard footprint sizes, but the current app only has one layout page normalized at a time. Per-layout size options give an auditable first normalization layer without inventing a global catalog before enough official pages have been cross-checked. Keeping the report evidence-only prevents CV segmentation errors or ambiguous size matches from mutating canonical layout geometry or LOS blockers.

Consequences:

- `/api/layouts/{layout_id}/footprint-normalization` exposes `options`, `detected_elements`, `matches`, and warning codes.
- The GUI shows Footprint Normalization as an advisory panel outside the blocking layout-load path.
- Ambiguous close-size matches and count mismatches report warnings instead of changing terrain footprints.
- A later global GW footprint catalog can aggregate repeated dimensions across all extracted pages once enough per-layout reports are stable.

## 2026-06-17: Symmetry Checks Are Advisory Evidence

Decision: Add a deterministic 180 degree rotational terrain symmetry report for every canonical layout, but keep it advisory and separate from validation readiness.

Reasoning: Official matched-play maps tend to be symmetric or near-symmetric, so symmetry is a useful extraction sanity check. It should not by itself mutate footprints, accept warnings, or block analysis because some official layouts can intentionally vary terrain size, category, or placement.

Consequences:

- `/api/layouts/{layout_id}/terrain-symmetry` reports matched feature count, max residual, unmatched feature IDs, and per-feature mirror matches.
- The GUI shows Symmetry in a collapsible technical evidence panel.
- Symmetry warnings support reviewer inspection but do not alter LOS, heatmap, exposure, or terrain-coverage behavior.

## 2026-06-17: Technical Evidence Panels Collapse By Default

Decision: Use native collapsible sections for dense technical evidence in the side panel, keeping only Layout open by default.

Reasoning: Source hashes, extraction methods, provisional match rows, normalization diagnostics, symmetry residuals, sanity checks, and validation records are important audit evidence but are not the first things a strategy user needs while interacting with the map.

Consequences:

- Sources, Rules, Footprints, Provisional Matches, Footprint Normalization, Symmetry, Sanity, and Validation remain available without dominating the viewport.
- Workflow panels for Terrain, Feature, LOS, and Analysis stay visible.
- Expanded technical rows must still wrap on mobile without horizontal overflow.

## 2026-06-17: Reconciliation Requires Independent Measurement And Symmetry Gates

Decision: Treat terrain reconciliation as a separate deterministic pass after source footprint extraction, map-image placement extraction, and grid snapping. The standard footprint catalog is a separate source step: Terrain Area Footprints provides template form and Dense wall fragment evidence, while the current parser derives standard inch-size evidence from official source-template matches across the extracted Event Companion corpus when explicit footprint dimensions are not present in the Terrain Area Footprints text layer. A final layout candidate must satisfy both positioned measurement checks and 180 degree one-to-one symmetry checks before it is considered resolved.

Reasoning: Terrain footprint forms, Dense wall fragments, and map placements are different evidence streams. Combining them too early can hide extraction mistakes, especially when a snapped placement looks plausible but violates printed edge measurements or map symmetry. Keeping measurement and symmetry as parallel final gates makes unresolved asymmetry visible and gives the reconciler a clear path for cycling through standard footprint options.

Consequences:

- Reconciliation reports expose a source-footprint-catalog step, map extraction, grid snap, measurement gate, symmetry gate, and final layout gate.
- Measurement checks require positioned inch annotations near all four corners of a snapped footprint; a globally matching number is not enough.
- Symmetry matching maximizes the one-to-one matched feature count before minimizing residuals, and requires matching category plus canonical dimensions, so duplicate terrain features cannot all claim the same mirrored partner.
- Alternative placements cycle source-catalog size options through self-centered and mirror-partner candidate placements, and are reported as viable candidates only when they are on the inch grid, do not overlap existing footprints, pass the positioned measurement gate, and satisfy symmetry.
- Source-catalog dimensions and Dense wall fragment counts are promoted only from deterministic candidate footprint-template matches; `needs_review` matches remain advisory evidence and cannot become authoritative reconciliation inputs.
- Viable candidates are not silently applied to canonical layouts yet; unresolved features remain warning-state evidence until a later deterministic promotion step is implemented.
