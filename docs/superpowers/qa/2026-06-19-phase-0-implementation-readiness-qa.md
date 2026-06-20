# Phase 0 Implementation Readiness QA Pathway

Date: 2026-06-19

## Purpose

This QA pathway proves Phase 0 is ready to hand off to Phase 1. It is written so a fresh subagent can execute it without hidden conversation context.

Phase 0 is documentation scaffolding only. It should not change product behavior.

## Preconditions

- Working directory: the Codex-provided repository root. Verify with `Resolve-Path .`; on this
  Windows checkout it normalizes to `C:\Users\Conferences and AI\Documents\Warhammer tournament companion`.
- Branch: `codex/assistant-companion-roadmap`
- Required repo instruction file: `AGENTS.md`
- Parent roadmap: `docs/superpowers/specs/2026-06-19-player-toolkit-assistant-roadmap-design.md`

## Required Artifacts

The following files must exist:

- `docs/superpowers/specs/2026-06-19-phase-0-implementation-readiness-design.md`
- `docs/superpowers/plans/2026-06-19-phase-0-implementation-readiness.md`
- `docs/superpowers/qa/2026-06-19-phase-0-implementation-readiness-qa.md`
- `docs/superpowers/reviews/2026-06-19-phase-0-consultant-readiness.md`
- `docs/superpowers/reviews/2026-06-19-phase-0-adversarial-readiness.md`
- `docs/work-log/player-toolkit-implementation.md`
- `docs/qa-scenarios.md`

Run:

```powershell
$paths = @(
  'docs\superpowers\specs\2026-06-19-phase-0-implementation-readiness-design.md',
  'docs\superpowers\plans\2026-06-19-phase-0-implementation-readiness.md',
  'docs\superpowers\qa\2026-06-19-phase-0-implementation-readiness-qa.md',
  'docs\superpowers\reviews\2026-06-19-phase-0-consultant-readiness.md',
  'docs\superpowers\reviews\2026-06-19-phase-0-adversarial-readiness.md',
  'docs\work-log\player-toolkit-implementation.md',
  'docs\qa-scenarios.md'
)
foreach ($path in $paths) {
  if (-not (Test-Path $path)) { throw "Missing required artifact: $path" }
}
```

Expected: command exits with no error.

## Preflight Checks

Run:

```powershell
Resolve-Path .
Test-Path AGENTS.md
Test-Path docs\superpowers\specs\2026-06-19-player-toolkit-assistant-roadmap-design.md
Test-Path docs\qa-scenarios.md
git status --short --branch --untracked-files=all
git diff --name-only
git diff --cached --name-only
git ls-files --others --exclude-standard
git diff --check
```

Expected:

- `Resolve-Path .` points at the Warhammer tournament companion repository root.
- All `Test-Path` commands return `True`.
- Current branch is `codex/assistant-companion-roadmap`.
- Diff is limited to Phase 0 documentation files.
- Untracked files are limited to intended Phase 0 files plus user-owned `AGENTS.md`.
- `git diff --check` reports no whitespace errors.

## Review Approval Evidence

Phase 0 requires at least:

- One consultant subagent approval.
- One adversarial subagent approval.

Reviewer prompts must require either `APPROVED` or `CHANGES_REQUIRED`. If any reviewer returns `CHANGES_REQUIRED`, the fix must be patched and re-reviewed until approved.

Evidence to record in `docs/work-log/player-toolkit-implementation.md`:

- Reviewer role.
- Final status.
- Blocking findings fixed.
- Nonblocking notes deferred.
- Review record path under `docs/superpowers/reviews/`.

## Static Documentation Checks

### 1. Worktree Check

Run:

```powershell
git status --short --branch --untracked-files=all
```

Expected:

- Current branch is visible.
- Only intended Phase 0 files are modified or staged for the Phase 0 commit.
- User-owned untracked files, such as a newly supplied `AGENTS.md`, are not staged unless explicitly intended.

### 2. Draft-Marker Check

Run:

```powershell
$pattern = ('TB' + 'D|TO' + 'DO|FIX' + 'ME|\?\?')
Select-String -Path docs\superpowers\specs\2026-06-19-phase-0-implementation-readiness-design.md,docs\superpowers\plans\2026-06-19-phase-0-implementation-readiness.md,docs\superpowers\qa\2026-06-19-phase-0-implementation-readiness-qa.md,docs\superpowers\reviews\2026-06-19-phase-0-consultant-readiness.md,docs\superpowers\reviews\2026-06-19-phase-0-adversarial-readiness.md,docs\work-log\player-toolkit-implementation.md,docs\qa-scenarios.md -Pattern $pattern
```

