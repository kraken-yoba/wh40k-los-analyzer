# Phase 11A Team Pairing Matrix Spec

Date: 2026-06-22

## Roadmap Anchor

Phase 11 is Matchup Analytics For Team Pairing. The roadmap asks for captain-facing pairing
scenario comparison after deterministic toolkit primitives exist. It also explicitly blocks
game-theoretic captain automation, calibrated expected tournament points, confidence bands, and
recommended pairings until a later `PairingModelSpec` defines priors, weights, calibration data,
sample sizes, validation error, and uncertainty propagation.

This first Phase 11 slice creates a deterministic pairing-matrix dossier. It is not a pairing
optimizer, win-probability model, tournament-point model, or roster-aware rules engine.

## Goal

Let a captain enter manual friendly and opponent list labels and inspect a row/column matrix of
component scorecards derived from existing deterministic tool outputs. Each cell must show what was
actually checked, what is source-pending, and what is unavailable because roster-aware mission and
calibration infrastructure does not exist yet.

Phase 11A cells are labels-only dossier cells. The same shared scenario-level source results are
repeated across row/column intersections until roster-specific and opponent-specific source results
exist. No cell performs list-specific matchup computation in this slice.

## Supported In This Slice

- Manual friendly and opponent list labels.
- Label normalization:
  - split on commas and newlines;
  - strip leading/trailing whitespace;
  - collapse internal whitespace to one space;
  - remove non-printing control characters other than separators;
  - preserve input order;
  - block more than eight labels per side with `too-many-friendly-lists` or
    `too-many-opponent-lists`;
  - block labels longer than 80 characters with `friendly-list-label-too-long` or
    `opponent-list-label-too-long`;
  - block duplicate normalized labels within a side with `duplicate-friendly-list-label` or
    `duplicate-opponent-list-label`.
- One selected terrain packet/layout from the existing packet selector.
- A single deterministic scenario record that captures:
  - selected packet id and label;
  - mission pack result id and readiness;
  - both going-first and going-second deployment scorecard assumptions;
  - labels-only list inputs.
- Pairing matrix rows and columns from the manual labels.
- Pairing cells with component cards:
  - `damage-output`: raw manual damage profile metrics from the existing Damage Profile toolkit.
  - `mission-context`: Mission Pack skeleton readiness and source-pending warnings.
  - `deployment-staging`: current Deployment Scorecard diagnostics for going-first and
    going-second assumptions.
  - `unsupported-data`: explicit unavailable-data card for roster-aware mission scoring,
    objective/action reliability, mobility/screening gaps, matchup weighting, selection guidance,
    and tournament-point modelling.
- Scenario metric ranges over deterministic values only:
  - expected damage from the manual damage profile;
  - expected models destroyed from the manual damage profile;
  - threat probability at the selected deployment point across the included turn-order
    assumptions.
- Web route `/team-pairing`.
- Desktop screen `Team Pairing`.

## Component Contract

`PairingComponentCard` records must contain:

- `component_id`: one of `damage-output`, `mission-context`, `deployment-staging`,
  `unsupported-data`.
- `label`: user-facing component name.
- `assessment`: one of `checked`, `warning`, `blocked`, `not_available`.
- `readiness`: `ToolkitReadiness` only; never `not_available`.
- `detail`: deterministic explanation of the component.
- `source_tool_id`, `source_result_id`, and `source_input_hash` when a deterministic source result
  exists.
- `metrics`: zero or more raw deterministic metrics.
- `warnings` and `block_reasons`: copied or summarized from source toolkit results.

The `unsupported-data` card must use `assessment="not_available"`, `readiness="degraded"`, and no
source result id/input hash because it describes missing infrastructure rather than a source
toolkit result.

Pairing cells must not expose aggregate scores, ranks, grades, picks, best/worst labels, matchup
ratings, calibrated ranges, confidence bands, expected tournament points, win probabilities, or
actionable pairing selections.

Every metric copied into multiple cells must be labeled as a shared scenario metric. Labels-only
cells must not present shared damage, deployment, or mission metrics as pair-specific findings.

## Readiness Semantics

