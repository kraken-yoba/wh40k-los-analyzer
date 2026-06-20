# Phase 3 Consultant Review - Base Size And Terrain Semantics

Date: 2026-06-20

## Review Scope

Consultants evaluate the Phase 3 spec, plan, QA pathway, and domain contract for base-size,
model-frame, manual-footprint, and terrain semantics records.

## Architecture Consultant

Reviewer: `019ee544-8b5b-77c3-aaf4-e0138bf467b4`

Status: completed.

Requested focus:

- Domain placement and module boundaries.
- Compatibility with future movement/threat APIs.
- Preservation of current LOS behavior.
- Source refs, readiness, warnings, and manual fallback semantics.

## Source-Trust And QA Consultant

Reviewer: `019ee547-0b62-73a2-98bb-5c5701762bb7`

Status: completed.

Requested focus:

- Unknown base and unknown terrain trait blocking behavior.
- Manual fallback readiness.
- Incompatible source pack and vertical/height assumptions.
- Protected content and raw-source non-redistribution.
- Autonomous QA executability.

## Triage

- Accepted: make Phase 3 a contracts-and-adapters slice, not a solver or UI slice.
- Accepted: split base-size, terrain-semantics, and shared readiness primitives into focused domain
  modules, with thin application builders returning `ToolkitResult`.
- Accepted: keep `MapPacket` as layout geometry only; terrain semantics are keyed by packet ID,
  packet digest, element kind, and element ID.
- Accepted: manual base/frame input is `estimated`; source refs and manual provenance do not make
  it trusted.
- Accepted: invalid, missing, unknown, stale, or incompatible base/terrain/source data blocks
  legal/safe trusted claims.
- Accepted: record manual provenance fields: local operator marker, timestamp, reason, reviewed
  fields, override history, units, field-level source refs, freshness, compatibility, validation
  records, warnings, and assumptions.
- Accepted: preserve current LOS, `MapPacket.blockers()`, rendering, web, and desktop behavior.
- Accepted: add tests for input-hash changes when manual base size, packet digest, or source-pack
  version changes.
- Accepted: update QA to scan for protected raw source artifacts and skip Browser/Computer Use only
  while the diff remains domain/application/tests/docs with no UI/runtime behavior changes.
