# Phase 0 Implementation Readiness Design

Date: 2026-06-19

## Status

Draft Phase 0 design for preparing implementation of the player-toolkit roadmap.

Parent roadmap: `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`

## Goal

Prepare the repository and workflow for Phase 1 without changing app behavior.

Phase 0 exists because the roadmap is broad, source-sensitive, and review-heavy. Before implementing Phase 1, the project needs a repeatable phase protocol: each phase gets a fine-grain spec, implementation plan, autonomous QA pathway, work-log entry, consultant review, adversarial review, verification evidence, and atomic commits.

## Non-Goals

Phase 0 must not:

- Implement `RulesPack`, `SourcePackRegistry`, source ingestion, roster parsing, or toolkit runtime code.
- Add custom frontend JavaScript, TypeScript, or a new UI framework.
- Bundle, commit, or regenerate official Games Workshop PDFs or protected source-derived data.
- Change battlefield coordinates, board size, existing LOS behavior, existing map packets, or web/desktop runtime behavior.
- Alter Codex/OpenAI credential handling.
- Replace the current Python service-layer architecture.

## Required Artifacts

Phase 0 creates the following durable artifacts:

- `docs/superpowers/specs/2026-06-19-phase-0-implementation-readiness-design.md`: this design.
- `docs/superpowers/plans/2026-06-19-phase-0-implementation-readiness.md`: exact implementation plan for Phase 0.
- `docs/superpowers/qa/2026-06-19-phase-0-implementation-readiness-qa.md`: autonomous QA pathway and reusable phase QA template.
- `docs/superpowers/reviews/2026-06-19-phase-0-consultant-readiness.md`: consultant review findings, triage, and final status.
- `docs/superpowers/reviews/2026-06-19-phase-0-adversarial-readiness.md`: adversarial review findings, triage, and final status.
- `docs/work-log/player-toolkit-implementation.md`: factual work log for the multi-phase player-toolkit program.
- `docs/qa-scenarios.md`: broader app QA contract updated with roadmap phase QA expectations.

These files are documentation scaffolding. They do not alter product behavior.

## Phase Execution Protocol

Every numbered phase, including `.5` housekeeping phases, must use this protocol:

1. Start a goal loop with the full phase objective.
2. Inspect current repo state, `AGENTS.md`, the parent roadmap, prior phase work logs, and relevant code.
3. Produce or update a phase-specific design spec.
4. Produce or update a phase-specific implementation plan under `docs/superpowers/plans/`.
5. Produce or update a phase-specific QA pathway under `docs/superpowers/qa/`.
6. Dispatch consultant subagents for research, architecture fit, and gap analysis.
7. Dispatch adversarial review subagents for false precision, security/IP/source trust, test adequacy, and scope creep.
8. Triage reviewer findings into accepted fixes, documented design decisions, or explicit reasoned pushback.
9. Implement with TDD for behavior changes.
10. Run the phase QA pathway, including browser/computer-use checks when UI/runtime behavior exists.
11. Update `docs/work-log/player-toolkit-implementation.md` with decisions, verification, and blockers.
12. Commit atomic checkpoints.
13. Mark the phase goal complete only after current evidence proves the phase objective and all review gates passed.

## Housekeeping Protocol

Between major phases, run `.5` housekeeping goal loops when one or more of these are true:

- Recent implementation created duplication, oversized files, awkward naming, or unclear service boundaries.
- Reviewers identify behavior-preserving cleanup that would reduce risk before the next phase.
- Verification reveals slow, flaky, or hard-to-run checks.
- Docs, plans, or QA pathways drift from implemented behavior.

Housekeeping phases must be behavior preserving unless the user explicitly approves a behavior change. They still require specs, plans, QA pathways, consultant review, adversarial review, and atomic commits.

## Design Decisions

### Decision 1: Phase 0 is documentation scaffolding only

Reasoning: The parent roadmap already says implementation should not begin until the first fine-grain spec is reviewed and approved. Creating runtime code in Phase 0 would skip that gate. Phase 0 prepares the gate rather than implementing Phase 1.

### Decision 2: QA pathways live under `docs/superpowers/qa/`

Reasoning: Existing Superpowers plans live under `docs/superpowers/plans/` and specs under `docs/superpowers/specs/`. A sibling `qa/` directory keeps autonomous QA instructions close to specs and plans without overloading `docs/qa-scenarios.md`, which is the broader app regression contract.

### Decision 3: Work logging gets one program-level file

Reasoning: Existing work logs are organized by workstream (`official-ingestion.md`, `desktop-app.md`). The player-toolkit roadmap is a long program with many phases, so `docs/work-log/player-toolkit-implementation.md` becomes the factual ledger for phase decisions, verification, and review outcomes.

### Decision 4: Browser/computer-use QA is required only when runtime behavior exists

Reasoning: Phase 0 is docs-only, so browser QA cannot prove product behavior. Later phases that add UI or runtime behavior must include Browser and, when relevant, Computer Use checks in their QA pathways.

### Decision 5: Phase 1 spec creation belongs to the Phase 1 goal loop

Reasoning: The user requested one goal loop per phase. Phase 0 should make Phase 1 safe to start, but the detailed `SourcePackRegistry` and `RulesPack` spec must be created, reviewed, and approved inside the Phase 1 loop so its source facts are current.

### Decision 6: Review evidence is stored under `docs/superpowers/reviews/`

Reasoning: Work-log summaries are useful for chronology, but the approval gate needs a durable place for consultant and adversarial findings. Review files keep approvals inspectable without mixing them into the executable plan or QA script.

## Phase 0 Acceptance Criteria

Phase 0 is complete only when all of the following are true:

- The required artifacts exist at the paths listed above.
- The phase plan includes concrete, ordered tasks with commands and expected results.
- The QA pathway can be executed by a fresh subagent without relying on hidden conversation context.
- `docs/qa-scenarios.md` includes a roadmap phase QA section that points future phase agents at phase-specific QA pathways.
- Consultant review approves the scope and artifact set.
- Adversarial review approves the readiness gates and confirms no Phase 1 behavior was implemented prematurely.
- Local verification confirms no unresolved draft markers, no non-ASCII surprises, clean markdown diff checks, and no unintended production-code changes.
- The work log records Phase 0 decisions, review outcomes, verification, and remaining nonblocking notes.
- The Phase 0 changes are committed atomically.

## Handoff To Phase 1

Phase 1 should start with a new goal loop and a new fine-grain spec named:

`docs/superpowers/specs/YYYY-MM-DD-source-pack-registry-and-rulespack-current-spec.md`

Phase 1 must refresh current source facts before relying on MFM, download pages, rules articles, or source timestamps.
