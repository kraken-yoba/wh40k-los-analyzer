# Phase 11.5 Pairing Label Normalization Housekeeping Spec

Date: 2026-06-22

## Roadmap Anchor

Phase 11A added the Team Pairing Matrix dossier. Phase 11.5 is a housekeeping slice after that
runtime feature. It must be behavior-preserving and must not expand matchup analytics.

## Goal

Extract Team Pairing label normalization into a small, typed helper module so future roster/list
ingestion can reuse the same rules without changing current web, desktop, or toolkit behavior.

## Supported In This Slice

- Move label parsing and validation out of `application/matchup_matrix.py`.
- Preserve every Phase 11A label rule:
  - split on commas and newlines;
  - strip leading/trailing whitespace;
  - collapse internal whitespace;
  - remove non-printing controls except separators;
  - drop empty fragments;
  - preserve order;
  - block missing labels, more than eight labels per side, duplicate normalized labels, and labels
    longer than 80 characters.
- Preserve `PairingListEntry` ids and labels for all currently tested inputs.
- Preserve Team Pairing input hash/result id for current valid and blocked inputs.
- Preserve web route output, desktop output, and smoke-test behavior.

## Explicitly Out Of Scope

- New matchup analytics.
- New UI controls.
- New source ingestion, roster ingestion, public sheet fetches, PDF fetches, external AI calls, or
  source refreshes.
- Changes to warning/detail copy, readiness, component ids, scenario ranges, or matrix cell
  semantics.
- Changes to label limits or blocker ids.

## Architecture

- Add `application/pairing_labels.py` containing:
  - `LabelInput` alias;
  - `PairingLabelNormalizationResult`;
  - constants for count and length limits;
  - `normalize_pairing_list_entries(side, labels)`.
- `application/matchup_matrix.py` imports and uses this helper.
- Existing tests gain characterization assertions for default input hashes and normalized label
  outputs before and after the refactor.

## Acceptance Criteria

- Focused Team Pairing toolkit, service, web, desktop, and smoke tests pass.
- Ruff format/check, Ruff check, mypy, and full pytest pass.
- Manual route QA may use the same FastAPI TestClient fallback as Phase 11A if Browser/Computer
  control is still unavailable; this slice has no visual/UI behavior change.
- Consultant and adversarial review approve the behavior-preserving scope.
- Protected-path/source scan is clean.
- One atomic Phase 11.5 commit records the cleanup.
