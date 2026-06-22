# Phase 9.5 Mission Source Metadata Housekeeping Spec

Date: 2026-06-22

## Goal

Run a behavior-preserving cleanup after the Phase 9 Mission Pack skeleton by centralizing mission
source refs and warning text inside the mission-pack application builder.

## Problem

Phase 9 records the public Google Sheet candidate in two places:

- the `MissionSourceRef` object;
- the input-hash payload.

Both must stay identical for source-trust correctness. Keeping duplicate literal metadata creates
avoidable drift risk before later mission-ingestion phases add more source records.

## Supported In This Slice

- Add a small internal helper or constants in `application/mission_pack.py` so:
  - source refs are built through one canonical path;
  - the input hash reads public-sheet metadata from the same source-ref object;
  - toolkit warnings and pack warnings share canonical text.
- Add focused guardrail tests for the canonical source-ref helper/hash behavior.
- Preserve the public `build_mission_pack_toolkit_result(...)` signature. Any test injection must
  target private helpers only.
- Preserve all public behavior from Phase 9:
  - toolkit result id/readiness semantics;
  - source ids, labels, URL, sheet id, gid, `not_fetched`, `untrusted_candidate`, and
    `content_hash=None`;
  - mission ids and anchors;
  - web route `/mission-pack`;
  - desktop screen `Mission Pack`.

## Explicitly Out Of Scope

- Fetching, parsing, or validating the public Google Sheet.
- Storing sheet exports, card images, screenshots, full card text, or OCR output.
- Adding primary or secondary mission scoring mechanics.
- Adding objective control, action, denial, flip, or team-pairing analytics.
- Moving public source metadata into the generic domain model module.

## Acceptance Criteria

- There is one canonical in-code source for public-sheet mission source metadata.
- The mission-pack input hash uses the canonical public-sheet source ref, not independent duplicate
  literals.
- The public `build_mission_pack_toolkit_result(...)` signature is unchanged.
- Existing Phase 9 tests keep passing without behavior changes.
- New guardrail tests prove toolkit source refs and hash identity respond consistently to source
  metadata.
- Browser QA confirms `/mission-pack` still renders the same source-safe summary.
