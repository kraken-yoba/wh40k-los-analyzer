# Roster Canonical Index And Snapshot Profiles QA Pathway

Date: 2026-06-21

## Scope

This QA pathway proves Phase 4B enriches admitted synthetic roster inputs with deterministic
canonical selection indexes and local unresolved snapshot profile/rule candidates. It must not
prove profile resolution, official points, legality, UI upload flows, movement/threat use, or AI
behavior.

## Automated Checks

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_profiles.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py tests\test_toolkit_contracts.py tests\test_rules_sources.py tests\test_base_sizes.py tests\test_terrain_semantics.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- Targeted snapshot profile tests pass.
- Existing roster safety, toolkit, source, base, and terrain regressions pass.
- Full suite, static checks, packet validation, desktop smoke, and diff checks pass.

## Manual Browser QA

Phase 4B changes no web UI. Because the user requested full manual QA for roadmap loops, launch
the local app and run the established Browser route sweep:

- `/viewer`
- `/heatmap`
- `/los-checker`
- `/hidden-coverage`
- `/settings`
- `/map-data`

Expected:

- No console errors.
- Map pages still render SVG outputs.
- Heatmap, LOS checker, and hidden coverage still render embedded PNG overlays.
- Existing forms preserve submitted values.

If Browser control fails:

- Record the exact Browser error.
- Try Computer Use with Firefox.
- Mark manual UI QA blocked only after both paths fail.

## Protected-Data Scan

Before staging, inspect staged files and confirm:

- No `.ros`, `.rosz`, `.cat`, `.catz`, `.gst`, `.gstz`, `.bsr`, `.bsi`, raw PDFs, public sheet
  exports, community catalogs, processed packs, screenshots, logs, SQLite/database files, or Codex
  state files are staged.
- Tests build tiny synthetic XML and ZIP bytes in memory.
- Rule/profile/characteristic strings in tests are synthetic and not copied from Games Workshop,
  community data, or user rosters.
- Canonical records do not retain rule description text; only hashes and lengths are exposed.
- Long characteristic values are also hash/length only.
- `AGENTS.md` remains unstaged unless the user explicitly asks to commit it.

## Reviewer Checklist

Approve only if:

- Snapshot profile/rule evidence is `estimated` local evidence.
- Every candidate is unresolved and cannot be used for profile resolution yet.
- Rule descriptions are not retained as canonical text.
- Duplicate raw IDs have non-colliding stable keys.
- Multi-force and structurally excessive XML are blocked with explicit reasons, not partially
  imported.
- Blocked imports have no army, no index, no profile pack, and no overlays.
- No result can claim legality, official points, trusted mechanics, recommendation, safety, or
  likely outcomes.
- Phase 4A malicious archive/XML regressions still pass.