- Invalid or empty friendly/opponent labels return `blocked` with no matrix cells.
- A cell is `blocked` only when no usable deterministic component exists for that cell.
- A cell is `degraded` when at least one deterministic component exists but unsupported-data cards
  or source-pending components are present.
- A cell is `estimated` only when every included component is estimated or better and no
  `not_available` component is present.
- The Phase 11A result must be `degraded` for valid inputs, even if future source components become
  `trusted`, because roster-aware mission scoring, objective/action reliability, mobility/screening
  gaps, and pairing model calibration are not implemented.
- No Phase 11A result may be `trusted`.

If one source component is blocked but another deterministic component remains usable, the cell is
`degraded` and carries the blocked component card. Cells are `blocked` only when no usable
deterministic component remains.

## Explicitly Out Of Scope

- Expected tournament points.
- Win probability.
- Confidence bands or calibrated uncertainty.
- Recommended, selected, or optimized pairings.
- Game-theoretic captain automation.
- Roster-derived list strength, list legality, official points, faction/detachment interactions, or
  target priority.
- Mission scoring formulas, secondary/action parsing, objective control math, and action
  reliability.
- Google Sheet mission-card ingestion, image/OCR extraction, screenshots, exports, or copied card
  text.
- External AI calls.

## Forbidden User-Facing Claims

The `/team-pairing` route and desktop `Team Pairing` screen must not display these phrases as
authority claims:

- `legal`
- `safe`
- `optimal`
- `recommended`
- `likely`
- `guaranteed`
- `preferred`
- `pairing score`
- `expected points`
- `win probability`
- `favored`
- `calibrated`

The word `pairing` is allowed because this phase is explicitly about team pairing. The forbidden
claim is a score, pick, optimization, prediction, or calibration claim.

Rendered user-facing unsupported-data copy must avoid the forbidden exact phrases. Use wording such
as `matchup weighting unavailable`, `selection guidance unavailable`, and `tournament-point model
unavailable`.

## Architecture

- `domain/matchups.py`: typed manual list entries, scenario records, component cards, metric
  records, scenario ranges, matrix cells, and payload records.
- `application/matchup_matrix.py`: deterministic builder that accepts existing toolkit results and
  produces a `ToolkitResult[PairingMatrixPayload]`.
- `application/services.py` and `application/view_models.py`: shared service/state methods.
- `web/server.py` and `web/templates/team_pairing.html`: server-rendered route and form; no custom
  JavaScript.
- `desktop/screens/team_pairing.py` and `desktop/main_window.py`: thin PySide6 adapter.

## Source And Privacy Guardrails

- Do not fetch the public Google Sheet.
- Do not fetch official PDFs or mutable external sources in this slice.
- Do not store source images, mission-card text, roster archives, screenshots, generated exports,
  raw PDFs, processed packets, databases, credentials, or Codex/OpenAI state.
- The aggregate `ToolkitResult` must have `overlays=()`.
- `PairingMatrixPayload` must not retain `MapPacket`, source toolkit payload objects, Shapely
  geometry, SVG, images, source URLs, Google Sheet id/gid, mission-card text, official rules text,
  or generated/exported source payloads.
- Only export/display labels, selected packet id/label, result ids, input hashes, readiness, source
  ref ids, warning text, blocker ids/details, and raw deterministic metrics from already-local
  toolkit outputs.
- `/team-pairing` must not perform network access, public sheet fetches, PDF fetches, external AI
  calls, or source refreshes.

## Acceptance Criteria

- Manual friendly/opponent labels produce a matrix with one cell per row/column pair.
- Valid default inputs return a `degraded` matrix with deterministic component cards and explicit
  unsupported-data cards.
- Empty manual labels return `blocked` with user-facing blocker text and no cells.
- Unsafe labels are escaped on web and rendered as plain text on desktop; label overflow, duplicate
  labels, and overlong labels are blocked.
- Scenario ranges are deterministic min/max values from included component metrics, not confidence
  intervals.
- Web and desktop surfaces show the matrix/components and cautious warnings.
- Browser/manual QA verifies `/team-pairing`, zero custom JavaScript, no traceback/internal-error
  text, no forbidden user-facing authority claims, valid matrix rendering, and blocked label
  behavior.
- Standard Python verification, desktop smoke, consultant review, adversarial review, protected-path
  scan, and atomic commit all pass.
