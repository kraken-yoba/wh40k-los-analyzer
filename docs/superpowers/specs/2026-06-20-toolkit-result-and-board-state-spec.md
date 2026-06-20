# Toolkit Result And Board State Spec

Date: 2026-06-20

## Status

Draft Phase 2 fine-grain implementation spec for the player-toolkit roadmap.

Parent roadmap: `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`

## Goal

Add shared typed contracts that every deterministic toolkit can use before rendering or AI
summarization.

This slice creates `ToolkitResult`, `MapOverlayLayer`, and a minimal `BoardState` that binds an
existing `MapPacket` to game-state assumptions without changing existing LOS, heatmap, hidden
coverage, web, or desktop behavior.

## Scope

Add:

- `src/warhammer_companion/domain/board_state.py`
- `src/warhammer_companion/domain/overlays.py`
- `src/warhammer_companion/application/toolkit.py`
- `ToolkitReadiness` states: `trusted`, `estimated`, `degraded`, and `blocked`.
- `ToolkitAssumption` and `ToolkitWarning` shared domain metadata.
- `BlockReason`, `ValidationRecord`, and `ExportMetadata` application result metadata records.
- `ToolkitResult[T]` as a frozen generic dataclass carrying readiness, payload, source refs,
  assumptions, warnings, block reasons, validation records, and export metadata.
- `MapOverlayLayer` as a rendering-neutral Shapely geometry overlay primitive.
- `BoardUnit`, `BoardModel`, `BoardState`, and `BoardStateContext` as minimal board-state
  primitives.
- A convenience constructor `BoardState.from_packet()` that wraps a `MapPacket` without mutating
  it.
- Tests proving readiness semantics, board-state packet separation, missing model/base handling,
  overlay geometry semantics, and no LOS behavior regression.

## Non-Goals

This slice must not:

- Add movement, threat, damage, roster, mission, or AI tools.
- Add web routes, desktop widgets, custom JavaScript, TypeScript, or new UI frameworks.
- Change `MapPacket` fields or store rules mechanics inside it.
- Change existing LOS, heatmap, hidden coverage, rendering, packet ingestion, or app behavior.
- Download, bundle, parse, or store official PDFs, public sheets, roster data, or community data.
- Claim that any board state is `trusted` by default.

## Architecture

Board-state and overlay contracts live in `warhammer_companion.domain` because they are durable
product model objects shared by application services, rendering projections, desktop adapters, and
later AI tool-calling. `ToolkitResult` lives in `warhammer_companion.application` because it is the
service result envelope returned before web or desktop rendering. None of these modules may import
FastAPI, PySide, Jinja, or rendering helpers.

`MapPacket` remains layout geometry only. `BoardState` references a selected `MapPacket` and adds
game-state context, units, models, source refs, and readiness metadata around it. The wrapper is
immutable and does not modify or copy rules mechanics into the packet.

Early `BoardState` instances may have no units. That is valid for existing LOS/map workflows, but
the state readiness is `estimated` with an explicit missing-data warning because downstream
movement/threat tools cannot make legal or safe claims without model positions and base sizes.

`ToolkitResult` supports every downstream tool. `blocked` results must carry at least one block
reason and must not carry tactical overlays. Recommendation wording is only allowed for `trusted`
results through `allows_recommendation_language()`.

## Data Model Requirements

`ToolkitResult[T]` must include:

- `result_id`
- `tool_id`
- `input_hash`
- `readiness`
- `payload`
- `overlays`
- `assumptions`
- `warnings`
- `block_reasons`
- `source_ref_ids`
- `validation_records`
- `export_metadata`

It must expose:

- `is_blocked`
- `is_usable`
- `allows_recommendation_language()`

It must validate:

- readiness is one of `trusted`, `estimated`, `degraded`, and `blocked`
- `blocked` results have at least one block reason
- `blocked` results do not include overlays
- `trusted` results have source refs and at least one passed validation record
- overlay readiness cannot exceed the result readiness

