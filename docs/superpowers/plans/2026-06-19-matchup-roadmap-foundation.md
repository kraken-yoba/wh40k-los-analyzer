# Matchup Roadmap Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Use consultants before execution and adversarial reviewers after each meaningful checkpoint. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 0/1 source trust contract and offline 11e RulesPack skeleton for the matchup-analysis roadmap.

**Architecture:** Add a focused `warhammer_companion.rules` package with source-reference models, RulesPack models, and a deterministic bundled core-rules builder. Expose the foundation through tests and a small CLI summary command rather than adding placeholder web/desktop screens.

**Tech Stack:** Python 3.12, Pydantic v2, Typer, pytest, ruff, mypy.

---

## Review Gates

- Before implementation: dispatch at least one codebase explorer, one source/librarian consultant, and one planning reviewer.
- During implementation: use TDD for every behavior change.
- After each committed implementation checkpoint: run spec compliance review first, then adversarial code-quality review.
- Before final handoff: run a LazyCodex gate/adversarial review over the full branch diff and QA evidence.
- Preserve shared-worktree safety: run `git status --short` before each task and do not revert unrelated user changes.

## Edition And Source Policy

- `wh40k-11e` is a project edition tag from the roadmap brief, not a claim proven by the PDF filename alone.
- Official Core Rules PDF anchors and hash control the first RulesPack.
- The RulesPack stores source ids, labels, anchors, hashes, short terms, and concept mappings only.
- It must not store long copied rules text, page images, full tables, near-verbatim rule blocks, or large extracted excerpts.
- Public Google Sheet records are untrusted mission/card inputs.
- Wahapedia records are provisional 10e profile-bootstrap inputs.

## Execution Status

- Task 1 and Task 2 were completed and committed before the explicit subagent requirement was restated.
- Task 3 and onward must use the review gates above.
- The CLI command is a developer/QA observable surface, not a committed product UI promise.

## File Structure

- Create: `src/warhammer_companion/rules/__init__.py`
  - Public package boundary for rules foundations.
- Create: `src/warhammer_companion/rules/sources.py`
  - Source kind, authority, trust state, and source-reference models.
- Create: `src/warhammer_companion/rules/models.py`
  - Canonical RulesPack, source document, rule section, glossary, concept mapping, readiness, and validation models.
- Create: `src/warhammer_companion/rules/core_rules.py`
  - Offline builder for `wh40k-11e-core-2026-06-01`.
- Modify: `src/warhammer_companion/cli.py`
  - Add `rules-pack` command as the observable surface.
- Create: `tests/test_rules_sources.py`
  - TDD coverage for source trust and serialization.
- Create: `tests/test_rules_pack.py`
  - TDD coverage for core RulesPack and old-assumption guardrails.
- Modify: `tests/test_cli.py`
  - CLI smoke coverage for the rules-pack summary.

---

### Task 1: Source Trust Contract

**Files:**
- Create: `tests/test_rules_sources.py`
- Create: `src/warhammer_companion/rules/__init__.py`
- Create: `src/warhammer_companion/rules/sources.py`

- [x] **Step 1: Write the failing tests**

Create `tests/test_rules_sources.py`:

