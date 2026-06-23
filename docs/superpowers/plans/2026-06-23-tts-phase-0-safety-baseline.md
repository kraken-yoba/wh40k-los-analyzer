# TTS Phase 0 Safety Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement
> this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Prepare the repository for TTS bridge and supervised self-play implementation without
changing runtime behavior.

**Architecture:** Phase 0 is a behavior-preserving safety and fixture baseline. It records local
artifact boundaries, fixture schema drafts, rules-source tuple requirements, manual QA instructions,
and review gates while deferring Python bridge code and live TTS integration to Phase 1.

**Tech Stack:** Markdown docs, `.gitignore`, PowerShell verification, existing Python 3.12 project
checks, consultant/adversarial subagent review, CodeRabbit review when available.

---

## Phase Chain

This TTS implementation program uses separate goal loops:

- Main phases: 0, 1, 2, 3, 4, 5, 6, 7.
- Housekeeping phases: 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5.

Phase 0 closes by recording the next-loop trigger:
`Start Phase 0.5 TTS housekeeping semantics-preserving cleanup`.

## File Map

- Modify: `.gitignore`
  - Add explicit local TTS harness artifact paths.
- Create: `docs/tts-harness-safety-baseline.md`
  - Durable Phase 0 safety baseline, fixture policy, schema drafts, and source tuple requirements.
- Create: `docs/superpowers/qa/2026-06-23-tts-phase-0-safety-baseline-qa.md`
  - Manual and automated QA pathway for an independent reviewer.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-0-consultant-plan.md`
  - Consultant planning review record.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-0-adversarial-plan.md`
  - Adversarial planning review and triage record.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-0-consultant-closeout.md`
  - Consultant closeout review record.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-0-adversarial-closeout.md`
  - Adversarial closeout review and triage record.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Append factual Phase 0 decisions, review results, verification, blockers, and next trigger.
- Modify: this plan file as tasks are completed.

Phase 0 must not create production Python modules, web routes, desktop UI, Lua harness code, raw TTS
saves, generated snapshots, generated replay logs, credentials, official PDF copies, or raw rosters.

## Task 1: Preflight And Scope Lock

**Files:**
- Read: `AGENTS.md`
- Read: `docs/superpowers/specs/2026-06-23-tts-agentic-harness-migration-spec.md`
- Read: `docs/superpowers/specs/2026-06-23-tts-implementation-infrastructure-spec.md`
- Verify: `.gitignore`

- [x] **Step 1: Confirm branch and visible worktree state**

Run:

```powershell
git status -sb
git rev-parse HEAD
```

Expected: branch is `codex/assistant-companion-roadmap`; only user-owned untracked `AGENTS.md`
and this Phase 0 plan may be visible before the rest of the Phase 0 edits.

- [x] **Step 2: Confirm Phase 0 boundaries**

Run:

```powershell
rg -n "Phase 0|No committed official PDFs|raw TTS saves|RulesSourceTuple|Minimum Implementation Sequence" docs/superpowers/specs/2026-06-23-tts-agentic-harness-migration-spec.md docs/superpowers/specs/2026-06-23-tts-implementation-infrastructure-spec.md
```

Expected: Phase 0 is spec/fixtures/safety baseline only; live TTS bridge feasibility is not claimed.

## Task 2: Add Local Artifact Ignore Rules

**Files:**
- Modify: `.gitignore`

- [x] **Step 1: Add explicit TTS local artifact paths**

Append these entries if they are not already present:

```gitignore
data/tts/
data/tts-harness/
data/tts-saves/
data/tts-screenshots/
data/snapshots/
data/replays/
data/rosters/raw/
data/steam-state/
data/war-organ/
data/codex-state/
data/openai-state/
```

These paths are local-only buckets for controlled TTS saves, sanitized intermediate snapshots,
replay logs, bridge scratch output, raw roster experiments, TTS screenshots, Steam-derived state,
War Organ local exports, Codex/OpenAI state, and future harness artifacts. Existing `.gitignore`
entries already cover `.env`, `.env.*`, `data/codex-home*`, and `logs/`; Phase 0 keeps those
guardrails.

- [x] **Step 2: Verify ignore behavior**

Run:

```powershell
$paths = @(
  'data/tts/example.json',
  'data/tts-harness/example.json',
  'data/tts-saves/example.json',
  'data/tts-screenshots/example.png',
  'data/snapshots/example.json',
  'data/replays/example.json',
  'data/rosters/raw/example.rosz',
  'data/steam-state/example.json',
  'data/war-organ/example.json',
  'data/codex-state/auth.json',
  'data/openai-state/session.json',
  'logs/tts-harness.log',
  'data/codex-home/auth.json',
  '.env.local'
)
git check-ignore @paths
```

Expected: each path is printed, proving the artifacts are ignored.

## Task 3: Write Safety Baseline And Fixture Drafts

**Files:**
- Create: `docs/tts-harness-safety-baseline.md`

- [x] **Step 1: Create the baseline document**

Create `docs/tts-harness-safety-baseline.md` with these sections:

```markdown
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
```

- [x] **Step 2: Verify no placeholders**

Run:

```powershell
rg -n "TO[D]O|TB[D]|FIX[M]E" docs/tts-harness-safety-baseline.md
```

Expected: no matches.

## Task 4: Add Phase 0 QA Pathway

**Files:**
- Create: `docs/superpowers/qa/2026-06-23-tts-phase-0-safety-baseline-qa.md`

- [x] **Step 1: Create QA pathway**

Create a QA file with:

- scope and pass criteria;
- exact changed-file allowlist;
- local artifact ignore verification;
- placeholder and ASCII scans;
- protected artifact and credential scan;
- behavior-preservation verification;
- manual QA section for an independent reviewer using Computer Use to inspect TTS/War Organ
  availability without opening or committing raw saves;
- manual QA reporting must be boolean-only and must not include screenshots, raw file contents,
  copied metadata, full local paths, shortcut targets, Steam account details, TTS save names, or
  War Organ local data;
- explicit note that Browser QA is not required because Phase 0 changes no web UI.

- [x] **Step 2: Include manual QA commands/checks**

The manual QA section must instruct an independent reviewer to verify:

- TTS executable exists;
- TTS local `Mods` and `Saves` directories exist;
- Hutber and ForceOrg names appear in local TTS metadata;
- War Organ shortcut target exists;
- no raw save, screenshot, roster, or credential file is staged.

The manual QA output must be limited to pass/fail booleans and short blocker labels such as
`tts_executable_missing` or `war_organ_shortcut_missing`; it must not paste local filenames, full
paths, save names, metadata contents, screenshots, account details, or credential material into the
QA file or work log.

## Task 5: Record Work Log

**Files:**
- Modify: `docs/work-log/player-toolkit-implementation.md`

- [x] **Step 1: Append a factual Phase 0 entry**

Append a new section:

```markdown
## 2026-06-23 - TTS Phase 0 - Safety Baseline

Purpose:

- Prepare the TTS bridge and supervised self-play harness without runtime behavior changes.

Artifacts:

- `docs/superpowers/plans/2026-06-23-tts-phase-0-safety-baseline.md`
- `docs/tts-harness-safety-baseline.md`
- `docs/superpowers/qa/2026-06-23-tts-phase-0-safety-baseline-qa.md`
- `docs/superpowers/reviews/2026-06-23-tts-phase-0-consultant-plan.md`
- `docs/superpowers/reviews/2026-06-23-tts-phase-0-adversarial-plan.md`
- `docs/superpowers/reviews/2026-06-23-tts-phase-0-consultant-closeout.md`
- `docs/superpowers/reviews/2026-06-23-tts-phase-0-adversarial-closeout.md`
- `.gitignore`

Decisions:

- Phase 0 is docs and safety baseline only.
- Phase 1 owns Python TTS records, companion endpoints, and Lua bridge template work.
- Existing `CodexBackend` is auth/runtime-status infrastructure, not a self-play agent runner.
- `AGENTS.md` remains user-owned and unstaged.

Review plan:

- Consultant review checks sufficiency for Phase 1.
- Adversarial review checks overclaiming, artifact safety, and QA executability.

Verification:

- To be filled during execution.

Next loop trigger:

- Start Phase 0.5 TTS housekeeping semantics-preserving cleanup.
```

- [x] **Step 2: Update verification and review sections after reviews/checks**

Record actual reviewer outcomes, accepted fixes, command outputs, manual QA result, CodeRabbit
status, and commit id before closing the phase.

## Task 6: Plan Review Loop

**Files:**
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-0-consultant-plan.md`
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-0-adversarial-plan.md`
- Review: all Phase 0 planned artifacts

