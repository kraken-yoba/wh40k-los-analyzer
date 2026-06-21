# Phase 4A Consultant Review - Roster Import Safety

Date: 2026-06-21

## Review Scope

Consultants evaluate Phase 4 decomposition, first safe implementation boundaries, file placement,
and QA coverage before roster/profile adapter implementation begins.

## Findings

Reviewer: `019ee97a-4ac5-7ca1-9a0e-2700a5bb0df2`

Status: approved Phase 4A direction.

- Phase 4 should be split into multiple fine-grain specs rather than one monolithic roster/profile
  implementation.
- First implementable sub-slice should be safe `.ros` and minimal `.rosz` import into
  `RosterImportRecord`/shallow `CanonicalArmy`.
- Profile resolution, BSData catalog import, MFM points, UI, persistence, BoardState placement, and
  movement/threat use should be deferred.
- Domain records belong under `domain`, hostile admission helpers under `ingestion`, and thin
  `ToolkitResult` builders under `application`.
- Tests should use synthetic fixtures only and prove archive/XML safety plus no protected data.

## Triage

- Accepted: split Phase 4 into Phase 4A import safety/source records, later canonical army
  enrichment, later profile resolution/points, later BoardState adapter, and later UI.
- Accepted: start with `.ros`/`.rosz` only.
- Accepted: no profile, points, UI, persistence, or downstream solver integration in Phase 4A.
- Accepted: place code in `domain.rosters`, `ingestion.roster_archives`,
  `ingestion.roster_xml`, and `application.roster_import`.

## Final Approval Gate

Final consultant approval requires:

- Phase 4A implementation stays inside the approved boundary.
- Synthetic tests prove safe import and malicious rejection.
- Standard verification and Browser route smoke are recorded before commit.

## Final Review

Reviewer: `019ee985-63f6-7d42-9933-1011bfa5b87a`

Status: changes required.

- P1: UTF-16 XML containing `DOCTYPE` and internal entities bypassed the raw byte safety scan.
- P1: deep roster XML could recurse until a `RecursionError` instead of returning a blocked
  result.
- P2: domain and ingestion modules imported the application-layer `BlockReason`.
- P3: `CanonicalArmy` did not carry source refs.

Triage:

- Accepted: reject non-UTF-8/BOM and NUL-containing XML bytes before scanning or parsing.
- Accepted: add depth enforcement before recursive selection extraction.
- Accepted: move roster block reasons into `domain.rosters` and adapt them in the application
  layer.
- Accepted: add `source_ref_ids` to `CanonicalArmy` and preserve them in the application builder.

## Final Re-Review

Reviewer: `019ee99a-5ac5-7181-b9db-e96ef20076f9`

Status: approved.

- Phase 4A stayed inside the approved boundary: no UI, persistence, profile/MFM/community import,
  damage/threat logic, overlays, or recommendation path.
- Source and canonical records are sufficient for later enrichment without claiming authority:
  raw IDs, names, source paths, costs-as-presented, source hashes, member metadata, quarantine
  status, and `CanonicalArmy.source_ref_ids`.
- Previous consultant blockers were closed: UTF-16/NUL XML is rejected, XML depth is gated before
  recursive extraction, roster block reasons live in `domain.rosters`, and application toolkit
  block reasons are created only at the service boundary.
- Documentation closeout, full pytest, packet validation, desktop smoke, Browser route sweep, and
  protected-data scan remain the final commit gates.
