# TTS Pivot Research Note

Date: 2026-06-22

## Decision

The sensible pivot is a TTS-first bridge, not an immediate rewrite of the project in Lua.

- Lua should own TTS interaction: live object discovery, selected-object controls, native physics
  casts, visible beams, hit markers, and local HTTP calls.
- Python should remain the durable companion engine for roster import, source trust, session state,
  batch analysis, reporting, and fallback rendering.
- War Organ, Hutber, and ForceOrg integrations are adapter hypotheses until representative saves
  and roster outputs are captured as fixtures.
- C or Rust should be deferred until TTS casts, explicit LOS proxies, and Python-side geometry are
  proven insufficient.

This keeps TTS as the live table source without moving roster safety, provenance, raster overlays,
and report logic into the least suitable runtime.

## Why Pivot Toward TTS

The current app manually models 40k boards and terrain packets. TTS already has the live table:
terrain objects, model positions, rotations, bases, markers, and mod-specific metadata. A TTS-first
workflow can therefore inspect the actual game state instead of asking users to recreate it in a
separate planner.

The existing Python code still matters. It should become the companion layer that consumes TTS board
snapshots and produces cautious deterministic diagnostics. The existing raster LOS and hidden
coverage renderer should remain the fallback/baseline until TTS snapshot ingestion and LOS
calibration are proven on real tables.

## API Findings

### TTS Lua Is The In-Game Surface

TTS stores Lua scripts inside save/workshop JSON. A game has one Global Script and optional Object
Scripts, which makes Lua the right place for buttons, selected-object actions, tags, beams, and
simple Workshop-only diagnostics.

