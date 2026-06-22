# Phase 8.5 Damage Profile Defaults Housekeeping Implementation Plan

Date: 2026-06-22

Goal: centralize Phase 8A manual Damage Profile default values without changing behavior.

## Task 1: Guardrail Tests

- [ ] Add or update tests proving:
  - `DEFAULT_DAMAGE_PROFILE_INPUT` contains attacks 2, hit 4, wound 4, save 4, damage 2.
  - `DEFAULT_TARGET_PROFILE_INPUT` contains wounds/model 2 and model count 3.
  - `WarhammerCompanionService.damage_profile_state()` uses those defaults and still yields expected
    damage 0.50.
  - Desktop `DamageProfileScreen` initial controls match those defaults.

## Task 2: Centralized Defaults

- [ ] Add canonical default constants to `domain/damage.py`.
- [ ] Import and use those constants in:
  - `application/services.py`;
  - `web/server.py`;
  - `desktop/screens/damage_profile.py`;
  - relevant tests.
- [ ] Do not centralize web query/form field names in the domain layer.

## Task 3: Documentation And Log

- [ ] Update the Phase 8.5 work-log entry with scope, decisions, verification, and reviewer
  outcomes.
- [ ] Add consultant and adversarial review records.

## Task 4: Verification

- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py tests\test_application_service.py tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

- [ ] Browser QA for `/damage-profile` default route:
  - heading `Damage Profile`;
  - one form;
  - zero `<script>` tags;
  - expected damage `0.50`;
  - distribution rows `49/64`, `14/64`, `1/64`;
  - manual estimate/effective save/unsupported effects warning copy;
  - no warning/error console logs.

## Task 5: Protected Path And Commit

- [ ] Confirm staged candidates exclude generated/raw/cache/log/build/dist/PDF/database/archive/image
  paths and credentials.
- [ ] Keep `AGENTS.md` untracked and unstaged unless explicitly requested.
- [ ] Commit as one atomic Phase 8.5 housekeeping commit.
