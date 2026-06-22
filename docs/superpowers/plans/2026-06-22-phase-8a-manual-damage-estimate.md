# Phase 8A Manual Damage Estimate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a manual estimated damage math toolkit without claiming roster/profile authority.

**Architecture:** Add typed damage records in `domain`, pure deterministic probability helpers in
the application layer, a `ToolkitResult` builder, then expose it through the shared service, web
route, and desktop screen. Web and desktop stay thin adapters with no custom JavaScript.

**Tech Stack:** Python 3.12, pytest, FastAPI/Jinja, PySide6, Ruff, mypy.

---

## File Map

- Create: `src/warhammer_companion/domain/damage.py`
- Create: `src/warhammer_companion/application/damage_profile.py`
- Modify: `src/warhammer_companion/application/services.py`
- Modify: `src/warhammer_companion/application/view_models.py`
- Modify: `src/warhammer_companion/web/server.py`
- Create: `src/warhammer_companion/web/templates/damage_profile.html`
- Modify: `src/warhammer_companion/web/templates/base.html`
- Create: `src/warhammer_companion/desktop/screens/damage_profile.py`
- Modify: `src/warhammer_companion/desktop/main_window.py`
- Modify: `src/warhammer_companion/desktop/app.py`
- Create: `tests/test_damage_profile_toolkit.py`
- Modify: `tests/test_application_service.py`
- Modify: `tests/test_web_server.py`
- Modify: `tests/test_desktop_app.py`
- Modify: `README.md`
- Modify: `docs/qa-scenarios.md`
- Modify: `docs/work-log/player-toolkit-implementation.md`
- Create/modify review docs under `docs/superpowers/reviews/`.

## Task 1: Domain Records And Pure Damage Math

- [ ] Add failing tests in `tests/test_damage_profile_toolkit.py` for:
  - D6 threshold probability for 2+, 4+, and 6+;
  - invalid threshold blocks via the result builder;
  - every declared invalid-input blocker class: zero attacks, negative attacks,
    non-integer attacks, non-finite attacks, thresholds outside 2+ to 6+,
    target wounds/model less than or equal to zero, non-integer target wounds/model,
    non-finite target wounds/model, target model count less than or equal to zero,
    non-integer target model count, non-finite target model count, negative damage,
    and non-finite damage;
  - 2 attacks, 4+ hit, 4+ wound, 4+ effective save, damage 2, target wounds/model 2, model count 3
    yields expected hits 1.0, expected wounds 0.5, expected unsaved wounds 0.25, expected damage
    0.5, expected models destroyed 0.25, and at-least-one-model probability 15/64;
  - kill distribution uses no spillover: 3 unsaved wounds at 3 damage into 5-wound models destroys
    1 model because damage accumulates on the active model but excess attack damage does not spill;
  - kill distribution discards overkill: 2 unsaved wounds at 6 damage into 5-wound models destroys
    2 models, not more;
  - warning text avoids `legal`, `optimal`, `recommended`, `likely`, `target priority`,
    `bad target`, and positive `official`/`profile-resolved` claims.
- [ ] Create `domain/damage.py` with:
  - `DAMAGE_PROFILE_TOOLKIT_SCHEMA_VERSION`;
  - `DamageProfileInput`;
  - `TargetProfileInput`;
  - `DamageProbabilityRow`;
  - `DamageEstimateSummary`;
  - `DamageEstimatePayload`.
- [ ] Create `application/damage_profile.py` with:
  - `d6_threshold_probability(threshold: int) -> float`;
  - `binomial_distribution(trials: int, probability: float) -> tuple[DamageProbabilityRow, ...]`;
  - `models_destroyed_distribution(...)`;
  - `build_damage_profile_toolkit_result(...)`.
- [ ] Result builder validation must block:
  - non-integer or less-than-one attacks;
  - thresholds outside 2..6;
  - non-integer, non-finite, or less-than-one target wounds/model;
  - non-integer, non-finite, or less-than-one target model count;
  - negative/non-finite damage.
- [ ] Result builder warnings must include the required manual-estimate trust wording.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py -q
```

## Task 2: Service State

- [ ] Add failing tests in `tests/test_application_service.py` proving:
  - `damage_profile_toolkit_result(...)` wraps the builder and preserves no recommendation language;
  - `damage_profile_state(...)` exposes manual inputs, summary values, distributions, warnings, and
    block details.
- [ ] Add `DamageProfileState` to `application/view_models.py`.
- [ ] Add service methods:
  - `damage_profile_toolkit_result(...)`;
  - `damage_profile_state(...)`.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_damage_profile_toolkit.py tests\test_application_service.py -q
```

## Task 3: Web Route

- [ ] Add failing tests in `tests/test_web_server.py` for:
  - GET `/damage-profile` renders controls, warnings, summary, distribution table, and no
    `<script>`;
  - POST `/damage-profile` preserves manual values in the redirect query;
  - visible copy avoids forbidden claim wording.
- [ ] Add GET and POST handlers in `web/server.py`.
- [ ] Add navigation link in `web/templates/base.html`.
- [ ] Create `web/templates/damage_profile.html`.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_web_server.py -q
```

## Task 4: Desktop Screen

- [ ] Add failing tests in `tests/test_desktop_app.py` proving:
  - main window includes `Damage Profile`;
  - screen shows non-empty estimate/status text;
  - desktop smoke includes `damage_profile_estimate: true`.
- [ ] Create `desktop/screens/damage_profile.py`.
- [ ] Add it to `desktop/main_window.py`.
- [ ] Add smoke summary field in `desktop/app.py`.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_desktop_app.py -q
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

## Task 5: Documentation, QA, And Commit

- [ ] Update `README.md` and `docs/qa-scenarios.md` with the manual Damage Profile route/screen and
  trust wording.
- [ ] Update `docs/work-log/player-toolkit-implementation.md` with Phase 8A decisions, TDD,
  reviewers, validation, Browser QA, and blockers.
- [ ] Run final validation:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

- [ ] Run Browser QA:
  - `/damage-profile`;
  - `/damage-profile?attacks=2&hit=4&wound=4&save=4&damage=2&wounds=2&models=3`;
  - a blocked invalid query such as `/damage-profile?attacks=0&hit=4&wound=4&save=4&damage=2&wounds=2&models=3`.
- [ ] Protected-path scan excludes generated/raw/PDF/credential artifacts and keeps `AGENTS.md`
  unstaged.
- [ ] Commit:

```powershell
git commit -m "Add manual damage estimate toolkit"
```
