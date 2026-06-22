# Phase 6.5 Adversarial Review - Threat Housekeeping

Date: 2026-06-22

## Initial Verdict

CHANGES_REQUESTED.

## Finding

- Static checks failed after the first implementation because `threat_range.py` imports were not in
  Ruff order and the file needed formatting.

## Fix

- Reordered the `base_center_region` import before `warhammer_companion.los.threat` imports.

## Fresh Local Evidence After Fix

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_movement_reach_geometry.py tests\test_threat_range_toolkit.py -q
```

Result: `13 passed`.

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
```

Result: `110 files already formatted`; `All checks passed!`.

## Final Verdict

APPROVED.

## Final Re-Check Notes

- No behavior drift found.
- Dependency boundary remains correct: `los/movement.py` owns reusable geometry, while
  `application/threat_range.py` owns `BlockReason` policy.
- Focused helper tests, static checks, broader adapter tests, full pytest, desktop smoke, and
  `git diff --check` passed.
- Browser QA was not required for the pure helper extraction, but was completed anyway for
  `/movement-reach` and `/threat-range`.
