# End-To-End Product Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Warhammer 40k LOS Analyzer end to end with deterministic extraction, canonical validation, LOS analysis, complete local GUI workflows, browser-tested UX, reviewer approval, security review, and public GitHub readiness.

**Architecture:** Python-only FastAPI app serving APIs, Jinja2 templates, CSS, and vanilla JavaScript. Deterministic extraction and geometry live in focused Python modules with Pydantic schemas. The GUI consumes backend JSON and renders board overlays with SVG/Canvas.

**Tech Stack:** Python 3.12, uv, FastAPI, Jinja2, Pydantic, PyMuPDF, OpenCV, Shapely, pytest, pytest-playwright, Ruff, mypy, Python Playwright, GitHub Actions.

**Implementation Order:** Build the deterministic synthetic data spine first, then the LOS kernel, then fixture-first GUI workflows, then official-PDF extraction. Official PDFs are an input adapter into the canonical model, not the foundation of the project.

---

## Execution Rules

- Use TDD for every behavior-bearing slice.
- Commit each completed slice atomically.
- Update `docs/work-log.md` after each substantial checkpoint.
- Update `docs/decisions.md` when the spec is ambiguous or an implementation tradeoff is settled.
- Use consultant subagents for uncertain research, extraction-risk analysis, and gap analysis.
- Use targeted adversarial reviewer subagents after each major slice before moving on.
- Use Browser plugin verification for GUI workflows.
- Use Codex Security and CodeRabbit review before claiming the product is complete.
- Keep `docs/browser-evidence.md` current once GUI workflows exist.
- Write a detailed phase plan before each behavior-bearing phase; this master plan defines ordering and gates, not line-by-line implementation.

## User Workflows For Browser UX Testing

1. Open the local app and confirm the dashboard loads without external network access.
2. View source manifest status and verify official PDF source URLs/hashes are visible.
3. Trigger or inspect extraction for a terrain layout.
4. Inspect the PDF underlay with extracted board, footprint, wall, label, and deployment overlays.
5. Click an extracted feature and view provenance, validation status, and warnings.
6. Mark a warning as accepted with warnings and confirm strategy views show degraded status.
7. Select a terrain layout and deployment map.
8. Select a firing point on the map and view point LOS coverage.
9. Select a base size and view base-aware LOS coverage.
10. Generate a firing-lane heatmap from a deployment/source region and inspect legend/tooltips.
11. Generate deployment exposure for a movement distance and threat/source region.
12. Select a terrain feature and inspect geometric LOS contribution metrics.
13. Export a reproducible analysis bundle and confirm it includes parameters, hashes, validation, and warnings.

## Major Slices

### Slice 1: Infrastructure Completion

- Finalize Python-only plan/spec updates.
- Add work log and decision log.
- Add schemas/fixtures docs, verification scripts, dev script, and Python-only CI.
- Verify Ruff, mypy, and pytest pass.
- Commit the checkpoint.

### Slice 2: Deterministic Data Spine

- Implement Pydantic models for source manifests, canonical layouts, validation states, warning/error records, review state, geometry primitives, and export bundles.
- Generate JSON Schema into `schemas/`.
- Add synthetic manifest fixtures, canonical layout fixtures, schema tests, and stable hash tests.
- Add validator rules for board bounds, footprint bounds, blocker bounds, deployment bounds, IDs, provenance, and warning states.
- Add source-hash mismatch tests.

### Slice 3: Geometry And LOS Engine

- Implement geometry primitives and blocker predicates against canonical fixtures.
- Implement point LOS and base-aware disk-to-disk LOS using an explicit deterministic contract.
- Implement legal base-center checks.
- Add fixtures for tangent endpoints, sealed endpoints, collinear overlap, contextual footprints, board clipping, and disk-to-disk visibility cases.

### Slice 4: Heatmap, Deployment Exposure, And Terrain Metrics

- Implement point-sampled heatmap generation with raw counts and normalized visibility.
- Implement movement reachability approximation and deployment exposure metrics.
- Implement terrain contribution metrics by including/excluding selected blockers.
- Add synthetic tests for known blocker layouts and zero-source/no-data cases.

### Slice 5: Fixture-First API And GUI Completion

- Implement source status, layout QA, review queue, provenance panel, LOS simulator, heatmap controls, exposure controls, terrain metrics, and export flow against synthetic fixtures first.
- Keep browser-side JavaScript small and deterministic.
- Add Python endpoint tests for each workflow.
- Add Python Playwright tests for key flows once the local server harness exists.

### Slice 6: Browser UX Verification

- Use Browser plugin to run the local app.
- Execute all user workflows listed above.
- Capture screenshots or inspection notes for each workflow in `docs/browser-evidence.md`.
- Fix UI or workflow gaps until the flow is complete.

### Slice 7: Deterministic PDF Acquisition And Rendering

- Implement official source manifest loading and local PDF cache checks.
- Implement download/cache path handling without committing PDFs.
- Implement deterministic page rendering metadata contracts.
- Add synthetic PDF/rendering fixtures where possible and official-cache gated tests.

### Slice 8: Extraction Pipeline MVP

- Implement text/vector extraction interfaces.
- Implement rendered-page CV extraction interfaces.
- Implement deterministic merge/precedence rules and validation state assignment.
- Build at least one synthetic board fixture that exercises board bounds, footprints, blockers, labels, dimensions, and deployments.

### Slice 9: Independent Review Gates

- Run an adversarial extraction/LOS reviewer subagent against implementation and tests.
- Run an adversarial UX reviewer subagent against Browser workflow evidence.
- Fix all valid findings.

### Slice 10: Security, Code Quality, And GitHub Readiness

- Run Codex Security review.
- Run CodeRabbit review when repository/PR state allows it.
- Fix all valid findings or document non-issues with reasoning.
- Repair GitHub authentication if needed, create/push public repository when authorized, and verify CI.

## Browser Evidence Matrix

Maintain `docs/browser-evidence.md` with one row per user workflow:

- Workflow ID and name.
- Fixture or official-cache input used.
- API endpoint or browser state exercised.
- Playwright test name, when available.
- Browser-plugin evidence path or inspection note.
- Pass/fail state and linked fix commit.

## Exit Conditions

- Independent reviewer subagent verifies extraction and LOS calculation work correctly.
- Independent reviewer subagent verifies browser-tested UX is complete end to end.
- Ruff, mypy, pytest, Python Playwright tests, security review, and code review have no unresolved critical or high findings.
- Work log and decision log are current.
- Git history contains atomic commits for each major checkpoint.
