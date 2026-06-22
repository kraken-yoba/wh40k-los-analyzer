# Phase 8A Manual Damage Estimate Spec

Date: 2026-06-22

## Roadmap Anchor

Phase 8 is Damage And Survivability Profiles. The roadmap says true Phase 8 becomes roster-aware
after source/profile resolution exists. The current repository does not have profile resolution
authority yet: imported roster profiles are unresolved local evidence and must not become mechanics
authority.

This slice is therefore **Phase 8A Manual Damage Estimate**, not full roster-aware Phase 8
completion.

## Goal

Add a deterministic manual damage math toolkit for one manually supplied weapon profile into one
homogeneous target profile.

It answers:

- What are expected hits, wounds, unsaved wounds, and flat damage?
- What is the probability distribution for unsaved wounds?
- What is the probability distribution for models destroyed when damage does not spill between
  models?
- How many models are expected to be destroyed under the supplied manual assumptions?

## Exact Math Scope

Supported:

- Fixed integer attack count.
- Hit threshold, wound threshold, and manually supplied effective save threshold, each in `2+` to
  `6+` form.
- Flat non-negative damage per unsaved wound.
- Target wounds per model and target model count as finite positive integers.
- Exact binomial probability mass function for unsaved wounds.
- Models destroyed distribution with no damage spill between target models. Damage from separate
  unsaved wounds can accumulate on the active target model, but excess damage from an attack after
  that model is destroyed is discarded.
- Expected models destroyed from that distribution.

Blocked/unsupported:

- Zero, negative, non-integer, or non-finite attack count.
- Thresholds outside `2+` to `6+`.
- Target wounds/model less than or equal to zero.
- Non-integer or non-finite target wounds/model.
- Target model count less than or equal to zero.
- Non-integer or non-finite target model count.
- Negative or non-finite flat damage.
- Random attacks, random damage, rerolls, modifiers, critical hits, lethal hits, sustained hits,
  devastating wounds, mortal wounds, Feel No Pain, damage reduction, AP, cover, invulnerable rule
  selection, anti, twin-linked, torrent, blast, stratagems, faction/detachment rules, leader/bodyguard
  behavior, allocation quirks, mission-critical warnings, target priority, unit-vs-unit matrices,
  and roster-derived profile resolution.

Save input is an **effective save target supplied by the user after all unmodeled AP/cover/invulnerable
choices**. The app does not calculate AP, cover, or invulnerable save selection in this slice.

## Readiness And Trust

- Valid manual inputs return `estimated`.
- Invalid or unsupported inputs return `blocked` and include no tactical overlays.
- No result returns `trusted`.
- Results must not use `legal`, `optimal`, `recommended`, `likely`, `target priority`, `bad target`,
  or positive `official`/`profile-resolved` claim wording.
- Warnings must explicitly state: manual estimate, not roster-derived, not official/profile-resolved,
  effective save supplied by user, unsupported effects omitted, and no source-backed rules/list claim.

## Architecture

- `domain/damage.py`: typed input/payload rows and summary records.
- `math/damage.py` or `application/damage_math.py`: pure exact D6/binomial helpers. The
  implementation must be independent of web/desktop.
- `application/damage_profile.py`: `ToolkitResult[DamageEstimatePayload]` builder, input hash,
  validation, assumptions, warnings, and block reasons.
- `application/services.py` and `application/view_models.py`: service/state methods for web and
  desktop.
- `web/server.py` and `web/templates/damage_profile.html`: server-rendered route and POST redirect;
  no custom JavaScript.
- `desktop/screens/damage_profile.py` and `desktop/main_window.py`: thin PySide6 screen over the
  shared service.

## Product Surface

Web route: `/damage-profile`.

Desktop screen: `Damage Profile`.

Primary visible fields:

- Attacks.
- Hit target.
- Wound target.
- Effective save target.
- Damage per unsaved wound.
- Target wounds per model.
- Target model count.

Primary output:

- Expected hits.
- Expected wounds.
- Expected unsaved wounds.
- Expected damage.
- Expected models destroyed.
- Probability of destroying at least one model.
- Unsaved-wound and model-destroyed distributions.
- Trust/unsupported-effect warnings.

## Protected Data Guardrails

- Tests use synthetic manual numbers only.
- Do not commit real roster/profile/rule text, official datasheet data, screenshots, generated
  reports, or protected source text.
- Do not read roster snapshot profiles as mechanics authority in this slice.

## Acceptance Criteria

- Valid manual inputs produce an `estimated` `ToolkitResult` with deterministic EV and distributions.
- Invalid inputs block with explicit reason ids and no overlays.
- Input hash changes when any manual input changes.
- Warning text includes manual-estimate trust boundaries and avoids forbidden claim wording.
- Web route renders controls, warnings, results, distributions, and no `<script>` tags.
- POST preserves manual values in the redirect query.
- Desktop screen renders and smoke summary includes `damage_profile_estimate: true`.
- Standard validation and Browser QA pass.
