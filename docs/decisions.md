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
