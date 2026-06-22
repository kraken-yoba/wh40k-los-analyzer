# Phase 10A Consultant Review - Manual Deployment Scorecard

Date: 2026-06-22

## Initial Verdict

Required changes.

The scope is sound: a narrow manual scorecard, reuse of deployment exposure and Mission Pack
builders, explicit turn order, and no claim to solve legal placement.

Blocked on QA reproducibility and coverage:

- Add exact valid and invalid `/deployment-scorecard?...` URLs.
- Sync forbidden-word checks across spec, plan, and QA.
- Add page 9/page 52 regression coverage or document why this slice does not alter geometry or
  rendering enough to require new coverage.
- Add desktop verification beyond the smoke key for the user-visible PySide6 screen.

## Resolution

Patched spec, plan, and QA with concrete valid/invalid routes, canonical forbidden visible-text
claims, page 9/page 52 reuse rationale, and a desktop test-harness verification step.
