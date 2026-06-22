# Phase 6.5 Consultant Review - Threat Housekeeping

Date: 2026-06-22

## Verdict

APPROVED.

## Notes

- Scope is appropriately small for a housekeeping slice: movement geometry helper extraction,
  threat validation reuse, focused tests, docs, and work-log updates only.
- `base_center_region(packet, base_radius)` belongs in `los/movement.py` because it is reusable
  board/base geometry rather than application policy.
- `application/threat_range.py` should remain the layer that translates geometry into
  `BlockReason` records.
- QA path is adequate for this refactor: direct helper tests, existing movement/threat tests,
  static checks, full pytest, desktop smoke, and protected-path scan.

## Follow-Up Applied

The consultant asked for a direct negative-radius guard test. Phase 6.5 adds
`test_base_center_region_rejects_negative_base_radius`.