```python
from __future__ import annotations

from warhammer_companion.rules.sources import (
    SourceAuthority,
    SourceKind,
    SourceRef,
    SourceTrustState,
)


def test_official_pdf_source_ref_serializes_source_anchor() -> None:
    ref = SourceRef(
        source_kind=SourceKind.OFFICIAL_PDF,
        authority=SourceAuthority.AUTHORITATIVE,
        trust_state=SourceTrustState.TRUSTED,
        source_document_id="core-rules-2026-06-01",
        source_label="Warhammer 40,000 Core Rules",
        url="https://assets.warhammer-community.com/core.pdf",
        local_filename="core-rules.pdf",
        sha256="abc123",
        page_number=50,
        section_id="13.08",
        section_label="Benefit of Cover",
    )

    payload = ref.model_dump(mode="json")

    assert payload["source_kind"] == "official_pdf"
    assert payload["authority"] == "authoritative"
    assert payload["trust_state"] == "trusted"
    assert payload["section_id"] == "13.08"
    assert payload["page_number"] == 50


def test_public_sheet_source_ref_is_untrusted_by_default() -> None:
    ref = SourceRef.public_sheet(
        source_document_id="mission-sheet-public",
        source_label="Public mission sheet",
        url="https://docs.google.com/spreadsheets/d/example",
        sheet_gid="1565185881",
    )

    assert ref.source_kind == SourceKind.PUBLIC_SHEET
    assert ref.authority == SourceAuthority.SUPPORTING
    assert ref.trust_state == SourceTrustState.UNTRUSTED
    assert ref.sheet_gid == "1565185881"


def test_wahapedia_source_ref_is_provisional_profile_bootstrap() -> None:
    ref = SourceRef.wahapedia_10e(
        source_document_id="wahapedia-10e-datasheets",
        source_label="Wahapedia 10e data export",
        url="https://wahapedia.ru/wh40k10ed/the-rules/data-export/",
    )

    assert ref.source_kind == SourceKind.WAHAPEDIA_10E
    assert ref.authority == SourceAuthority.PROVISIONAL_PROFILE_BOOTSTRAP
    assert ref.trust_state == SourceTrustState.PROVISIONAL
    assert ref.edition_id == "wh40k-10e"
```

- [x] **Step 2: Run RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_rules_sources.py -q
```

Expected: FAIL because `warhammer_companion.rules` does not exist.

- [x] **Step 3: Implement the source models**

Create `src/warhammer_companion/rules/__init__.py`:

```python
"""Rules and source-trust foundations for matchup analysis."""
```

Create `src/warhammer_companion/rules/sources.py` with `StrEnum` classes for `SourceKind`, `SourceAuthority`, `SourceTrustState`, and a Pydantic `SourceRef` model with the fields used by the tests. Add `public_sheet()` and `wahapedia_10e()` class methods returning the explicit untrusted/provisional defaults.

- [x] **Step 4: Run GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_rules_sources.py -q
```

Expected: PASS.

- [x] **Step 5: Commit checkpoint**

Run:

```bash
git add tests/test_rules_sources.py src/warhammer_companion/rules
git commit -m "Add rules source trust contract"
```

---

### Task 2: Core RulesPack Skeleton

**Files:**
- Create: `tests/test_rules_pack.py`
- Create: `src/warhammer_companion/rules/models.py`
- Create: `src/warhammer_companion/rules/core_rules.py`

- [x] **Step 1: Write the failing tests**

Create `tests/test_rules_pack.py`:

```python
from __future__ import annotations

from warhammer_companion.rules.core_rules import build_core_rules_pack
from warhammer_companion.rules.models import ReadinessState


def test_core_rules_pack_identifies_official_source_metadata() -> None:
    pack = build_core_rules_pack()

    assert pack.rules_pack_id == "wh40k-11e-core-2026-06-01"
    assert pack.edition_id == "wh40k-11e"
    assert pack.readiness == ReadinessState.TRUSTED
    assert pack.source_documents[0].source_ref.source_document_id == "core-rules-2026-06-01"
    assert pack.source_documents[0].source_ref.local_filename == "core-rules.pdf"
    assert pack.source_documents[0].source_ref.sha256 == (
        "f6a2443a44627ac5f0ef08407d29aa5ec7e97339998f05bc35f3ae37bf276833"
    )


def test_core_rules_pack_contains_required_source_anchors() -> None:
    pack = build_core_rules_pack()
    anchors = {section.section_id: section for section in pack.source_sections}

    for section_id in ["03.04", "05.01", "13.08", "13.09", "13.10", "13.11", "14.01", "16.01", "20.04"]:
        assert section_id in anchors
        assert anchors[section_id].page_number > 0
        assert anchors[section_id].source_document_id == "core-rules-2026-06-01"


def test_core_rules_pack_maps_current_rules_concepts() -> None:
    pack = build_core_rules_pack()
    concepts = {concept.concept_id: concept for concept in pack.concept_mappings}

    assert concepts["benefit_of_cover"].display_label == "Benefit of Cover"
    assert "bs_worsening" in concepts["benefit_of_cover"].mechanic_tags
    assert "save_modifier" not in concepts["benefit_of_cover"].mechanic_tags

    assert "2in_horizontal_5in_vertical" in concepts["engagement_range"].mechanic_tags
    assert "1in_horizontal_only" not in concepts["engagement_range"].mechanic_tags

    assert concepts["reserve_arrival_method"].display_label == "Ingress Move"
    assert "Deep Strike-modified Ingress Move" in concepts["reserve_arrival_method"].related_terms

    assert concepts["objective_region"].display_label == "Terrain Objective"
    assert "terrain_area_range" in concepts["objective_region"].mechanic_tags

    assert set(concepts["visibility_state"].related_terms) >= {
        "visible",
        "fully visible",
        "Hidden",
        "Obscuring",
        "Solid",
    }
```

