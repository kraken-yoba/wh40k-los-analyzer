# Phase 11A Team Pairing Matrix QA Pathway

Date: 2026-06-22

## Purpose

Prove Phase 11A adds a deterministic, degraded Team Pairing Matrix dossier that aggregates existing
toolkit outputs without optimizer, expected-points, win-probability, calibration, or source-ingestion
claims.

## Preconditions

- Branch is `codex/assistant-companion-roadmap`.
- `AGENTS.md` may be untracked and must remain unstaged unless the user explicitly requests
  otherwise.
- Official seed packets are available from `src/warhammer_companion/seed_data/map-packets`.
- The phase spec is
  `docs/superpowers/specs/2026-06-22-phase-11a-team-pairing-matrix.md`.
- The implementation plan is
  `docs/superpowers/plans/2026-06-22-phase-11a-team-pairing-matrix.md`.

## Automated QA

Run:

```powershell
git status --short --branch
.\.venv\Scripts\python.exe -m pytest tests\test_matchup_matrix_toolkit.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_web_server.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Expected:

- Focused Team Pairing tests pass.
- Focused application/web/desktop tests pass.
- Ruff format/check passes.
- Ruff check passes.
- mypy passes.
- Full pytest passes.
- Desktop smoke reports `status: ok` and `team_pairing_matrix_degraded: true`.

## Web Manual QA

Launch:

```powershell
.\.venv\Scripts\python.exe -m warhammer_companion.app
```

Open:

- `/team-pairing`
- `/team-pairing?friendly_lists=Alpha%0ABeta&opponent_lists=Gamma%0ADelta`
- `/team-pairing?friendly_lists=Alpha%20%20Prime%2C%2C%20%20Beta%0AControl%07Name&opponent_lists=Gamma%2C%2C%20Delta`
- `/team-pairing?friendly_lists=&opponent_lists=Gamma%0ADelta`
- `/team-pairing?friendly_lists=%3Cscript%3Ealert(1)%3C%2Fscript%3E&opponent_lists=Gamma`
- `/team-pairing?friendly_lists=A%0AB%0AC%0AD%0AE%0AF%0AG%0AH%0AI&opponent_lists=Gamma`

Expected:

- Valid pages render heading `Team Pairing`.
- Valid pages show degraded readiness, default matrix rows/columns, component cards, and
  `unsupported-data`.
- Valid pages state that labels-only cells use shared scenario metrics, not pair-specific
  list-vs-list computation.
- The normalization route shows labels in input order as `Alpha Prime`, `Beta`, and `ControlName`
  on the friendly side and `Gamma`, `Delta` on the opponent side.
- The normalization route does not show doubled internal spaces, the control character, or empty
  label fragments.
- Valid pages show deterministic scenario ranges and source-pending/unavailable warnings.
- Blocked empty-label page shows `missing-friendly-lists`, no matrix cells, and no traceback.
- Unsafe label text is escaped on web; `<script>alert(1)</script>` is visible as text and does not
  execute.
- Overflow-label pages show `too-many-friendly-lists` and no matrix cells.
- Pages contain zero `<script>` tags.
- Pages contain no traceback or internal server error text.
- User-facing visible text does not contain exact authority phrases as word-boundary matches:
  `legal`, `safe`, `optimal`, `recommended`, `likely`, `guaranteed`, `preferred`, `pairing score`,
  `expected points`, `win probability`, `favored`, or `calibrated`.
- Pages do not render `docs.google.com`, the public sheet id/gid, source URLs, mission-card text,
  raw official rules text, SVG/image payloads, or source toolkit payload representations.
- `/team-pairing` performs no network access, public sheet fetch, PDF fetch, source refresh, or
  external AI call.
- If Browser control is available, the console has no warning/error logs.
- If Browser control is unavailable, record the blocker and run local HTTP fallback checks for the
  same pages.

## Desktop QA

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_desktop_app.py::test_desktop_team_pairing_screen_reports_degraded_matrix_and_blockers -q
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Expected:

- Navigation contains `Team Pairing`.
- Default screen status says degraded and source-pending/unavailable.
- Matrix summary contains default friendly/opponent labels and component ids.
- Empty labels produce blocked status.
- Labels are rendered with Qt plain text handling.
- Desktop text does not expose source URLs, the public sheet id/gid, source payloads, SVG/image
  payloads, or forbidden authority phrases.
- Smoke JSON contains `team_pairing_matrix_degraded: true`.

## Protected Source And Credential QA

Scan all staged and untracked Phase 11A candidates before commit.

Expected:

- No files under generated/local/protected paths are staged:
  - `data/raw/`, `data/processed/`, `data/cache/`, `data/codex-home*`, `build/`, `dist/`,
    `logs/`, `.codex/`, `.agents/`.
- No raw PDFs, processed packets, SQLite/database files, image files, screenshots, exports, roster
  archives, or Google Sheet payloads are staged.
- No Codex/OpenAI credentials, API keys, tokens, browser sessions, cookies, or auth files are
  staged.
- No new public Google Sheet fetch output, mission-card text, card images, or official rules text is
  introduced.

## Review Gates

- Consultant review must approve the slice boundary and missing-data semantics.
- Adversarial review must approve that the implementation does not create hidden recommendations,
  scores, expected-points claims, source-ingestion leaks, or unsafe export surfaces.
- Any Critical or Important review issue must be fixed and re-reviewed before commit.

## Commit Gate

Expected final status:

- Only intended Phase 11A files are staged.
- `AGENTS.md` remains untracked/unstaged.
- One atomic commit records the Phase 11A implementation.
