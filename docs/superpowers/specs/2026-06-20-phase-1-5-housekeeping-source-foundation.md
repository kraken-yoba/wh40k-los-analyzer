# Phase 1.5 Housekeeping Source Foundation Design

Date: 2026-06-20

## Goal

Perform behavior-preserving cleanup after Phase 1 before starting Phase 2.

## Scope

The code cleanup is test-contract typing around remote verification:

- Change `_fake_get_factory()` in `tests/test_rules_sources.py` from returning `object` to returning
  the `RemoteGet` protocol used by `verify_remote_http_source()`.
- Express `RemoteResponse` protocol attributes as read-only properties so frozen fake responses can
  satisfy the protocol under test-specific mypy.

This makes the injected fake response contract explicit without changing runtime behavior.

## Non-Goals

- No production feature changes.
- No service, CLI, web, desktop, packaging, source-fetch workflow, or source metadata changes.
- No new external source facts.
- No official PDFs, copied source text, roster data, or generated packs.

## Acceptance Criteria

- Consultant and adversarial reviewers approve the housekeeping scope.
- The only production-code change, if made, is protocol typing that preserves verifier behavior.
- The test cleanup uses `RemoteGet`/`RemoteResponse` and passes `mypy tests/test_rules_sources.py`.
- `tests/test_rules_sources.py` passes.
- `ruff format --check src tests`, `ruff check .`, and `mypy src` pass.
- `AGENTS.md` remains user-owned and unstaged.
- Changes are committed atomically if reviewers approve the cleanup.
