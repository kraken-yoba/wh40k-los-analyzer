# Phase 10A Adversarial Review - Manual Deployment Scorecard

Date: 2026-06-22

## Initial Verdict

Required changes.

Blocking issues:

- Turn order is a new Phase 10A input and needs a first-class invalid-input path:
  `invalid-turn-order`, `blocked`, no overlays, and user-facing block reasons.
- Component semantics were underspecified and could drift into aggregate scoring or placement
  preference. The exact component ids, assessment values, data sources, and banned aggregate/rank
  output must be explicit.
- Forbidden wording checks were inconsistent and need one visible-text-only list.
- Browser QA must submit the form, verify redirect/value preservation, and prove invalid base and
  invalid turn-order routes render blocked state with no tactical overlay.
- Add an explicit assertion that no public sheet fetch, mission-card/rules text, copied source
  images, or Google Sheet exports are introduced.

## Resolution

Patched spec, plan, and QA with typed turn-order validation, exact component contract, canonical
visible-text claim checks, form-submission Browser QA, blocked-output overlay checks, and
metadata-only mission-source acceptance.

## Re-Review Verdict

Required changes.

- Plan readiness logic still implied `estimated` unless exposure blocked; this omitted invalid
  turn order.
- Manual input units were not explicit enough for coordinates, base diameters, move, and threat
  fields.
- Spec needed to state all blocked scorecard outputs produce no tactical overlays, not just invalid
  turn order.
- Browser QA needed a precise DOM assertion for blocked tactical overlays.

## Re-Review Resolution

Patched spec, plan, and QA with inch-unit field definitions, `estimated` only when turn order and
deployment exposure are valid, no tactical overlays for every blocked scorecard result, valid QA
URLs using 1.57 inch base diameters and supported mode names, and the Browser assertion
`document.querySelectorAll('[data-toolkit-overlay]').length === 0`.
