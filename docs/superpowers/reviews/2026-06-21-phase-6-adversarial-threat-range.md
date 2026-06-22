# Phase 6 Adversarial Review - Threat Range Toolkit

Date: 2026-06-21

Reviewer: adversarial subagent `019eebfd-9276-7e90-993d-25e4fa5b855d`

## Prompt

Critique the proposed first Phase 6 slice: rosterless/manual threat range toolkit with raw range,
move-plus-range, and simple deterministic dice distribution for advance/charge reach, using current
2D movement geometry and dense terrain blockers, with thin web/desktop adapters and `estimated`
readiness.

## Outcome

Conditionally approved.

Accepted constraints:

- Keep valid outputs `estimated`; invalid or non-finite inputs are `blocked` with no tactical
  overlay.
- Dice probability is deterministic manual math only: D6 and 2D6, no rerolls, modifiers, CP,
  stratagems, transports, reserves, actions, engagement, or source-backed legality.
- Use and visibly label the `target-point` measurement convention. Do not call it Warhammer legal
  range.
- Dense terrain remains a source-pending 2D blocker hint and movement geometry is not pathfinding
  proof.
- UI copy must avoid legal, safe, recommended, optimal, guaranteed, and full-threat wording.
- Keep web/desktop thin over shared Python services; no custom frontend JavaScript.
- Do not mutate roster/profile, damage, mission/action, BoardState legality, or recommendation
  surfaces.

Accepted test requirements:

- Exact D6 and 2D6 distribution counts.
- Threshold probability tests for impossible, guaranteed, and monotonic reach probability.
- Geometry tests for raw range, move-plus-range, board clipping, dense blocker exclusion, and
  straight-corridor limitations.
- Toolkit hash coverage includes packet digest, points, bases, ranges, movement, dice profile, and
  measurement convention.
- Web/desktop/Browser/manual QA and standard static/test gates.