`MapOverlayLayer` must include:

- `layer_id`
- `layer_kind`
- `geometry`
- `units`
- `style_token`
- `label`
- `readiness`
- `source_ref_ids`

It must expose:

- `is_empty`

`BoardState` must include:

- `state_id`
- selected `MapPacket`
- `BoardStateContext` with round, turn, phase, active player, and going-first assumption
- `units`
- `source_ref_ids`
- `readiness`
- `assumptions`
- `warnings`

`BoardUnit` must include:

- `unit_id`
- `label`
- `controller`
- `models`
- `source_ref_ids`
- `readiness`
- `warnings`

`BoardModel` must include:

- `model_id`
- optional `base_diameter`
- optional `position`
- optional `footprint`
- `source_ref_ids`
- `readiness`
- `warnings`

The implementation should use frozen dataclasses with `slots=True` and strict types.

## Acceptance Criteria

- `ToolkitResult` defaults are immutable tuples, not mutable lists.
- `blocked` results report `is_blocked`, not `is_usable`, and do not allow recommendation
  language.
- `estimated` and `degraded` results are usable diagnostics but do not allow recommendation
  language.
- `trusted` results allow recommendation language.
- `MapOverlayLayer` accepts Shapely geometry and remains rendering-neutral.
- `BoardState.from_packet()` preserves the exact packet object reference and does not mutate
`MapPacket`. This is a shallow immutable wrapper over the live `MapPacket` object; the wrapper also
stores a packet content digest so durable toolkit results can detect same-id packet content changes.
- A board state with no units is `estimated` and warns that model positions and base sizes are
  missing.
- A board state with a model missing either position or base size is not `trusted` and includes an
  explicit warning for the missing field.
- A board state with a unit that has no models includes an explicit missing-model warning.
- A board state with all model positions and base sizes may be `estimated`, but not `trusted`,
  because source-backed mechanics and validation are not implemented in this slice.
- Existing LOS geometry tests still pass unchanged.
- No raw protected source text or generated official/community data is committed.

## Browser And Desktop QA Decision

Phase 2 changes no web route, template, static asset, desktop widget, generated SVG, or runtime UI
surface. Browser and Computer Use checks are not required for this slice. The phase QA still runs
existing service/rendering/desktop smoke commands to prove no runtime regression.

## Design Decisions

### Decision 1: Split domain contracts from application envelopes

`BoardState` lives in `src/warhammer_companion/domain/board_state.py` and `MapOverlayLayer` lives in
`src/warhammer_companion/domain/overlays.py` because they are domain data. Shared readiness,
assumption, and warning primitives also live in `domain.overlays` so domain modules do not import
from application modules. `ToolkitResult` lives in `src/warhammer_companion/application/toolkit.py`
because it is an application-service result envelope that can contain a payload plus overlays and
metadata before rendering.

### Decision 2: Source refs are IDs in this slice

The objects carry `source_ref_ids: tuple[str, ...]` rather than importing Phase 1 `SourceRef`
objects. This keeps the domain contracts free of ingestion ownership while still linking outputs
to the source registry.

### Decision 3: Minimal state is estimated, not trusted

Wrapping a `MapPacket` without units is useful for current map/LOS workflows, but it cannot support
legal movement, threat, roster, mission, or recommendation claims. The default readiness is
therefore `estimated`.

### Decision 4: Recommendation language is explicit

The first enforcement point is a small `allows_recommendation_language()` helper on
`ToolkitResult`. UI and AI wording tests can use this before later rendering or companion layers
exist.

### Decision 5: Service wrappers are introduced for LOS only

This slice adds a narrow `los_checker_toolkit_result()` service method that produces
`ToolkitResult` before the existing SVG `los_checker_state()` projection. Heatmap and hidden
coverage wrappers are deferred to later slices to keep this phase small while proving the contract
path.
