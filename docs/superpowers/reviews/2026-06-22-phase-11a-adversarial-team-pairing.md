# Phase 11A Adversarial Review - Team Pairing Matrix

Date: 2026-06-22

## Scope

Adversarial design review for the Phase 11A Team Pairing Matrix before production code.

## Required Changes

The adversarial reviewer found these blockers:

- The matrix could be misread as pair-specific list-vs-list analysis. The design needed explicit
  labels-only/shared-scenario wording and tests proving repeated metrics are marked shared.
- The plan could allow copied source payloads. It needed explicit no `MapPacket`, no source payload,
  no geometry, no SVG/image, no source URL, no Google Sheet id/gid, and empty aggregate overlays.
- Forbidden visible terms conflicted with unsupported-data wording. User-facing copy needed to avoid
  exact forbidden phrases.
- Desktop parity was underspecified; the screen needed rows/columns, components, warnings/blockers,
  and ranges, not just a summary label.
- Label handling needed max length, duplicate handling, control normalization, escaping/plain-text
  rendering, and concrete tests.
- Valid Phase 11A output needed a forced `degraded` readiness.
- QA needed source-component blocker cases and no-network assertions.

## Resolution

The docs were patched to require:

- Labels-only cells with shared scenario metrics and no pair-specific computation.
- Sanitized scalar payloads only.
- Empty aggregate overlays.
- `unsupported-data` with `assessment="not_available"`, `readiness="degraded"`, and no source ids.
- Blocking label overflow, duplicate normalized labels, and overlong labels.
- Web escaping and desktop plain-text label rendering.
- Source blocker propagation.
- No network, public-sheet, PDF, source-refresh, or external-AI behavior on `/team-pairing`.

Focused adversarial re-review initially required stronger QA coverage for comma/newline splitting,
internal whitespace collapse, control-character removal, empty-fragment dropping, and order
preservation. The QA route was patched to include all of those cases and the final focused re-review
approved the design package.
