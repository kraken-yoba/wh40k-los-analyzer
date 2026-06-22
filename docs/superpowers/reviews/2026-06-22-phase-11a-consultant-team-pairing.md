# Phase 11A Consultant Review - Team Pairing Matrix

Date: 2026-06-22

## Scope

Consultant review for the first Phase 11 matchup analytics slice. The proposed implementation is a
labels-only Team Pairing Matrix dossier that aggregates existing deterministic toolkit outputs.

## Initial Recommendation

The consultant gap-analysis pass recommended a narrow `Pairing Matrix V0: deterministic component
dossier`:

- Use row/column manual list labels.
- Populate cells with component cards sourced from existing `ToolkitResult` objects.
- Treat damage profile, mission pack, and deployment scorecard as shared scenario components.
- Mark roster-aware mission scoring, objective/action reliability, mobility/screening gaps, matchup
  weighting, selection guidance, and tournament-point modelling as unavailable.
- Do not implement expected tournament points, win probability, confidence bands, best/worst labels,
  recommendations, or game-theoretic captain automation.

## Required Changes

The consultant design review approved the direction but required narrower semantics:

- Clarify that component `readiness` remains `ToolkitReadiness`; `not_available` is an assessment,
  not a readiness.
- Make `unsupported-data` use `assessment="not_available"` and `readiness="degraded"` with no
  source result fields.
- Avoid forbidden visible terms in unsupported-data copy.
- Block more than eight labels per side instead of silently truncating.
- Assert Team Pairing does not render source URLs, public sheet id/gid, mission-card text, raw
  official text, or source payloads.

## Resolution

The spec, plan, and QA pathway were patched:

- Valid Phase 11A outputs are forced to `degraded`; no Phase 11A result may be `trusted`.
- Label overflow blocks with side-specific blocker ids.
- User-facing copy uses `matchup weighting unavailable`, `selection guidance unavailable`, and
  `tournament-point model unavailable`.
- Source/privacy QA covers URL, sheet id/gid, payload, SVG/image, and no-network assertions.

The focused re-review approved the final design package after label-normalization QA was made
concrete.
