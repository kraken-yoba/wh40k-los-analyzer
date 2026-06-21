# Roster Import Safety And Source Records QA Pathway

Date: 2026-06-21

## Scope

This QA pathway proves Phase 4A safely admits synthetic `.ros`/`.rosz` inputs into local source
records and shallow canonical roster snapshots. It must not prove profile resolution, official
points, list legality, UI upload flows, movement/threat use, or AI behavior.

## Automated Checks

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_import_safety.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_roster_import_safety.py tests\test_toolkit_contracts.py tests\test_rules_sources.py tests\test_base_sizes.py tests\test_terrain_semantics.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected:

- Targeted roster import tests pass.
- Existing toolkit/source/base/terrain regressions pass.
- Full suite, static checks, packet validation, desktop smoke, and diff checks pass.

## Manual Browser QA

Phase 4A changes no web UI. Because the user requested full manual QA for the ongoing phase loops,
launch the local app and run the established Browser route sweep:

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

## Protected-Data Scan

Before staging, inspect staged files and confirm:

- No `.ros`, `.rosz`, `.cat`, `.catz`, `.gst`, `.gstz`, `.bsr`, `.bsi`, raw PDFs, public sheet
  exports, community catalogs, processed packs, screenshots, logs, SQLite/database files, or Codex
  state files are staged.
- Tests build tiny synthetic XML and ZIP bytes in memory.
- No copied rules, card, datasheet, profile, roster, or community-catalog text is included.
- `AGENTS.md` remains unstaged unless the user explicitly asks to commit it.

## Reviewer Checklist

Approve only if:

- Archive inspection rejects traversal, absolute paths, nested archives, encryption flags,
  unexpected extensions, excess members, excess size, and high ratio.
- XML pre-screen rejects `DOCTYPE`, DTD/entity constructs, XInclude, malformed XML, and URLs before
  any canonical roster is produced.
- Safe imports are `estimated`, not `trusted`.
- Unsafe imports are `blocked`, have block reasons, and have no tactical overlays.
- Imported costs are "as presented" local evidence, not official points authority.
- No downstream solver or UI path can treat Phase 4A outputs as legal/safe/recommended.
