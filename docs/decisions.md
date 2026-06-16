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
