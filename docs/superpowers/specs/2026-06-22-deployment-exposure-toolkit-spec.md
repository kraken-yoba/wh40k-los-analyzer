# Phase 7 Deployment Exposure Toolkit Spec

Date: 2026-06-22

## Roadmap Anchor

Phase 7 is the Early Safe Exposure And Deployment MVP. In this spec, user-facing
wording uses "deployment exposure" and "not exposed under selected assumptions" rather than
presenting "safe" as a tactical truth:

- Exposure overlays from known or manual unit footprints.
- Safe staging regions by selected enemy threat/LOS assumptions.
- Deployment-zone safe-area checks using current map geometry.
- Manual unit placement diagnostics.

This phase comes after movement reach and threat range. It must not become damage math, mission
analytics, objective scoring, deployment optimization, or an AI recommendation engine.

## Considered Approaches

1. **Recommended: manual single-unit exposure/deployment diagnostic.**
   Compose existing LOS, threat, movement-base, deployment-zone, and rendering primitives. Inputs are
   manual centers/base sizes plus selected enemy threat/LOS assumptions. Output is an estimated
   diagnostic and overlays. This is implementable in one loop and directly satisfies Phase 7.
2. **Deferred: multi-unit placement candidate generator.**
   Generates ranked deployment locations. This is too close to Phase 10 and risks false precision
   without roster, coherency, objective, mission, and legal-placement backing.
3. **Deferred: mission-aware placement planner.**
   Uses primary/secondary scoring and objectives. This belongs after Phase 9 mission primitives.

## Product Behavior

Add a `Deployment Exposure` toolkit that answers:

- Is this manually placed friendly circular base inside the selected deployment zone under the
  current 2D estimate?
- Is the base fully on the board?
- Does the base overlap dense terrain features under the current dense-feature collision estimate?
- Is the placement exposed to the selected enemy LOS assumption?
- Is the placement inside the selected enemy threat projection?
- Which center positions in the selected deployment zone are not exposed under the selected enemy
  threat/LOS assumptions?

The tool does not rank positions, optimize placement, make matchup recommendations, or claim
source-backed placement compliance. It reports component diagnostics and overlays only.

## Inputs

- Map packet selector.
- Deployment zone id, default `attacker`.
- Friendly unit center X/Y and friendly base diameter.
- Enemy source center X/Y and enemy base diameter.
- Enemy move distance, threat range, and threat mode using the Phase 6 `THREAT_MODES`.
- Exposure mode:
  - `threat-only`: exposed if inside the enemy threat projection.
  - `los-only`: exposed if visible from the enemy source.
  - `threat-or-los`: exposed if inside either threat projection or LOS region.
  - `threat-and-los`: exposed only if inside both threat projection and LOS region.

## Geometry Semantics

- Battlefield coordinates remain inches, origin lower-left, standard board 44 x 60.
- Friendly and enemy models are manual circular bases.
- Enemy threat geometry reuses Phase 6 exact deterministic threat projection. Dice modes still use
  exact D6/2D6 math without rerolls or modifiers.
- Enemy LOS geometry reuses the current 2D visibility polygon from the enemy base.
- The placement base is a circular footprint. Diagnostics check the base footprint, not only the
  center point, for board, deployment-zone, and dense-feature overlap.
- Candidate staging regions are **base-center regions**. They are derived from:
  selected deployment-zone geometry, board base-center limits, dense-feature collision estimates,
  and the selected enemy risk region expanded by the friendly base radius.
- Dense-feature exclusion is an estimated 2D collision guard inherited from movement reach. It is
  not a full terrain traversal or legal placement rule.

## Readiness And Trust

- Valid manual inputs return `estimated`.
- Invalid inputs return `blocked` with no tactical overlays.
- No Phase 7 result returns `trusted`; source-backed placement compliance is not implemented.
- The output must warn that roster base sizes, coherency, terrain traversal, mission/deployment
  constraints, objective scoring, opponent intent, and optimization are not modeled.

## Architecture

- `domain/exposure.py`: typed payload, exposure mode, placement diagnostic records.
- `los/exposure.py`: focused geometry helpers for allowed center regions and risk composition.
- `application/deployment_exposure.py`: `ToolkitResult` builder, input hash, validation, geometry
  composition, assumptions/warnings.
- `application/services.py` and `application/view_models.py`: service entrypoints and state for web
  and desktop.
- `rendering/svg.py`: reuse existing `coverage_polygon`, `safe_regions`, `base_center`,
  `threat_regions`, and `threat_source_center` inputs. Add renderer changes only if tests prove the
  existing hooks cannot represent the new overlay.
- `web/server.py` and `web/templates/deployment_exposure.html`: server-rendered route and POST
  redirect; no custom JavaScript.
- `desktop/screens/deployment_exposure.py` and `desktop/main_window.py`: PySide6 screen using the
  shared service.

## Acceptance Criteria

- A toolkit result can be produced from manual inputs without roster/profile data.
- Valid results are `estimated`, include no recommendation language, and include explicit warnings.
- Invalid inputs are `blocked` and include no overlays.
- Placement diagnostics cover deployment-zone footprint, board footprint, dense-feature overlap,
  LOS exposure, threat exposure, threat probability at the friendly center, and final
  `not_exposed_under_assumptions`.
- Candidate staging center regions are clipped to the selected deployment zone, board-fit region,
  dense-feature collision estimate, and selected enemy risk assumptions.
- Web route `/deployment-exposure` renders controls, warnings, diagnostic summary, one SVG map, and
  no `<script>` tags; POST preserves manual values.
- Desktop app includes a `Deployment Exposure` screen and smoke-test proof that the SVG renders.
- Browser QA verifies the route renders overlays and warnings with no console warnings/errors.

## Explicit Non-Goals

- No source-backed placement-compliance plan.
- No candidate ranking or optimization.
- No roster-derived base sizes, unit counts, coherency, or keywords.
- No objective or mission scoring.
- No damage or survivability math.
- No stratagem, CP, detachment, faction, transport, reserve, Ingress, Scout, or Deep Strike logic.
- No official PDF/card image bundling or copied protected rules text.
- No custom frontend JavaScript.