Expected: no matches.

### 3. ASCII Check

Run:

```powershell
$paths = @(
  'docs\superpowers\specs\2026-06-19-phase-0-implementation-readiness-design.md',
  'docs\superpowers\plans\2026-06-19-phase-0-implementation-readiness.md',
  'docs\superpowers\qa\2026-06-19-phase-0-implementation-readiness-qa.md',
  'docs\superpowers\reviews\2026-06-19-phase-0-consultant-readiness.md',
  'docs\superpowers\reviews\2026-06-19-phase-0-adversarial-readiness.md',
  'docs\work-log\player-toolkit-implementation.md',
  'docs\qa-scenarios.md'
)
foreach ($path in $paths) {
  $content = Get-Content -LiteralPath $path -Raw
  $matches = [regex]::Matches($content, '[^\x00-\x7F]')
  if ($matches.Count -gt 0) { "$path has non-ASCII" }
}
```

Expected: no output.

### 4. Markdown Content Check

Run:

```powershell
Select-String -Path docs\superpowers\specs\2026-06-19-phase-0-implementation-readiness-design.md -Pattern 'Phase Execution Protocol|Housekeeping Protocol|Acceptance Criteria|Handoff To Phase 1'
Select-String -Path docs\superpowers\plans\2026-06-19-phase-0-implementation-readiness.md -Pattern 'REQUIRED SUB-SKILL|Task 1|Task 8|git commit'
Select-String -Path docs\superpowers\qa\2026-06-19-phase-0-implementation-readiness-qa.md -Pattern 'Review Approval Evidence|Browser And Computer Use|Reusable QA Template'
Select-String -Path docs\superpowers\reviews\2026-06-19-phase-0-consultant-readiness.md -Pattern 'Consultant Review|Final Status|Triage'
Select-String -Path docs\superpowers\reviews\2026-06-19-phase-0-adversarial-readiness.md -Pattern 'Adversarial Review|Final Status|Triage'
Select-String -Path docs\work-log\player-toolkit-implementation.md -Pattern 'Phase 0 - Implementation Readiness|Artifacts|Verification|Review Gates'
Select-String -Path docs\qa-scenarios.md -Pattern 'Roadmap Phase QA|phase-specific QA pathway|adversarial review'
```

Expected: each command returns matching lines.

### 5. Diff Whitespace Check

Run:

```powershell
git diff --check
git diff --cached --check
```

Expected: no whitespace errors.

### 6. Behavior-Preservation Check

Run:

```powershell
$allowedPhase0 = @(
  'docs/qa-scenarios.md',
  'docs/superpowers/plans/2026-06-19-phase-0-implementation-readiness.md',
  'docs/superpowers/qa/2026-06-19-phase-0-implementation-readiness-qa.md',
  'docs/superpowers/reviews/2026-06-19-phase-0-adversarial-readiness.md',
  'docs/superpowers/reviews/2026-06-19-phase-0-consultant-readiness.md',
  'docs/superpowers/specs/2026-06-19-phase-0-implementation-readiness-design.md',
  'docs/work-log/player-toolkit-implementation.md'
)
$allowedUserOwnedUntracked = @('AGENTS.md')
$modified = @(git diff --name-only)
$staged = @(git diff --cached --name-only)
$untracked = @(git ls-files --others --exclude-standard)
$allVisible = @($modified + $staged + $untracked) |
  Where-Object { $_ } |
  Sort-Object -Unique
$unexpected = $allVisible | Where-Object {
  ($_ -notin $allowedPhase0) -and ($_ -notin $allowedUserOwnedUntracked)
}
if ($unexpected) { throw "Unexpected changed/untracked files: $($unexpected -join ', ')" }
if ($staged -contains 'AGENTS.md') { throw 'AGENTS.md is user-owned and must not be staged' }
```

Expected: only the Phase 0 documentation allowlist is changed or staged. `AGENTS.md` may remain
untracked and user-owned, but must not be staged. No files under `src/`, `tests/`, `data/`,
`build/`, `dist/`, or `logs/` should appear.

### 7. AGENTS Compliance Check

Run:

```powershell
$modified = @(git diff --name-only)
$staged = @(git diff --cached --name-only)
$untracked = @(git ls-files --others --exclude-standard)
$allVisible = @($modified + $staged + $untracked) |
  Where-Object { $_ } |
  Sort-Object -Unique
$newJsTs = $allVisible | Where-Object { $_ -match '\.(js|jsx|ts|tsx)$' }
$generated = $allVisible | Where-Object { $_ -match '^(data|build|dist|logs)/' }
if ($newJsTs) { throw "JavaScript/TypeScript files are not allowed in Phase 0: $($newJsTs -join ', ')" }
if ($generated) { throw "Generated/local data files are not allowed in Phase 0: $($generated -join ', ')" }
$secretPattern = '(api[_-]?key|bearer\s+[A-Za-z0-9._-]+|sk-[A-Za-z0-9]{16,}|token\s*[:=]|secret\s*[:=]|password\s*[:=])'
$secretMatches = Select-String -CaseSensitive -Path docs\superpowers\specs\2026-06-19-phase-0-implementation-readiness-design.md,docs\superpowers\plans\2026-06-19-phase-0-implementation-readiness.md,docs\superpowers\qa\2026-06-19-phase-0-implementation-readiness-qa.md,docs\superpowers\reviews\2026-06-19-phase-0-consultant-readiness.md,docs\superpowers\reviews\2026-06-19-phase-0-adversarial-readiness.md,docs\work-log\player-toolkit-implementation.md,docs\qa-scenarios.md -Pattern $secretPattern
if ($secretMatches) { throw "Potential secret material found: $($secretMatches -join '; ')" }
```

Expected:

- The diff remains documentation-only.
- No new JavaScript or TypeScript source files appear.
- No generated files under `data/`, `build/`, `dist/`, or `logs/` are part of Phase 0.
- No credential or secret-like values are present.

### 8. No Behavior Baseline

Because Phase 0 changes only documentation, the diff-based behavior-preservation check is the primary proof.
If the project virtual environment exists, run the standard baseline commands as an additional guard:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Expected: commands pass if the environment and seed data are present. If `.venv` or seed data is
missing, record the blocker in the work log; this does not block Phase 0 when the diff confirms no
runtime, data, package, web, or desktop files changed.

If an optional baseline command fails against untouched runtime files, record the exact command,
affected files, and output summary in the work log. Do not auto-fix source files inside the
docs-only Phase 0 checkpoint. Defer behavior-preserving cleanup to the next `.5` housekeeping loop
unless reviewers determine the failure blocks Phase 0 readiness.

## Browser And Computer Use

Phase 0 does not add or modify runtime behavior, so Browser and Computer Use checks are not required to prove Phase 0.

Optional confidence path if a reviewer requests UI proof despite the docs-only scope:

1. Launch the existing web app with `.\.venv\Scripts\python.exe -m warhammer_companion.app`.
2. Use Browser to open `http://127.0.0.1:8000`.
3. Verify Settings, Map Data, Map Viewer, LOS Heatmap, and LOS Checker still load.
4. Verify page 9 and page 52 render where seed or generated packets exist.
5. Record that this was an unchanged-baseline smoke check, not proof of new Phase 0 behavior.

For later phases:

- Use Browser checks when web routes, rendered maps, controls, or layout behavior change.
- Use Computer Use checks when native Windows desktop behavior, installer behavior, OS dialogs, or packaged app interactions change.
- Record target URL, route, viewport/window, console errors, DOM or pixel assertions, and screenshots when available.

## Reusable QA Template For Later Phases

Each later phase QA file should include:

1. Phase objective and scope.
2. Preconditions and required local data.
3. Required artifacts.
4. Reviewer approval evidence.
5. Unit and integration commands with expected outputs.
6. Source-trust, freshness/source-refresh, and readiness-state checks for mutable official,
   public-sheet, MFM, roster, mission-pack, or community-pack data.
7. Browser checks for web-facing behavior.
8. Computer Use checks for desktop/packaged behavior.
9. Regression checks against page 9 and page 52 when map overlays are involved.
10. Work-log evidence requirements.
11. Commit/staging checks.

## Phase 0 Pass Criteria

Phase 0 passes only if:

- All required artifacts exist.
- Consultant and adversarial reviewers approve after any fixes.
- Static checks pass.
- Behavior-preservation check shows no production code or generated data changes.
- Work log records decisions, review outcomes, verification, and remaining nonblocking notes.
- Phase 0 artifacts are committed atomically.
