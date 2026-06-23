# TTS Phase 0.5 Housekeeping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply behavior-preserving documentation housekeeping after TTS Phase 0.

**Architecture:** Phase 0.5 changes no runtime behavior. It cleans the Phase 0 documentation set so
the completed plan, QA allowlist, and work log are easier for later reviewers to use, then reruns
the Phase 0 safety checks to prove no guardrail regression.

**Tech Stack:** Markdown docs, PowerShell verification, existing Python checks, consultant and
adversarial subagent review, CodeRabbit when available.

---

## Scope

Allowed changes:

- Update Phase 0 plan task checkboxes to reflect completed work.
- Break very long shell command lines in docs into readable PowerShell continuations where behavior
  is unchanged.
- Add a short Phase 0.5 work-log entry with review and verification evidence.
- Add Phase 0.5 review records if reviewers require durable records.

Forbidden changes:

- No production Python, Lua, web, desktop, package, or fixture behavior.
- No changes to TTS artifact policy semantics.
- No new generated data, raw saves, raw rosters, screenshots, PDFs, credentials, Codex/OpenAI state,
  Steam state, or War Organ local data.
- Do not stage `AGENTS.md`.

## File Map

- Modify: `docs/superpowers/plans/2026-06-23-tts-phase-0-safety-baseline.md`
  - Mark completed Phase 0 steps and improve readability of long commands without changing meaning.
- Modify: `docs/superpowers/qa/2026-06-23-tts-phase-0-safety-baseline-qa.md`
  - Improve readability of long commands without changing meaning.
- Modify: `docs/work-log/player-toolkit-implementation.md`
  - Add Phase 0.5 entry.
- Modify: this plan file
  - Current untracked Phase 0.5 plan artifact to commit after review.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-0-5-consultant-housekeeping.md`
  - Consultant review record.
- Create: `docs/superpowers/reviews/2026-06-23-tts-phase-0-5-adversarial-housekeeping.md`
  - Adversarial review and triage record.

## Task 1: Preflight

- [ ] **Step 1: Confirm starting state**

Run:

```powershell
git status -sb
git show --stat --oneline --name-only HEAD
```

Expected: branch is `codex/assistant-companion-roadmap`, Phase 0 commit is current, and only
user-owned untracked `AGENTS.md` plus this Phase 0.5 plan file are visible before the rest of the
Phase 0.5 edits.

## Task 2: Documentation Housekeeping

- [ ] **Step 1: Mark Phase 0 plan steps complete**

In `docs/superpowers/plans/2026-06-23-tts-phase-0-safety-baseline.md`, change only executed
checkboxes from `- [ ]` to `- [x]`.

- [ ] **Step 2: Wrap long command lines**

In the Phase 0 plan and QA file, wrap the `git check-ignore` command into a PowerShell array plus
`git check-ignore @paths`. Preserve the exact path list and expected output semantics.

- [ ] **Step 3: Verify no semantic drift**

Run:

```powershell
rg -n "data/tts|data/tts-harness|data/tts-saves|data/tts-screenshots|data/snapshots|data/replays|data/rosters/raw|data/steam-state|data/war-organ|data/codex-state|data/openai-state|logs/tts-harness.log|data/codex-home/auth.json|\\.env.local" docs/superpowers/plans/2026-06-23-tts-phase-0-safety-baseline.md docs/superpowers/qa/2026-06-23-tts-phase-0-safety-baseline-qa.md
```

Expected: all protected example paths remain present.

## Task 3: Reviews

- [ ] **Step 1: Consultant review**

Ask a consultant subagent whether the housekeeping is semantics-preserving and whether Phase 1
readiness remains intact.

Expected: PASS or concrete P0/P1 issues.

- [ ] **Step 2: Adversarial review**

Ask an adversarial subagent to look for behavior drift, weakened protected-artifact gates, staging
risks, or overclaiming.

Expected: PASS or concrete P0/P1 issues.

- [ ] **Step 3: Triage and re-review**

Patch accepted P0/P1 issues, record reasoning, and resubmit until both reviews pass.

## Task 4: Verification

- [ ] **Step 1: Run Phase 0 ignore verification**

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

Expected: every path is printed.

- [ ] **Step 2: Run docs scans**

Run:

```powershell
$files=@(
  'docs/superpowers/plans/2026-06-23-tts-phase-0-safety-baseline.md',
  'docs/superpowers/qa/2026-06-23-tts-phase-0-safety-baseline-qa.md',
  'docs/superpowers/plans/2026-06-23-tts-phase-0-5-housekeeping.md',
  'docs/superpowers/reviews/2026-06-23-tts-phase-0-5-consultant-housekeeping.md',
  'docs/superpowers/reviews/2026-06-23-tts-phase-0-5-adversarial-housekeeping.md',
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

Expected: `NonAscii=0` and `Placeholders=0`.

- [ ] **Step 3: Run standard checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest tests\test_codex_backend.py -q
```

Expected: all pass.

- [ ] **Step 4: Run protected-path scan**

Run:

```powershell
git status --porcelain=v1
git diff --name-only
git diff --cached --name-only
```

Expected: only Phase 0.5 docs and user-owned untracked `AGENTS.md` are visible.

## Task 5: Commit

- [ ] **Step 1: Attempt CodeRabbit**

Run:

```powershell
coderabbit --version
coderabbit auth status --agent
coderabbit review --agent -t uncommitted
```

Expected: CodeRabbit review completes or exact install/auth/system blocker is logged. Do not present
manual review as CodeRabbit output.

- [ ] **Step 2: Stage exact files**

Run:

```powershell
git add -- docs/superpowers/plans/2026-06-23-tts-phase-0-safety-baseline.md docs/superpowers/qa/2026-06-23-tts-phase-0-safety-baseline-qa.md docs/superpowers/plans/2026-06-23-tts-phase-0-5-housekeeping.md docs/superpowers/reviews/2026-06-23-tts-phase-0-5-consultant-housekeeping.md docs/superpowers/reviews/2026-06-23-tts-phase-0-5-adversarial-housekeeping.md docs/work-log/player-toolkit-implementation.md
git diff --cached --name-only
```

Expected: exactly those six files. `AGENTS.md` is not staged.

- [ ] **Step 3: Commit Phase 0.5**

Run:

```powershell
git commit -m "Housekeep TTS phase 0 docs"
```

Expected: one atomic housekeeping commit.

## Next Loop Trigger

Start Phase 1 TTS feasibility harness.