- [x] **Step 2: Run RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_rules_pack.py -q
```

Expected: FAIL because `rules.models` and `rules.core_rules` do not exist.

- [x] **Step 3: Implement the RulesPack models and builder**

Create Pydantic models in `src/warhammer_companion/rules/models.py`:

- `ReadinessState`
- `ValidationSeverity`
- `ValidationRecord`
- `RuleSourceDocument`
- `RuleSection`
- `GlossaryTerm`
- `ConceptMapping`
- `CanonicalRulesPack`

Create `src/warhammer_companion/rules/core_rules.py` with constants for the official core-rules URL/hash and a `build_core_rules_pack()` function that returns a deterministic `CanonicalRulesPack` with source anchors and concept mappings required by the tests.

- [x] **Step 4: Run GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_rules_sources.py tests/test_rules_pack.py -q
```

Expected: PASS.

- [x] **Step 5: Commit checkpoint**

Run:

```bash
git add tests/test_rules_pack.py src/warhammer_companion/rules
git commit -m "Add core rules pack skeleton"
```

---

### Task 3: CLI RulesPack Surface

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/warhammer_companion/cli.py`

- [ ] **Step 1: Write the failing CLI test**

Add to `tests/test_cli.py` using the existing `CliRunner` pattern:

```python
def test_cli_rules_pack_outputs_core_rules_summary() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["rules-pack"])

    assert result.exit_code == 0
    assert "wh40k-11e-core-2026-06-01" in result.output
    assert "core-rules-2026-06-01" in result.output
    assert "Benefit of Cover" in result.output
    assert "trusted" in result.output
```

- [ ] **Step 2: Run RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k rules_pack -q
```

Expected: FAIL because the CLI command does not exist.

- [ ] **Step 3: Add the CLI command**

Modify `src/warhammer_companion/cli.py`:

```python
from warhammer_companion.rules.core_rules import build_core_rules_pack
```

Add:

```python
@cli.command("rules-pack")
def rules_pack() -> None:
    """Print the bundled core rules pack summary."""
    pack = build_core_rules_pack()
    typer.echo(f"{pack.rules_pack_id}: {pack.readiness.value}")
    for source in pack.source_documents:
        typer.echo(
            f"  source {source.source_ref.source_document_id}: "
            f"{source.source_ref.local_filename}"
        )
    typer.echo("  concepts:")
    for concept in pack.concept_mappings:
        typer.echo(f"  - {concept.display_label} ({concept.concept_id})")
```

- [ ] **Step 4: Run GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k rules_pack -q
```

Expected: PASS.

- [ ] **Step 5: Commit checkpoint**

Run:

```bash
git add tests/test_cli.py src/warhammer_companion/cli.py
git commit -m "Expose core rules pack summary"
```

---

### Task 4: Verification And Observable QA

**Files:**
- Existing files changed by prior tasks.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_rules_sources.py tests/test_rules_pack.py tests/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: PASS.

- [ ] **Step 3: Run lint and type checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\mypy.exe src
```

Expected: PASS.

- [ ] **Step 4: Drive the matching surface**

Run:

```powershell
.\.venv\Scripts\python.exe -m warhammer_companion.cli rules-pack
```

Expected output includes:

```text
wh40k-11e-core-2026-06-01: trusted
source core-rules-2026-06-01: core-rules.pdf
Benefit of Cover
```

- [ ] **Step 5: Final status**

Run:

```bash
git status --short
```

Expected: clean, unless the current agent is intentionally leaving uncommitted follow-up changes for review.
