# Threat Range Toolkit Spec

Date: 2026-06-21

## Purpose

Phase 6 starts threat range tooling. The roadmap includes melee, shooting, reserves, transports,
actions, and probability-aware threat modes, but the first implementation slice must be small enough
to verify end to end before roster/profile/rules ingestion is complete.

This slice adds a rosterless, manual-input, single-model, circular-base, 2D threat projection
diagnostic. It estimates areas that can be affected by a selected range after optional movement and
surfaces exact dice distributions for common advance/charge-style reach budgets. It is not a
rules-legal threat solver and does not make matchup recommendations.

## Supported Inputs

- Map packet selector.
- Source center `x/y` in battlefield inches.
- Source base diameter.
- Movement distance in inches.
- Threat range in inches.
- Threat mode:
  - `raw-range`: threat range from the current source center.
  - `fixed-move-plus-range`: fixed movement envelope buffered by threat range.
  - `d6-move-plus-range`: fixed movement plus an exact D6 distribution and threat range.
  - `2d6-move-plus-range`: fixed movement plus an exact 2D6 distribution and threat range.
- Target point `x/y` for a single diagnostic probability readout.
- Measurement convention:
  - `source-base-edge-to-target-point`: the rendered projection means a target point lies within
    the estimated threat geometry after adding the source base radius to the reach budget. It does
    not include target base radius, hull geometry, engagement range, weapon range rules, or official
    range measurement semantics.

## Geometry Semantics

- Battlefield coordinates remain inches, origin lower-left, standard board 44 x 60.
- Source base is circular.
- Board clipping keeps source centers inside board bounds by base radius.
- Movement portions reuse Phase 5 movement envelope behavior:
  - 2D center movement.
  - Dense terrain features are diagnostic blockers for the movement component.
  - Coherency, other models, vertical movement, engagement range, and route finding around blockers
    are not modeled.
- Threat projection is a geometry estimate:
  - `raw-range` is `Point(source_center).buffer(source_base_radius + threat_range)` clipped to the
    board under the `source-base-edge-to-target-point` convention.
  - movement-capable modes use `movement_envelope(...).buffer(source_base_radius + threat_range)`
    clipped to the board.
  - The threat range buffer itself does not model LOS, cover, wall traversal, melee engagement
    details, target base sizes, or weapon-specific targeting restrictions.

## Distribution Semantics

The first slice surfaces exact reach-budget distributions and renders a probability raster overlay
for those distributions. It does not produce matchup analytics, opponent-score heatmaps, or
recommendation maps.

- `raw-range` and `fixed-move-plus-range` have one deterministic outcome with probability `1.0`.
- `d6-move-plus-range` outcomes are D6 totals `1..6`, each probability `1/6`.
- `2d6-move-plus-range` outcomes are 2D6 totals `2..12`, with standard two-dice probabilities.
- Each outcome records:
  - dice label.
  - total added inches.
  - total reach budget: movement distance + dice total + threat range + source base radius.
  - probability.

The rendered overlay is a probability raster for the selected mode. For deterministic modes, the
raster is binary. For dice modes, each outcome contributes its exact probability to the pixels in
that outcome's threat region. The distribution table states exactly which dice model produced the
probability bands.

The slice also exposes deterministic threshold helpers for the selected distribution:

- impossible thresholds return `0.0`.
- guaranteed thresholds return `1.0`.
- probability of reaching a farther threshold is monotonic non-increasing.
- no rerolls, modifiers, CP, stratagems, transport, reserve, action, engagement, or official
  legality rules are included.

The selected target point diagnostic reports the exact probability that the target point is inside
the estimated 2D threat geometry for one or more outcomes. It does not infer target eligibility or
target base contact.

## Toolkit Result

Add a `threat_range` toolkit result:

- Readiness: `estimated` for valid manual inputs.
- Readiness: `blocked` for non-finite or non-positive base diameter, non-finite or negative
  movement distance, non-finite or negative threat range, or non-finite source/target coordinates.
- Overlay kind: `threat_projection`.
- Warning language must include:
  - manual 2D geometry.
  - target-point measurement convention.
  - source-backed rules pending.
  - unsupported modifiers disabled.
  - no recommendations.

## UI Surface

Add thin web and desktop adapters:

- Web route/template: `/threat-range`.
- Desktop navigation item: `Threat Range`.
- Both call `WarhammerCompanionService` and render the shared SVG output.
- No custom frontend JavaScript.
- Visible wording must use "Estimated 2D threat projection" and must avoid "legal", "safe",
  "recommended", "optimal", "guaranteed", and "likely" wording for estimated results.

## Explicit Non-Goals

- No damage, survivability, target profiles, army list, roster import, or unit profile resolution.
- No source-backed stratagem, CP, modifier, reroll, transport, reserve, ingress, action, objective,
  target base, pile-in/consolidation, engagement range, or mission logic.
- No opponent-score recommendation map.
- No new official source extraction.
- No custom JavaScript.
- No generated data/raw official files/screenshots/logs/caches/credentials.

## Acceptance Criteria

- Geometry tests cover raw range, move-plus-range, dense terrain movement blocker carry-through, and
  invalid input blocking.
- Distribution tests cover fixed, D6, and 2D6 probabilities, threshold probabilities,
  impossible/guaranteed thresholds, monotonic reach probability, and total reach budgets.
- Toolkit tests cover readiness, no recommendation language, input hash identity, warnings, and no
  overlays on blocked results.
- Rendering tests prove a stable `threat-projection-image` raster and marker classes.
- Web tests prove the route controls, cautious copy, no scripts, and value preservation.
- Desktop tests prove smoke summary and screen pixmap rendering.
- Browser QA covers `/threat-range` and existing smoke routes with no console warnings/errors.
- Full static checks, pytest, packet validation, desktop smoke, protected-path scan, and atomic
  commit pass.
