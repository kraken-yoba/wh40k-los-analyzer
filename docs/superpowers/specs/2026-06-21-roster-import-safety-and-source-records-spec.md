# Roster Import Safety And Source Records Spec

Date: 2026-06-21

Parent roadmap:

- `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`
- `docs/superpowers/reviews/2026-06-21-phase-3-5-adversarial-semantics-hardening.md`

## Goal

Add the first Phase 4A roster-import boundary: safely admit hostile roster-like inputs into a
quarantined import record with source metadata, hashes, archive/XML safety diagnostics, and a
shallow canonical roster snapshot.

This phase proves the app can inspect `.ros` and `.rosz` inputs without trusting them, storing raw
data in the repo, resolving profiles, importing community catalogs, or making tactical claims.

## Scope

Implement a source-record and admission layer for:

- `.ros` XML bytes.
- `.rosz` zip archives containing exactly one selected `.ros` XML member.

The implementation must:

- Inspect archives in memory without extracting members to disk.
- Block absolute paths, `..`, nested archives, encrypted members, unexpected extensions, excessive
  member count, oversized compressed bytes, oversized decompressed bytes, and high decompression
  ratio.
- Pre-screen XML bytes for `DOCTYPE`, DTD declarations, entity declarations/references, XInclude,
  and HTTP/HTTPS references before parsing.
- Parse only already-screened XML bytes with the standard library XML parser; the pre-screen gate
  is the hardened-parser equivalent for this slice because `defusedxml` is not a current project
  dependency.
- Preserve short roster identity fields and selection/cost IDs/names/values from synthetic
  BattleScribe-style fixtures.
- Return `ToolkitResult` values with readiness, warnings, block reasons, source refs, and stable
  provenance-sensitive input hashes.

## Non-Goals

- No `.cat`, `.catz`, `.gst`, `.gstz`, `.bsr`, public-sheet, image, or pasted-roster ingestion.
- No New Recruit account/API workflow.
- No BSData/community catalog import or refresh.
- No official MFM row import, points authority, or points divergence checks.
- No profile resolution, aliases, manual corrections, damage/survivability, movement/threat,
  mission, team-pairing, or AI companion behavior.
- No web, desktop, persistence, upload, or review UI.
- No real roster archives, community catalogs, official PDFs, protected profile/rule text, or
  processed roster packs committed to the repository.

## Data Model

Create immutable domain records in `warhammer_companion.domain.rosters`:

- `RosterSourceKind`: `ros_xml`, `rosz_archive`.
- `RosterImportFormat`: `battlescribe_ros_v0`.
- `RosterImportSource`: filename, source kind, byte size, SHA-256, selected XML member path,
  selected XML SHA-256, parser version, schema version, quarantine status, warnings, and block
  reasons.
- `RosterCost`: raw cost ID, name, type ID, and value as-presented.
- `RosterSelection`: raw selection ID, name, type, source path, child selections, and costs.
- `CanonicalArmy`: roster ID, name, game system ID, catalogue name, source format, selections,
  costs, and source refs.
- `RosterImportPayload`: source record plus optional canonical army.

The canonical army is intentionally shallow. It preserves short identifiers and hierarchy from
the roster input, but it does not treat embedded profiles/rules/characteristics as authority and
does not copy long profile/rule text into distributed artifacts.

## Ingestion Modules

Create focused ingestion helpers:

- `warhammer_companion.ingestion.roster_archives`
  - `inspect_roster_archive(...)`
  - archive limits and member diagnostics.
- `warhammer_companion.ingestion.roster_xml`
  - `parse_roster_xml(...)`
  - pre-screen XML safety gate and shallow XML-to-domain extraction.

Keep file/path handling injectable and byte-oriented so tests can generate tiny synthetic fixtures
without committing raw roster files.

## Application Service

Create `warhammer_companion.application.roster_import`:

- `build_roster_import_result_from_bytes(...)`
- Returns `ToolkitResult[RosterImportPayload]`.
- Uses `blocked` for unsafe archives/XML.
- Uses `estimated` for successfully parsed roster snapshots because roster data is local evidence,
  not source authority.
- Emits no overlays and no recommendation/legal/points language.

## Acceptance Criteria

- `.ros` XML bytes produce an estimated import result with a `RosterImportSource`, source refs,
  stable input hash, and shallow `CanonicalArmy`.
- `.rosz` bytes produce an estimated import result when the archive contains one safe `.ros` member.
- `.rosz` import records archive member path, compressed size, decompressed size, selected XML hash,
  parser version, and schema version.
- Unsafe archives block with no canonical army and no tactical overlays.
- Unsafe XML blocks with no canonical army and no tactical overlays.
- Import hashes change when filename, source bytes, or source kind changes.
- No roster entry in a synthetic fixture is silently discarded.
- Costs are preserved as presented without treating points as official.
- Results never claim legality, valid list construction, resolved profiles, official points,
  recommendations, or tactical safety.
- Existing LOS, rendering, web, desktop, packet validation, and Phase 3/3.5 semantics remain
  unchanged.

## QA Requirements

Automated QA must include:

- Safe `.ros` and `.rosz` synthetic fixtures.
- Malicious archive fixtures for path traversal, absolute paths, nested archives, encryption flags,
  unexpected file types, too many members, oversized decompressed bytes, and decompression ratio.
- Malicious XML fixtures for malformed XML, `DOCTYPE`, entity declarations/references, XInclude,
  and HTTP/HTTPS references.
- Protected-artifact scan proving no raw roster/archive/community/official source data is staged.
- Standard Ruff, mypy, full pytest, packet validation, desktop smoke, and Browser route smoke if
  the user requires manual QA for the phase loop.

## Review Requirements

Consultant review must confirm:

- Phase 4A is safely split from canonical roster enrichment, profile resolution, MFM points, and UI.
- File placement follows `AGENTS.md`.

Adversarial review must confirm:

- Unsafe archive/XML inputs fail closed.
- Import outputs cannot be mistaken for source authority or tactical truth.
- No protected/raw data is committed or packaged.
- No UI/LOS/rendering behavior changed.

## Browser And Computer Use

Phase 4A changes no UI, but the active roadmap loop requires manual QA. Final closeout should run
the established Browser route sweep against the local web app. If Browser fails, record the exact
blocker and try Computer Use/Firefox before marking manual UI QA blocked.
