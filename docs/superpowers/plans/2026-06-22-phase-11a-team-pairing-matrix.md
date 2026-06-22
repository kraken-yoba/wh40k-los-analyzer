# Phase 11A Team Pairing Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cautious Team Pairing Matrix V0 that aggregates existing deterministic toolkit
results into component cards without claims of optimization, expected points, or win probability.

**Architecture:** Add a typed matchup domain model and pure application builder, then expose it
through the existing shared service layer, server-rendered web route, and PySide6 desktop screen.
The matrix is degraded by design because roster-aware mission scoring and calibrated pairing models
are unavailable.

**Tech Stack:** Python 3.12, dataclasses, FastAPI/Jinja, PySide6, pytest, Ruff, mypy.

---

## Task 1: Domain And Builder Tests

**Files:**

- Create: `tests/test_matchup_matrix_toolkit.py`
- Later create: `src/warhammer_companion/domain/matchups.py`
- Later create: `src/warhammer_companion/application/matchup_matrix.py`

- [ ] Add tests for the valid degraded matrix:
  - build a matrix for friendly labels `("Alpha", "Beta")` and opponent labels
    `("Gamma", "Delta")`;
  - assert `tool_id == "team_pairing_matrix"`;
  - assert readiness is `degraded`;
  - assert four cells exist;
  - assert each cell has `damage-output`, `mission-context`, `deployment-staging`, and
    `unsupported-data` component ids;
  - assert no `total_score`, `rank`, `grade`, `expected_points`, `win_probability`, or
    `recommendation` attribute exists.
  - assert repeated damage/deployment metrics are labeled as shared scenario metrics, not
    pair-specific findings.
- [ ] Add tests for blocked labels:
  - empty/whitespace-only friendly labels block with reason id `missing-friendly-lists`;
  - empty/whitespace-only opponent labels block with reason id `missing-opponent-lists`;
  - more than eight labels per side block with `too-many-friendly-lists` or
    `too-many-opponent-lists`;
  - duplicate normalized labels block with `duplicate-friendly-list-label` or
    `duplicate-opponent-list-label`;
  - labels longer than 80 characters block with `friendly-list-label-too-long` or
    `opponent-list-label-too-long`;
  - blocked results have no matrix cells.
- [ ] Add tests for label normalization:
  - comma and newline separators both create labels;
  - input order is preserved after normalization;
  - internal whitespace collapses to one space;
  - non-printing control characters are removed before duplicate/length checks;
  - empty separator fragments are dropped without changing stable ids for remaining labels.
- [ ] Add tests for deterministic identity:
  - changing a friendly label changes `input_hash`;
  - changing a source result hash changes `input_hash`;
  - result id suffix matches the input hash prefix.
- [ ] Add tests for scenario ranges:
  - expected damage min/max use the manual damage result;
  - expected models destroyed min/max use the manual damage result;
  - threat probability range uses going-first and going-second deployment scorecard payload values.
- [ ] Add tests for visible text safety:
  - component details/warnings do not contain forbidden authority claims.
- [ ] Add tests for payload/source safety:
  - aggregate `ToolkitResult.overlays == ()`;
  - serialized payload contains no `MapPacket`, Shapely geometry, SVG, image extension, source URL,
    Google Sheet id/gid, or source payload object representation;
  - component readiness values are only `trusted`, `estimated`, `degraded`, or `blocked`;
  - `unsupported-data` has `assessment == "not_available"`, `readiness == "degraded"`, and no
    source result id/input hash.
- [ ] Add tests for source blocker propagation:
  - blocked damage results become blocked damage component cards while the matrix remains degraded
    if mission/deployment components are still usable;
  - blocked deployment scorecards become blocked deployment component cards while other usable
    components remain visible.
- [ ] Run the new tests and confirm they fail because the matchup modules do not exist.

## Task 2: Domain Model And Builder

**Files:**

- Create: `src/warhammer_companion/domain/matchups.py`
- Create: `src/warhammer_companion/application/matchup_matrix.py`

- [ ] Implement typed dataclasses:
  - `PairingListEntry`;
  - `PairingScenario`;
  - `PairingMetric`;
  - `PairingScenarioRange`;
  - `PairingComponentCard`;
  - `PairingCell`;
  - `PairingMatrixPayload`.
- [ ] Implement literals/constants:
  - component ids `damage-output`, `mission-context`, `deployment-staging`, `unsupported-data`;
  - assessments `checked`, `warning`, `blocked`, `not_available`;
  - schema version `team-pairing-matrix/v0`.
- [ ] Implement `build_team_pairing_matrix_toolkit_result(...)` accepting:
  - `packet`;
  - `friendly_labels`;
  - `opponent_labels`;
  - `damage_result`;
  - `mission_result`;
  - `deployment_scorecard_results`.
- [ ] Normalize labels by splitting on commas/newlines, stripping whitespace, collapsing internal
  whitespace to one space, removing non-printing control characters, dropping empty fragments,
  preserving input order, blocking more than eight labels per side, checking duplicate normalized
  labels, blocking overlong labels, and assigning stable ids `friendly-1`, `opponent-1`, etc.
