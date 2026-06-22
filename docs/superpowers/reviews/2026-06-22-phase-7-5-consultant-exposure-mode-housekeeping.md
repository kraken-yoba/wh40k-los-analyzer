# Phase 7.5 Consultant Review - Exposure Mode Housekeeping

Date: 2026-06-22

## Verdict

APPROVED.

## Notes

The consultant agreed this is an appropriate Phase 7.5 housekeeping slice. `domain/exposure.py`
already owns `ExposureMode`, `EXPOSURE_MODES`, `DeploymentExposurePayload`, and
`coerce_exposure_mode(...)`, so it should also own exposure-mode component predicate semantics.

Accepted recommendations:

- Keep the helpers plainly named.
- Keep callers passing already-coerced `ExposureMode` values where possible.
- Add direct truth-table coverage for all four supported modes.
- Keep the existing selected-risk integration test because it proves behavior beyond predicate
  truth values.
- Do not broaden the slice into Phase 8, UI changes, renderer changes, or exposure-risk geometry.

The consultant noted `AGENTS.md` is untracked and must remain unstaged unless intentionally added.
