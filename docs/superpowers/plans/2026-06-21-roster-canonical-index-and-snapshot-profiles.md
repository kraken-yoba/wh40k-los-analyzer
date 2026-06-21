# Roster Canonical Index And Snapshot Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Phase 4B deterministic roster enrichment: canonical selection indexing plus local
snapshot profile/rule candidates extracted from admitted `.ros`/`.rosz` inputs.

**Architecture:** Keep persistent contracts in `domain.rosters`, XML extraction in
`ingestion.roster_xml`, and toolkit payload assembly in `application.roster_import`. Use synthetic
fixtures only.

**Tech Stack:** Python 3.12, dataclasses, stdlib XML after the existing fail-closed gate, pytest,
Ruff, mypy.

---

## File Structure

- Modify: `src/warhammer_companion/domain/rosters.py`
  - Add snapshot profile/rule/characteristic, unresolved candidate, selection index, and profile
    pack records.
- Modify: `src/warhammer_companion/ingestion/roster_xml.py`
  - Extract direct embedded profiles, characteristics, and rule metadata from admitted selections.
- Modify: `src/warhammer_companion/application/roster_import.py`
  - Add index/profile-pack enrichment to successful import payloads and warning language.
- Create: `tests/test_roster_snapshot_profiles.py`
  - Phase 4B red/green tests.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Record Phase 4B decisions, review triage, verification, and blockers.
- Create: `docs/superpowers/qa/2026-06-21-roster-canonical-index-and-snapshot-profiles-qa.md`
  - Autonomous QA pathway.
- Create: `docs/superpowers/reviews/2026-06-21-phase-4b-consultant-roster-candidates.md`
  - Consultant findings and final approval.
- Create: `docs/superpowers/reviews/2026-06-21-phase-4b-adversarial-roster-candidates.md`
  - Adversarial findings, triage, and final approval.

## Task 1: Write Failing Tests

- [ ] **Step 1: Add embedded profile/rule tests**

Create `tests/test_roster_snapshot_profiles.py` with synthetic XML proving:

- `.ros` import preserves embedded profiles and characteristics as local snapshot evidence.
- Nested selection profile/rule evidence is present in the snapshot pack.
- Rule descriptions are represented by SHA-256 and length, not retained as text.
- Selection index entries include depth, counts, source paths, and type counts.
- Profile candidates are emitted for selections and all statuses are `unresolved`.
- Result remains `estimated`, has no overlays, and disallows recommendation language.

- [ ] **Step 2: Add identity and blocked-path tests**

Add tests proving:

- Snapshot pack hash changes when embedded characteristic/rule data changes.
- Blocked malicious XML inputs produce no army, no roster index, and no snapshot profile pack.
- Snapshot warnings do not use official, legal, safe, recommended, likely, or trusted language.

- [ ] **Step 3: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_profiles.py -q
```

Expected: FAIL because Phase 4B records and extraction do not exist.

## Task 2: Implement Domain And Parser Enrichment

- [ ] **Step 1: Add domain records**

Add immutable records to `domain.rosters`:

- `ProfileResolutionStatus`
- `RosterSnapshotCharacteristic`
- `RosterSnapshotProfile`
- `RosterSnapshotRule`
- `RosterSnapshotProfileCandidatePack`
- `RosterProfileCandidate`
- `RosterSelectionIndexEntry`
- `RosterSelectionTypeCount`
- `CanonicalRosterIndex`

Add helper methods on `RosterSelection`/`CanonicalArmy` only when they reduce duplicated traversal.

- [ ] **Step 2: Extend XML extraction**

In `ingestion.roster_xml`, extract direct embedded profile, characteristic, and rule metadata from
selection children after the existing safety gate admits the XML.

Do not parse rule descriptions as mechanics. Store only digest and length.

Block multi-force or zero-force roster XML with explicit unsupported-shape reasons until the
canonical model is force-aware. Add whole-document structural limits for total elements, element
depth, attributes, text length, profiles per selection, rules per selection, and characteristics per
profile.

- [ ] **Step 3: Enrich application payloads**

In `application.roster_import`, attach `CanonicalRosterIndex` and `RosterSnapshotProfilePack` to
successful `RosterImportPayload` values. Blocked payloads keep those fields `None`.

Add explicit local-evidence warnings for snapshot profile/rule/cost data.

Ensure candidate records carry record-level `local_evidence`, `unresolved`,
`not_official_points`, and `not_profile_resolution` markers.

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_profiles.py -q
```

Expected: PASS.

## Task 3: Review, QA, And Commit

- [ ] **Step 1: Run focused regression**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_roster_snapshot_profiles.py tests\test_roster_import_safety.py tests\test_toolkit_contracts.py tests\test_rules_sources.py tests\test_base_sizes.py tests\test_terrain_semantics.py -q
```

Expected: PASS.

- [ ] **Step 2: Run static checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
```

Expected: all pass.

- [ ] **Step 3: Run consultant and adversarial review**

Reviewers must inspect:

- Phase 4B does not become profile resolution, points authority, UI, persistence, or tactical
  analysis.
- Rule description text is not retained in canonical records or fixtures beyond tiny synthetic
  test strings.
- Snapshot evidence cannot imply legality, official points, or trusted mechanics.
- Source refs, source paths, and identity hashes are sufficient for later resolution work.

- [ ] **Step 4: Run full validation and manual QA**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Then run the established Browser route sweep against the local web app. If Browser fails, try
Computer Use with Firefox and record the exact blocker.

- [ ] **Step 5: Protected-artifact scan and commit**

Confirm no raw roster/profile/community/official data, logs, screenshots, generated databases,
Codex state, or `AGENTS.md` are staged.

Commit message:

```text
Add roster snapshot profile candidates
```
