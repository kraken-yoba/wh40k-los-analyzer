# Deterministic Data Spine Phase Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every implementation step and superpowers:subagent-driven-development or superpowers:executing-plans to execute this plan.

**Goal:** Establish the canonical data model, deterministic serialization, synthetic fixtures, validators, schema exports, and source manifest contracts that every later extraction, LOS, GUI, and export workflow depends on.

**Scope:** This phase does not parse official PDFs and does not implement LOS calculations. It creates the stable data contracts and fixtures needed to test those later phases deterministically.

---

## Decisions Applied

- Board coordinates are stored in inches.
- Canonical layout JSON uses sorted keys and fixed float precision.
- Source manifests store URLs, expected hashes, cache policy, and source type without committing official PDFs.
- Review and validation states are first-class data, not UI-only flags.
- Geometry tolerance and display tolerance are separate settings.

## Phase Steps

- [ ] **Step 1: Add failing schema tests**
  - Test canonical layout models require board dimensions, terrain features, blockers, deployments, provenance, validation status, and schema version.
  - Test invalid coordinates outside board bounds fail validation.
  - Test stable serialization produces identical bytes for equivalent model construction order.

- [ ] **Step 2: Implement canonical Pydantic models**
  - Add `fortyk_los_backend/domain/models.py`.
  - Include board, point, polygon, line segment, terrain feature, blocker, deployment zone, provenance, warning, validation, review, and layout models.
  - Use explicit units and enum values.

- [ ] **Step 3: Add deterministic serialization and hashing**
  - Add fixed precision float normalization.
  - Add canonical JSON bytes export.
  - Add stable SHA-256 layout hash excluding volatile local paths and timestamps.

- [ ] **Step 4: Add source manifest models**
  - Add source URL, expected hash, cache filename, source kind, license note, and retrieval status fields.
  - Add public-safe sample manifest entries for the official terrain and rules PDFs using source URLs only.
  - Add hash mismatch and missing-cache status tests.

- [ ] **Step 5: Add validator rules**
  - Validate board bounds, closed polygons, blocker endpoints, deployment zones, duplicate IDs, missing provenance, and unreviewed warnings.
  - Return structured warning/error records with codes suitable for GUI display.

- [ ] **Step 6: Add synthetic fixtures and goldens**
  - Add a tiny canonical board fixture with known footprints, wall segments, deployments, warnings, and provenance.
  - Add expected canonical JSON and hash outputs.
  - Keep fixtures copyright-safe and independent of official artwork/rules text.

- [ ] **Step 7: Export JSON Schema**
  - Generate deterministic schema files into `schemas/`.
  - Add a test that schema generation is stable and current.

- [ ] **Step 8: Add data-spine API endpoints**
  - Expose fixture layout list, layout detail, validation records, and source manifest status through FastAPI.
  - Add endpoint tests.

- [ ] **Step 9: Reviewer gate**
  - Run an adversarial data-spine reviewer subagent against models, validation rules, fixtures, and tests.
  - Fix valid findings before moving to LOS.

## Verification

Run after this phase:

```powershell
.\scripts\verify-public.cmd
git diff --check
```

Expected result: Ruff, mypy, pytest, schema stability tests, and fixture tests pass.
