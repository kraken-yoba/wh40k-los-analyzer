# Phase 7.5 Exposure Mode Housekeeping Spec

Date: 2026-06-22

## Roadmap Anchor

Phase 7.5 is a behavior-preserving housekeeping slice after Phase 7 Deployment Exposure and before
Phase 8 Damage And Survivability Profiles.

Phase 7 introduced exposure modes in both the application result builder and the service rendering
adapter. The same "does this mode include LOS?" and "does this mode include threat?" semantics are
currently duplicated. That duplication is a small but real code smell before later phases start
depending on exposure semantics.

## Goal

Centralize exposure-mode predicate semantics in `domain/exposure.py` and update current callers to
use the shared helpers.

## Scope

Allowed changes:

- Add typed helpers to `src/warhammer_companion/domain/exposure.py`:
  - `exposure_mode_includes_los(exposure_mode: ExposureMode) -> bool`
  - `exposure_mode_includes_threat(exposure_mode: ExposureMode) -> bool`
- Add direct unit coverage for all four supported exposure modes.
- Add service/rendering coverage for all four modes so LOS and threat overlays cannot be swapped or
  accidentally rendered for the wrong mode.
- Add a direct unsupported-mode regression proving invalid raw exposure modes still block with
  `invalid-exposure-mode` and no overlays.
- Update `application/deployment_exposure.py` and `application/services.py` to use the shared
  helpers.
- Update work-log and review docs.

Out of scope:

- No route, template, desktop layout, SVG renderer, geometry, source-trust, roster, damage,
  survivability, mission, analytics, or AI changes.
- No change to `EXPOSURE_MODES` values or coercion behavior.
- No new user-facing wording.
- No official source ingestion or generated data changes.

## Behavior Preservation Contract

The helpers must preserve these semantics:

| Mode | Includes LOS | Includes threat |
| --- | --- | --- |
| `threat-only` | no | yes |
| `los-only` | yes | no |
| `threat-or-los` | yes | yes |
| `threat-and-los` | yes | yes |

These helpers mean "include this component diagnostic/overlay." They do not define selected exposure
risk composition. `threat-and-los` includes both component overlays, while the selected risk region
remains the intersection handled by `los/exposure.py`.

Invalid exposure modes are still handled by existing builder validation and
`coerce_exposure_mode(...)`; this housekeeping slice must not make unsupported modes valid.

## QA Expectations

- Direct unit tests prove the helper matrix above.
- Deployment Exposure toolkit tests still pass, including curved deployment-zone and all-four-mode
  regressions from Phase 7.
- Unsupported raw exposure modes still return `blocked`, include `invalid-exposure-mode`, and include
  no overlays.
- Service rendering tests prove `coverage-image` appears iff the mode includes LOS and
  `threat-projection-image` appears iff the mode includes threat.
- Service/rendering/web/desktop tests still pass for the Phase 7 route/screen.
- Static checks and full pytest pass.
- Browser QA verifies `/deployment-exposure`, the page 9 regression route, and the page 52 regression
  route still render the expected overlays with no scripts, no forbidden visible claim wording, and
  no console warnings/errors.
- Protected-path scan keeps generated data, raw official sources, binaries, credentials, and
  `AGENTS.md` out of staging.
