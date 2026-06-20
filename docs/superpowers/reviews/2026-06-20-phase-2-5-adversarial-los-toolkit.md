# Phase 2.5 Adversarial Review - LOS Toolkit Extraction

Date: 2026-06-20

## Scope

Adversarial review of the Phase 2.5 behavior-preserving LOS toolkit extraction.

## Findings

Initial adversarial review requested changes:

- Important: `tests/test_los_toolkit.py` did not pin the exact Phase 2 LOS toolkit contract. It
  derived the suffix from the produced hash and omitted checks for literal v0 hash payload format,
  full result/layer IDs, assumptions, warnings, overlay metadata, and overlay geometry identity.
- Minor: the Phase 2.5 spec contained non-ASCII mojibake in the word `facade`.

## Triage

Accepted and fixed:

- Tightened `tests/test_los_toolkit.py` to independently compute the expected
  `los-checker-toolkit/v0` input hash.
- Added exact assertions for `result_id`, `input_hash`, `layer_id`, assumption id/detail, warning
  ids/detail, overlay geometry identity, units, style token, label, and readiness.
- Replaced the spec text with ASCII `facade`.

## Re-Review Status

- 2026-06-20: re-review approved. The tightened test covers literal v0 hash payload format,
  exact result/layer IDs, assumption id/detail, warning IDs and detail, overlay metadata, overlay
  geometry identity, recommendation-language guard, and packet non-mutation. The extraction stays
  scoped to service thinning plus `application.los_toolkit`.

## Final Status

Approved.
