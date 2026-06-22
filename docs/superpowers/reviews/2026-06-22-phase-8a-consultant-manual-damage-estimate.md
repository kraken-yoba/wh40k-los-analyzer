# Phase 8A Consultant Review - Manual Damage Estimate

Date: 2026-06-22

## Verdict

APPROVED with scope wording changes.

## Notes

The consultant agreed Phase 8A is the right first slice if it is explicitly framed as a manual
estimated damage math toolkit, not true roster-aware Phase 8 completion.

Accepted recommendations:

- Use manual inputs only.
- Add typed domain records and a `ToolkitResult` builder.
- Include expected hits, wounds, failed saves, damage, expected models destroyed, and useful
  survivability/kill distributions.
- Keep readiness `estimated` for valid manual inputs and `blocked` for invalid inputs.
- Never return `trusted`.
- Defer roster/profile integration, AP/cover/modifiers, rerolls, core abilities, Feel No Pain,
  damage reduction, spillover quirks, leader/bodyguard behavior, weapon keywords, and official
  ability authority.

Trust wording should say the result is manual, not roster-derived, not official/profile-resolved,
uses user-entered effective save, and omits unsupported effects.

## Re-Review

The corrected Phase 8A spec, plan, and QA pathway were rechecked after narrowing the slice and
adding explicit invalid-input coverage. Consultant verdict: APPROVED.

## Implementation Review

The implementation matched the approved manual-only scope with typed manual inputs, exact
D6/binomial math, estimated/blocked readiness, no overlays/source refs, no roster/profile authority,
and cautious effective-save/unsupported-effects wording.

Implementation review verdict: APPROVED.
