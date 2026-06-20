# Phase 0.5 Housekeeping Formatting Design

Date: 2026-06-20

## Status

Draft housekeeping design for the first behavior-preserving cleanup slice after Phase 0.

Parent roadmap: `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`

Prior phase: `docs/superpowers/specs/2026-06-19-phase-0-implementation-readiness-design.md`

## Goal

Resolve the known Ruff formatting drift recorded during Phase 0 without changing product behavior.

Phase 0.5 exists to clear the immediate baseline issue before Phase 1 starts. The Phase 0 work log
recorded that `.\.venv\Scripts\python.exe -m ruff format --check src tests` would reformat
`src\warhammer_companion\los\geometry.py`. This slice applies only the formatter-owned change,
verifies behavior, records review evidence, and commits an atomic housekeeping checkpoint.

## Non-Goals

Phase 0.5 must not:

- Implement Phase 1 source, rules, roster, mission, or toolkit runtime behavior.
- Change LOS semantics, battlefield coordinates, board dimensions, terrain assumptions, map packets,
  web routes, desktop screens, packaging behavior, or generated data.
- Add JavaScript, TypeScript, a frontend framework, official PDFs, protected source-derived data, or
  credential/auth handling changes.
- Refactor `src\warhammer_companion\los\geometry.py` beyond the formatter output required by Ruff.

## Required Artifacts

- `docs/superpowers/specs/2026-06-20-phase-0-5-housekeeping-formatting-design.md`: this design.
- `docs/superpowers/plans/2026-06-20-phase-0-5-housekeeping-formatting.md`: implementation plan.
- `docs/superpowers/qa/2026-06-20-phase-0-5-housekeeping-formatting-qa.md`: autonomous QA pathway.
- `docs/superpowers/reviews/2026-06-20-phase-0-5-consultant-housekeeping.md`: consultant review record.
- `docs/superpowers/reviews/2026-06-20-phase-0-5-adversarial-housekeeping.md`: adversarial review record.
- `docs/work-log/player-toolkit-implementation.md`: Phase 0.5 work-log entry.
- `src/warhammer_companion/los/geometry.py`: Ruff formatter-only source change.

## Design Decisions

### Decision 1: This housekeeping slice is formatter-only

Reasoning: The only concrete baseline issue from Phase 0 was Ruff format drift in one LOS file.
Ruff owns the formatting output, so manual semantic edits would add unnecessary review risk before
Phase 1.

### Decision 2: No new tests are added

Reasoning: The source change is formatting-only. Existing LOS, rendering, web, desktop, packet, and
full test suites are the right proof that behavior did not change.

### Decision 3: Browser and Computer Use checks are not required

Reasoning: This slice changes only Python formatting and documentation. It does not change web,
desktop, packaged, or runtime behavior. The desktop smoke command remains useful as a regression
guard.

## Acceptance Criteria

Phase 0.5 is complete only when:

- The required artifacts exist.
- Ruff formatting has been applied only to `src\warhammer_companion\los\geometry.py`.
- The source diff is formatter-only.
- Consultant and adversarial reviewers approve the scope, QA pathway, and resulting diff.
- `ruff format --check src tests`, `ruff check .`, `mypy src`, `pytest`, packet validation, and
  desktop smoke verification pass or any unrelated environmental blocker is documented.
- `git diff --check` passes.
- `AGENTS.md` remains untracked and unstaged unless the user explicitly asks to stage it.
- The Phase 0.5 changes are committed atomically.

## Handoff To Phase 1

After Phase 0.5, Phase 1 can start its own goal loop with the source/rules foundation spec named:

`docs/superpowers/specs/YYYY-MM-DD-source-pack-registry-and-rulespack-current-spec.md`