Reference: [TTS scripting introduction](https://api.tabletopsimulator.com/)

### TTS Can Call A Local Companion

TTS `WebRequest` can call web services from the host computer. For a hosted multiplayer table,
`127.0.0.1` means the host machine, not each remote player. The host must run the companion app for
companion-backed features.

JSON should use `WebRequest.custom` with `Content-Type: application/json`, response-code checks,
timeout/error handling, and a small response schema. `WebRequest.post` is form-encoded and should
not be the assumed JSON path.

Reference: [TTS WebRequest manager](https://api.tabletopsimulator.com/webrequest/manager/)

### TTS Can Attempt A Live Inventory Snapshot

TTS Lua can enumerate objects and read names, GUIDs, tags, transforms, scale, bounds, visual bounds,
snap points, decals, and vector lines. That is enough to attempt an inventory snapshot, but not
enough to claim exact gameplay footprints, true meshes, or terrain semantics.

The snapshot schema should mark fields as:

- `observed`: direct TTS values such as GUID, tag, position, rotation, scale, bounds;
- `inferred`: derived battlefield coordinates, terrain roles, base radius, ownership;
- `manual`: user-provided tags, mappings, or corrections.

Reference: [TTS Base functions](https://api.tabletopsimulator.com/base/),
[TTS Object API](https://api.tabletopsimulator.com/object/)

### TTS Physics Casts Are The First LOS Primitive

TTS exposes `Physics.cast` with ray, box, and sphere casts. It returns hit objects, hit points,
normals, and distances. This is the first native candidate for model-to-model LOS.

These results are diagnostic until calibrated. Physics casts hit colliders, not necessarily the
visible mesh or a Warhammer terrain rule profile. TTS also warns that 30+ casts at once can stutter
or crash the game, so dense heatmaps and broad unit sweeps should not start as Lua-only cast loops.

Reference: [TTS Physics.cast](https://api.tabletopsimulator.com/physics/)

### Renderer Features Are Not A Lua LOS API

Unity can render shadows efficiently with shadow maps, and Unity C# has `Physics.Raycast` plus
batched `RaycastCommand`. TTS Lua exposes the physics wrapper, not a renderer/depth-buffer query or
Unity job-system batch API.

Visual beams are still useful for auditability. They can show the tested line and hit marker, but
the programmatic result should come from TTS physics casts, explicit LOS proxy geometry, or a
companion-side geometry engine.

References:
[Unity shadow mapping](https://docs.unity3d.com/Manual/shadow-mapping.html),
[Unity Physics.Raycast](https://docs.unity3d.com/ScriptReference/Physics.Raycast.html),
[Unity RaycastCommand](https://docs.unity3d.com/ScriptReference/RaycastCommand.html)

## Immediate Validation Plan

The next work should be a narrow feasibility harness, not a broad product rewrite.

### Phase 0 Scope

Build one local test save and one minimal Lua script that can:

- identify three manually tagged objects: attacker, target, and LOS-blocking terrain;
- capture a minimal `TtsBoardSnapshot v0`;
- prove a `TtsBoardTransform`: TTS origin, board rotation, scale to 44 x 60 battlefield inches,
  and round-trip checks from known placements;
- run one selected attacker-to-target `Physics.cast`;
- draw one visible beam and one hit marker;
- call `POST /api/tts/snapshot` with JSON via `WebRequest.custom`;
- save one sanitized JSON fixture from the companion.

Out of scope for Phase 0:

- War Organ roster linking;
- automatic Hutber/ForceOrg adapter logic;
- batch heatmaps;
- C/Rust side engines;
- official PDF or rules ingestion changes;
- claims that TTS LOS is legal, trusted, or tournament-authoritative.

### Phase 0 Exit Criteria

The feasibility harness is useful only if it produces measurable evidence:

- the companion receives schema-valid JSON for the tagged attacker, target, terrain, transform, and
  cast result;
- known TTS placements round-trip to battlefield inches within an explicitly recorded tolerance;
- the visible beam and hit marker match the reported cast path;
- a hosted-table smoke check confirms that the host-running companion receives the request while
  remote clients do not need local services for basic visual use;
- the result is labeled diagnostic until a later truth table compares collider hits to player
  visual judgment.

### LOS Calibration Gate

Before building real tools, run a small truth table on representative Hutber/ForceOrg-style tables:

- compare physics ray, sphere, and box casts against player visual judgment;
- test base-center, eye-point, hull/body, and target sample origins;
- record false positives and false negatives by terrain type;
- measure a safe cast budget and interaction latency on a normal host machine;
- identify terrain that needs explicit LOS proxy solids.

Passing this gate unlocks a selected-model LOS checker. Collider mismatch unlocks proxy audit
tooling. Performance failure moves batch work to the companion. HTTP/workflow failure keeps the
Workshop mod as a standalone diagnostic helper.

## Infrastructure Needed For Phase 0

Required:

- local Tabletop Simulator installation;
- one representative test save with tagged terrain and two tagged models;
- local Python companion endpoint on the host machine;
- manual Lua paste/injection workflow for the test save;
- sanitized fixture output under a non-generated docs/test location.

Useful but deferred:

- representative War Organ output;
- Hutber and ForceOrg convention survey fixtures;
- Lua save-file injection tooling;
- cast benchmark harness;
- protected-artifact scan for raw rosters, official PDFs, screenshots, caches, and generated data.

## Side Engine Gate

Do not start a C or Rust LOS engine from bounds-only snapshots. A faster engine is useful only after
the project has:

- a proven TTS-to-battlefield transform;
- explicit LOS proxy solids or usable geometry;
- fixture-backed evidence that TTS physics casts or Python fallback geometry are inadequate.

Until then, the likely failure mode is not speed. It is poor input geometry or unclear terrain
semantics.

## Open Questions

- Do common Hutber/ForceOrg tables encode terrain type, footprint, height, or rules semantics?
- Are common terrain colliders close enough to player visual LOS?
- Can War Organ output be linked to TTS models automatically, or is manual linking required?
- What latency and cast count are acceptable during a hosted game?
- Which features should remain available when the host is not running the companion?

## Recommendation

Start with Phase 0. Preserve the current Python engine while proving that a real TTS table can
produce a calibrated board snapshot, a diagnostic LOS cast, a visible audit beam, and a local
companion round trip. Only after that evidence should the project commit to deeper TTS tooling,
adapter work, or native side-engine exploration.
