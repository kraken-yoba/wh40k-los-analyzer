# Codex Categorizer Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the placeholder ChatGPT subscription link with a real local Codex account/backend surface, and harden terrain-feature visual categorization around a known feature-type catalog.

**Architecture:** Codex owns credentials through `openai-codex`; the FastAPI app only reads sanitized status and starts local Codex login/logout flows. Visual model output remains structured artifact data that is validated by catalog version, feature digest, type ID, confidence, and duplicate checks before deterministic LOS blocker projection.

**Tech Stack:** Python 3.12, FastAPI/Jinja, `openai-codex`, Pydantic, Shapely, pytest, ruff, mypy. No JavaScript or TypeScript is used in this slice.

---

### Task 1: Codex Backend Account Surface

**Files:**
- Create: `src/warhammer_companion/integrations/codex_backend.py`
- Modify: `src/warhammer_companion/web/server.py`
- Modify: `src/warhammer_companion/web/templates/settings.html`
- Test: `tests/test_codex_backend.py`
- Test: `tests/test_web_server.py`

- [x] Write failing tests for SDK missing, authenticated, unauthenticated, login start, logout, and sanitized errors.
- [x] Add `openai-codex` as a dependency and implement a small integration wrapper.
- [x] Use the packaged `openai-codex-cli-bin` runtime rather than a globally installed Codex binary.
- [x] Store Codex state in the OS user-data directory by default, with a standalone packaging override.
- [x] Keep credentials outside app storage; never read or render `auth.json` contents.
- [x] Replace external ChatGPT links with POST-backed Codex browser login, device-code login, and logout actions.
- [x] Verify settings renders no custom JavaScript and no `https://chatgpt.com` placeholder link.

### Task 2: Known Terrain Feature Type Catalog

**Files:**
- Create: `src/warhammer_companion/ingestion/terrain_feature_catalog.py`
- Create: `src/warhammer_companion/catalog_assets/*.svg`
- Modify: `pyproject.toml`
- Test: `tests/test_terrain_feature_catalog.py`

- [x] Define catalog version, type IDs, display names, descriptions, representative top-down images, blocker templates, typical positions, default wall sides, and classification hints.
- [x] Include initial types: L ruin, U ruin, perimeter ruin, armoured container, solid blocker, and floor/platform.
- [x] Package catalog assets with the Python package.

### Task 3: Visual Categorizer Contract Hardening

**Files:**
- Modify: `src/warhammer_companion/ingestion/feature_categorizer.py`
- Modify: `src/warhammer_companion/ingestion/packet_builder.py`
- Test: `tests/test_feature_categorizer.py`
- Test: `tests/test_packet_builder.py`

- [x] Add catalog version, catalog options, `type_id`, feature position, and `feature_digest` to the categorizer request/result contract.
- [x] Apply catalog `type_id` to deterministic `feature_profile` and wall-side defaults.
- [x] Reject stale results when geometry digest changes.
- [x] Reject conflicting duplicate rows instead of last-write-wins.
- [x] Surface unmatched, low-confidence, stale-digest, and duplicate-conflict counts in ingestion reports.

### Task 4: Verification And Handoff

**Files:**
- Modify: `docs/work-log/official-ingestion.md`

- [x] Run `ruff format --check src tests`.
- [x] Run `ruff check src tests`.
- [x] Run `mypy src`.
- [x] Run `pytest -q`.
- [x] Run official page ingestion smoke.
- [x] Verify Settings, Map Data, Heatmap, and LOS Checker in the built-in browser.
- [ ] Commit and push the atomic slice.