- [ ] Return blocked with no cells for missing side labels.
- [ ] Build deterministic components from source toolkit result ids/input hashes/readiness.
- [ ] Store only sanitized scalar dossier fields in the payload: no `MapPacket`, source payloads,
  overlays, geometry, SVG, images, source URLs, Google Sheet id/gid, mission-card text, official
  rules text, or generated source payloads.
- [ ] Force `ToolkitResult.overlays=()`.
- [ ] Build one scenario record from packet/mission/deployment assumptions.
- [ ] Compute cell readiness using the spec semantics.
- [ ] Force valid Phase 11A result readiness to `degraded`; return `blocked` only for input
  blockers or no usable deterministic components. Never return `trusted`.
- [ ] Add canonical JSON hashing with schema version, labels, packet id, and source input hashes.
- [ ] Run `tests/test_matchup_matrix_toolkit.py -q` and confirm it passes.

## Task 3: Service And View State

**Files:**

- Modify: `src/warhammer_companion/application/services.py`
- Modify: `src/warhammer_companion/application/view_models.py`
- Modify: `src/warhammer_companion/desktop/app.py`
- Modify: `tests/test_application_service.py`

- [ ] Add `TeamPairingMatrixState` to `view_models.py`.
- [ ] Add `team_pairing_matrix_toolkit_result(...)` to `WarhammerCompanionService`.
- [ ] Add `team_pairing_matrix_state(...)` to `WarhammerCompanionService`.
- [ ] The service must build:
  - default damage profile toolkit result;
  - mission pack toolkit result;
  - two deployment scorecard results for `going-first` and `going-second` using the selected packet
    and existing default manual deployment inputs.
- [ ] Add service tests for:
  - valid state has degraded readiness and four default cells;
  - blocked state from empty labels has no cells and user-facing blocker text;
  - warning details mention source-pending/unavailable data.
- [ ] Extend desktop smoke summary with `team_pairing_matrix_degraded: true`.
- [ ] Run focused service tests.

## Task 4: Web Route And Template

**Files:**

- Modify: `src/warhammer_companion/web/server.py`
- Modify: `src/warhammer_companion/web/templates/base.html`
- Create: `src/warhammer_companion/web/templates/team_pairing.html`
- Modify: `tests/test_web_server.py`

- [ ] Add GET `/team-pairing` route with packet selector and comma/newline friendly/opponent label
  inputs.
- [ ] Add POST `/team-pairing` redirect preserving resolved packet id and label strings.
- [ ] Add navigation link `Team Pairing`.
- [ ] Create template showing:
  - readiness;
  - scenario assumptions;
  - warning/blocker lists;
  - matrix table with component ids/assessments/details;
  - scenario range table.
- [ ] Do not add custom JavaScript.
- [ ] Add web tests for:
  - default route renders heading, matrix labels, degraded readiness, unsupported-data, and no
    `<script>`;
  - blocked empty-label route shows blocker text and no cell table body;
  - POST redirect preserves labels and packet selection;
  - forbidden authority claims are absent from normalized visible text.
  - labels such as `<script>alert(1)</script>`, quotes, duplicates, and long labels are escaped or
    blocked as specified;
  - comma/newline splitting, whitespace collapse, control-character removal, empty-fragment
    dropping, and order preservation are visible in the rendered labels;
  - rendered text does not expose `docs.google.com`, the public sheet id/gid, source URLs,
    mission-card text, raw official text, or exported source payloads.
- [ ] Run focused web tests.

## Task 5: Desktop Screen

**Files:**

- Create: `src/warhammer_companion/desktop/screens/team_pairing.py`
- Modify: `src/warhammer_companion/desktop/main_window.py`
- Modify: `tests/test_desktop_app.py`

- [ ] Add a thin `TeamPairingScreen` with two plain-text inputs, a Generate button, status label,
  matrix detail label, blocker/warning label, and scenario range label.
- [ ] Add screen to `MainWindow` navigation after `Mission Pack`.
- [ ] Add desktop test verifying:
  - navigation contains `Team Pairing`;
  - default screen status includes degraded/source-pending/unavailable wording;
  - matrix detail label includes rows, columns, component ids, assessments, and details;
  - warning/blocker label includes cautious warning text;
  - scenario range label includes deterministic range labels;
  - empty labels produce blocked status.
  - `<script>alert(1)</script>` labels render as plain text, not rich text.
- [ ] Run focused desktop tests.

## Task 6: Documentation, QA, And Verification

**Files:**

- Modify: `README.md`
- Modify: `docs/qa-scenarios.md`
- Modify: `docs/work-log/player-toolkit-implementation.md`

- [ ] Update README user-facing tool list with Team Pairing Matrix.
- [ ] Add a Team Pairing Matrix scenario to `docs/qa-scenarios.md`.
- [ ] Update the work log with Phase 11A decisions, TDD red/green evidence, verification, manual QA,
  review, and blockers.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_matchup_matrix_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

- [ ] Launch the local web app and run Browser QA if Browser control is available. If Browser
  control is unavailable, document the blocker and run local HTTP fallback checks against
  `/team-pairing`, a valid label query, and an empty-label blocked query.
- [ ] Run consultant/spec compliance and adversarial code-quality review.
- [ ] Run protected-path and new-content source/credential scans.
- [ ] Stage only intended Phase 11A files, leaving `AGENTS.md` untracked.
- [ ] Commit as one atomic Phase 11A commit.
