# Phase 10A Manual Deployment Scorecard Spec

Date: 2026-06-22

## Roadmap Anchor

Phase 10 is Mission-Aware Deployment Toolkit. The roadmap asks for safe deployment overlays,
exposure-minimizing candidate regions, objective/action reach, screening gaps, transport staging,
and manual deployment edit/rescore while deferring full optimization and perfect legal placement.

This first Phase 10 slice creates a manual deployment staging scorecard. It is not a legal
deployment solver, not a mission-scoring engine, and not an optimization tool.

Canonical forbidden visible-text claims for this slice are: `legal`, `safe`, `optimal`,
`recommended`, `likely`, `guaranteed`, `preferred`, and `pairing`. Checks apply to user-visible
text, not implementation-only CSS class names or SVG ids inherited from earlier renderers.

## Goal

Let a player enter one manual friendly footprint and one enemy threat/LOS source, then receive an
estimated deployment scorecard that combines existing deployment exposure diagnostics with explicit
going-first/going-second and mission-readiness warnings.

All battlefield coordinates, base diameters, move distances, and threat ranges are measured in
inches. Web query/form field names use those inch values directly:

- `friendly_x`, `friendly_y`, `enemy_x`, `enemy_y`: center coordinates in battlefield inches.
- `friendly_base`, `enemy_base`: circular base diameter in inches, not millimetres.
- `enemy_move`, `enemy_threat`: movement and threat distances in inches.

## Supported In This Slice

- Typed scorecard records for:
  - selected packet/deployment zone;
  - friendly footprint center/base;
  - enemy threat source and selected exposure mode;
  - going-first/going-second assumption;
  - component diagnostics and caution flags.
- Reuse existing `deployment_exposure_toolkit_result(...)` for geometry, threat, LOS, and placement
  diagnostics.
- Include the current Mission Pack skeleton readiness as context only.
- Produce a deterministic component scorecard:
  - deployment-zone fit;
  - selected threat/LOS exposure under current assumptions;
  - mission readiness limitation;
  - turn-order assumption limitation.
- Validate `TurnOrderAssumption = Literal["going-first", "going-second"]`; unsupported values
  return `blocked`, include block reason `invalid-turn-order`, and produce no overlays.
- All blocked scorecard outputs, whether caused by turn order or reused deployment exposure input
  validation, produce no tactical overlays.
- Web route `/deployment-scorecard`.
- Desktop screen `Deployment Scorecard`.

## Scorecard Component Contract

Each component record has:

- `component_id`: one of `deployment-fit`, `selected-exposure`, `mission-readiness`,
  `turn-order-assumption`.
- `label`: concise user-facing component name.
- `assessment`: one of `checked`, `warning`, `blocked`.
- `detail`: deterministic text explaining the component.
- `source_ref_ids`: source/result ids used to derive the component.

Allowed derivations:

- `deployment-fit`: derived only from the deployment exposure payload and block reasons.
- `selected-exposure`: derived only from deployment exposure payload probability/blocked state.
- `mission-readiness`: summarizes the Mission Pack skeleton source-pending limitation only.
- `turn-order-assumption`: echoes the manual going-first/going-second assumption and limitation.

The builder must not emit aggregate scores, ranks, grades, best-placement labels, placement
recommendations, or captain-level matchup guidance.

## Explicitly Out Of Scope

- Full mixed-integer optimization.
- Legal deployment validation for complex 3D terrain, unit coherency, multiple models, or whole
  army placement.
- Objective/action reach, OC, flip/denial potential, and mission scoring formulas.
- Screening gaps against Deep Strike/Ingress.
- Transport staging lanes.
- Roster-derived unit footprint resolution.
- Any recommendation that a placement is legal, safe, optimal, recommended, likely, guaranteed,
  preferred, or useful for pairing decisions.

## Architecture

- `domain/deployment_scorecard.py`: scorecard payload and component records.
- `application/deployment_scorecard.py`: deterministic builder that wraps existing deployment
  exposure and mission-pack context.
- `application/services.py` and `application/view_models.py`: shared service/state methods.
- `web/server.py` and `web/templates/deployment_scorecard.html`: server-rendered route; no custom
  JavaScript.
- `desktop/screens/deployment_scorecard.py` and `desktop/main_window.py`: thin PySide6 adapter.

## Readiness And Trust

- Valid results are `estimated`.
- Invalid manual inputs are `blocked` through the reused deployment exposure result.
- The scorecard must not use the canonical forbidden visible-text claims.
- Mission context remains `estimated` and source-pending until mission mechanics are reviewed.
- Public-sheet mission context remains metadata-only: no sheet fetch, no mission-card/rules text,
  no copied source images, and no Google Sheet exports are created or committed.

## Acceptance Criteria

- The scorecard uses existing deployment exposure results instead of duplicating geometry logic.
- Outputs explain component tradeoffs and warnings.
- Going-first/going-second assumptions are explicit.
- Manual footprint mode works before roster placement exists.
- Web and desktop surfaces render the scorecard and cautious warnings.
- Browser QA verifies `/deployment-scorecard`, zero custom JavaScript, no traceback/internal-error
  text, and no forbidden recommendation wording.
- Page 9 and page 52 stay covered by the reused deployment exposure tests and app-wide smoke tests;
  this slice does not alter geometry, terrain, LOS, deployment-zone rendering, or mission-zone
  rendering code.
