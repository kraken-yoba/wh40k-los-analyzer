# Phase 7.5 Adversarial Review - Exposure Mode Housekeeping

Date: 2026-06-22

## Initial Verdict

REQUIRED CHANGES.

## Findings

- The proposed helper extraction was valid, but service/rendering QA was too weak. Existing coverage
  only checked `threat-and-los`, so a swapped helper call could still pass.
- Invalid-mode behavior needed direct protection. Unsupported raw `exposure_mode` values must keep
  returning `blocked` with `invalid-exposure-mode` and no overlays.
- Helper semantics needed clarification: these helpers mean component diagnostic/overlay inclusion,
  not selected exposure risk composition.

## Applied Plan Changes

- Added parameterized service/rendering coverage for all four modes.
- Added direct unsupported-mode blocking regression.
- Clarified that `threat-and-los` includes both component overlays while selected risk remains an
  intersection in `los/exposure.py`.
- Kept `AGENTS.md` explicitly out of commit scope.

## Re-Review Finding

REQUIRED CHANGES.

The QA intent was sound, but the plan had implementation details that would fail:

- The service test snippet used a non-existent `MapRepository.in_memory(...)` API and positional
  `WarhammerCompanionService(...)` construction.
- `_placement_diagnostic(...)` still typed `exposure_mode` as `str`, which would conflict with
  helpers typed as `ExposureMode`.
- The file map omitted `tests/test_application_service.py`.

## Applied Plan Fixes

- Updated the service test snippet to use the existing
  `WarhammerCompanionService(paths=IngestionPaths(), repository=StaticMapRepository(...),
  codex_backend=server.codex_backend)` pattern.
- Added an explicit implementation step to import `ExposureMode` and type `_placement_diagnostic`
  with it.
- Added `tests/test_application_service.py` to the file map.

## Plan Re-Review Verdict

APPROVED.

## Implementation Review

Initial implementation verdict: REQUIRED CHANGES.

No Python code blockers were found, and focused regressions passed in the reviewer environment, but
the plan-required Phase 7.5 work-log entry was missing.

Applied fix:

- Added the Phase 7.5 entry to `docs/work-log/player-toolkit-implementation.md` with scope,
  red/green evidence, reviewer outcomes, Browser QA, protected-path scan status, and remaining
  blocker status.
