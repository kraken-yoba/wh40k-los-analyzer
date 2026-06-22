# Phase 9 Mission Pack Skeleton Spec

Date: 2026-06-22

## Roadmap Anchor

Phase 9 is Mission Pack And Game Analytics Primitives. The roadmap asks for mission, primary,
secondary/action, objective, deployment map, and timing records before captain-level analytics.

This first Phase 9 slice creates a source-safe mission pack skeleton. It does not implement mission
scoring, secondary/action parsing, objective control math, or matchup analytics.

## Goal

Add typed mission pack records and a user-facing Mission Pack surface that shows the currently known
primary mission environment from existing layout metadata while treating public/community mission
sources as untrusted candidate inputs.

## Inputs

- Existing `OfficialLayoutMetadata` already stores short primary mission labels and source pages for
  official event companion layouts.
- The user-provided public Google Sheet URL is recorded as a candidate public/community source only:
  `https://docs.google.com/spreadsheets/d/1vlRuvuiy6YOOPLmYyLEUfcGVpGL56aWWMA4iWh18Yuw/edit?gid=1565185881#gid=1565185881`.
  The only stored fields are the URL, sheet id, gid `1565185881`, retrieval status `not_fetched`,
  trust `untrusted_candidate`, and a warning that no sheet content hash exists because no fetch
  occurs. The app must not fetch it, parse it, store images, or copy full card text in this slice.

## Supported In This Slice

- Mission source refs and anchors:
  - derived official layout metadata source;
  - public mission sheet candidate source.
- Primary mission records:
  - short label;
  - stable normalized id;
  - source page anchors from layout metadata;
  - readiness `estimated`.
- Mission pack payload/result:
  - source refs;
  - primary mission records;
  - warnings that mechanics/scoring/action text are source-pending;
  - warnings that public sheet data is untrusted and not ingested.
- Web route `/mission-pack`.
- Desktop screen `Mission Pack`.

## Explicitly Out Of Scope

- Fetching Google Sheets or image URLs.
- OCR, image processing, or storing card images.
- Full card text or protected rules text.
- Primary scoring formulas.
- Secondary/action mechanics.
- Objective control, contest, action eligibility, disruption, denial, flip potential, or hidden
  action capacity calculations.
- Team-pairing analytics, score recommendations, or expected tournament points.

## Architecture

- `domain/missions.py`: mission source refs, anchors, records, pack records, and payload records.
- `application/mission_pack.py`: deterministic builder from existing layout metadata.
- `application/services.py` and `application/view_models.py`: shared service/state methods.
- `web/server.py` and `web/templates/mission_pack.html`: server-rendered route; no custom
  JavaScript.
- `desktop/screens/mission_pack.py` and `desktop/main_window.py`: thin PySide6 adapter.

## Readiness And Trust

- The toolkit result is `estimated`, never `trusted`.
- Public sheet source is recorded as untrusted/public candidate data and is not read.
- Public sheet source metadata must use retrieval status `not_fetched`, trust
  `untrusted_candidate`, and no content hash.
- Mission records are derived from existing short layout labels only; mechanics are source-pending.
- Results must not use legal, optimal, recommended, likely, target priority, or pairing-score
  language.

## Acceptance Criteria

- Mission pack result contains source refs, warnings, and primary mission records with anchors.
- Short mission labels from existing layout metadata are deduplicated and stable-id normalized.
- The public sheet candidate is present as source metadata only and not ingested.
- No card images, full card text, screenshots, generated mission packs, or external-sheet payloads
  are committed.
- Web and desktop surfaces render the Mission Pack summary and cautious warnings.
- Standard validation and Browser QA pass.
