# Phase 9 Mission Pack Skeleton Implementation Plan

Date: 2026-06-22

Goal: add source-safe mission pack records and a thin Mission Pack product surface without storing
protected mission content or implementing scoring mechanics.

## Task 1: Domain And Builder Tests

- [ ] Add failing tests in `tests/test_mission_pack_toolkit.py` for:
  - mission labels from `OFFICIAL_LAYOUT_PAGE_METADATA` are deduplicated into primary mission
    records;
  - stable ids are normalized from labels;
  - each mission has source refs and at least one source page anchor;
  - result readiness is `estimated`, has no overlays, and cannot use recommendation language;
  - public Google Sheet source is present as untrusted candidate metadata only;
  - public Google Sheet metadata stores only the supplied URL, sheet id, gid `1565185881`,
    retrieval status `not_fetched`, trust `untrusted_candidate`, and no content hash;
  - warnings explicitly state mechanics/scoring/actions are source-pending and public sheet data is
    not ingested;
  - no record contains card image URLs or long card/rules text.

## Task 2: Mission Domain And Builder

- [ ] Add `domain/missions.py` with typed records:
  - source ref;
  - source anchor;
  - mission record;
  - mission pack;
  - mission pack payload.
- [ ] Add `application/mission_pack.py` with:
  - stable id normalization;
  - `build_mission_pack_toolkit_result(...)`;
  - public sheet candidate source metadata constant using the supplied URL and gid `1565185881`.
- [ ] Use existing official layout metadata only; do not fetch network resources.

## Task 3: Service And UI Adapters

- [ ] Add `MissionPackState` to `application/view_models.py`.
- [ ] Add `mission_pack_state(...)` and `mission_pack_toolkit_result(...)` to the shared service.
- [ ] Add web GET `/mission-pack` and `web/templates/mission_pack.html`.
- [ ] Add `Mission Pack` to web navigation.
- [ ] Add desktop `MissionPackScreen`, main-window navigation, and desktop smoke key
  `mission_pack_estimate`.

## Task 4: Documentation And QA

- [ ] Update README route list.
- [ ] Update `docs/qa-scenarios.md` with a mission-pack skeleton scenario.
- [ ] Update `docs/work-log/player-toolkit-implementation.md`.

## Task 5: Verification

- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_mission_pack_toolkit.py tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

- [ ] Browser QA:
  - `/mission-pack`;
  - verify heading, source warning, primary mission table, one form or no form as designed, zero
    `<script>` tags, no traceback/internal error text, and no console warning/error logs.

## Task 6: Protected Path And Commit

- [ ] Confirm changed files exclude generated/raw/cache/log/build/dist/PDF/database/archive/image
  paths and credentials.
- [ ] Confirm no mission-card images, screenshots, Google Sheet exports, or full card text are
  committed.
- [ ] Keep `AGENTS.md` untracked and unstaged unless explicitly requested.
- [ ] Commit as one atomic Phase 9 commit.
