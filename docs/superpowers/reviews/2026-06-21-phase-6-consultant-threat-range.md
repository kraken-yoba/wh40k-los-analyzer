# Phase 6 Consultant Review - Threat Range Toolkit

Date: 2026-06-21

Reviewer: consultant subagent `019eebfd-6a1e-7390-bf18-96e79d96a530`

## Prompt

Review the Phase 6 roadmap and current movement reach implementation. Recommend a minimal first
developmental slice for manual deterministic threat range tooling before roster/rules ingestion is
complete.

## Outcome

Approved with recommended scope adjustments.

Accepted recommendations:

- Name this first slice Phase 6A/manual threat probability bands.
- Keep the tool rosterless, manual-input, and `estimated` for valid inputs.
- Use neutral dice-mode names rather than legal Advance/Charge/Shooting labels.
- Reuse `movement_envelope(...)` for the movement component.
- Render exact probability bands by accumulating outcome probability per threat region, not Monte
  Carlo.
- Include a selected target-point probability diagnostic and distribution table.
- Add `/threat-range` and a desktop `Threat Range` screen only after service/result logic exists.
- Always list modeled mechanics exactly and surface unsupported mechanics as warnings/non-goals.