- [x] **Step 1: Consultant review**

Dispatch a consultant subagent to answer:

- Is the Phase 0 artifact set sufficient to start Phase 1 safely?
- Are any fixture/source/QA gates missing?
- Does the plan avoid premature runtime implementation?

Expected: PASS or concrete P0/P1 issues.

Record the outcome in `docs/superpowers/reviews/2026-06-23-tts-phase-0-consultant-plan.md`.

- [x] **Step 2: Adversarial review**

Dispatch an adversarial subagent to search for:

- accidental commitment paths for raw saves, rosters, PDFs, screenshots, generated logs, or
  credentials;
- overclaiming live TTS feasibility;
- missing manual QA instructions;
- ambiguity that blocks Phase 1.

Expected: PASS or concrete P0/P1 issues.

Record the outcome, P1s, fixes, and re-review status in
`docs/superpowers/reviews/2026-06-23-tts-phase-0-adversarial-plan.md`.

- [x] **Step 3: Triage and re-review**

For each P0/P1 issue:

- verify it against the repo;
- patch the plan/artifacts if accepted;
- record reasoning in the work log;
- resubmit to the same review focus until PASS.

## Task 7: Run Verification

**Files:**
- Verify: Phase 0 changed files

- [x] **Step 1: Run docs scans**

Run:

```powershell
$files=@(
  '.gitignore',
  'docs/tts-harness-safety-baseline.md',
  'docs/superpowers/plans/2026-06-23-tts-phase-0-safety-baseline.md',
  'docs/superpowers/qa/2026-06-23-tts-phase-0-safety-baseline-qa.md',
  'docs/work-log/player-toolkit-implementation.md'
)
$results = foreach ($file in $files) {
  $text=Get-Content -Raw -Path $file
  [pscustomobject]@{
    File=$file
    NonAscii=([regex]::Matches($text,'[^\x00-\x7F]')).Count
    Placeholders=([regex]::Matches($text,'TO[D]O|TB[D]|FIX[M]E')).Count
  }
}
$results | ConvertTo-Json
```

Expected: `NonAscii=0` and `Placeholders=0` for each file.

- [x] **Step 2: Run protected-path scan**

Run:

```powershell
git status --porcelain=v1
git diff --name-only
git diff --cached --name-only
```

Expected: only Phase 0 files plus untracked user-owned `AGENTS.md` are visible.

- [x] **Step 3: Run standard checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest tests\test_codex_backend.py -q
```

Expected: all pass. Full pytest is optional for docs-only Phase 0 if already fresh; if run, record
the result.

- [x] **Step 4: Execute manual QA pathway**

Run the non-invasive shell checks from the QA file. Do not launch TTS or War Organ in Phase 0 unless
the reviewer explicitly requests visible Computer Use verification. Record the result.

## Task 8: Code Review And Commit

**Files:**
- Stage only Phase 0 files

- [x] **Step 1: Run CodeRabbit if available**

Run:

```powershell
coderabbit --version
coderabbit auth status --agent
coderabbit review --agent -t uncommitted
```

Expected: CodeRabbit review completes or a precise install/auth blocker is recorded. Do not present
manual review as CodeRabbit.

- [x] **Step 2: Stage exact files**

Run:

```powershell
git add -- .gitignore docs/tts-harness-safety-baseline.md docs/superpowers/plans/2026-06-23-tts-phase-0-safety-baseline.md docs/superpowers/qa/2026-06-23-tts-phase-0-safety-baseline-qa.md docs/superpowers/reviews/2026-06-23-tts-phase-0-consultant-plan.md docs/superpowers/reviews/2026-06-23-tts-phase-0-adversarial-plan.md docs/superpowers/reviews/2026-06-23-tts-phase-0-consultant-closeout.md docs/superpowers/reviews/2026-06-23-tts-phase-0-adversarial-closeout.md docs/work-log/player-toolkit-implementation.md
git diff --cached --name-only
```

Expected: exactly those nine files. `AGENTS.md` is not staged.

- [x] **Step 3: Commit Phase 0**

Run:

```powershell
git commit -m "Add TTS phase 0 safety baseline"
```

Expected: one atomic Phase 0 commit.

- [x] **Step 4: Post-commit proof**

Run:

```powershell
git status -sb
git show --stat --oneline --name-only HEAD
```

Expected: only user-owned untracked `AGENTS.md` remains visible.
