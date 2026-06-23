# TTS Harness Safety Baseline

Date: 2026-06-23

## Purpose

Phase 0 prepares the repository for the TTS bridge and supervised self-play harness without changing
runtime behavior.

## Local Artifact Policy

Ignored local paths:

- `data/tts/`
- `data/tts-harness/`
- `data/tts-saves/`
- `data/tts-screenshots/`
- `data/snapshots/`
- `data/replays/`
- `data/rosters/raw/`
- `data/steam-state/`
- `data/war-organ/`
- `data/codex-state/`
- `data/openai-state/`

Never commit raw TTS saves, raw rosters, official PDFs, generated snapshots, generated replay logs,
screenshots, Codex/OpenAI state, Steam state, War Organ local data, or credentials.

## RulesSourceTuple Draft

Required fields:

- `edition_id`
- `source_name`
- `publisher_or_domain`
- `source_kind`
- `url_or_local_reference`
- `release_or_update_id`
- `retrieved_at`
- `content_hash`
- `local_artifact_id`
- `source_trust`

The first implementation phases may define this as a typed Python record, but Phase 0 only records
the contract.

## Required Source Tuple Entries

- Core rules source.
- Event companion mission and terrain layout source.
- Prepared development roster fixture source.
- Weapons, profiles, base sizes, and named effects source for prepared rosters.
- Points/profile source for prepared rosters.
- Scripted non-tournament scoring fixture.

## Sanitized Snapshot Fixture Draft

Fixture fields:

- `snapshot_id`
- `source_session_label`
- `captured_at`
- `board_transform`
- `objects`
- `selected_object_ids`
- `source_warnings`
- `schema_version`

## Sanitized Object Fixture Draft

Fixture fields:

- `guid`
- `name`
- `tags`
- `object_kind`
- `owning_side`
- `position`
- `rotation`
- `scale`
- `bounds`
- `source_classification`
- `warnings`

## Development Roster Fixture Outline

The first prepared rosters should include two tiny forces, one simple shooting profile, one target
profile, one objective-control example, and no mixed saves, multi-damage allocation, Precision,
FnP-like post-save rolls, transports, reserves, or melee interactions.

## Phase 1 Handoff

Phase 1 may implement Python records, tests, and a Lua bridge template only after this baseline is
reviewed and committed. Phase 1 must not claim live bridge feasibility until TTS sends JSON to the
local companion through `WebRequest.custom`.
