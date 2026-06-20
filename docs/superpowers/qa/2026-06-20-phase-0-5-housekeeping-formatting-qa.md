# Phase 0.5 Housekeeping Formatting QA Pathway

Date: 2026-06-20

## Purpose

Prove that Phase 0.5 only applies behavior-preserving Ruff formatting cleanup and leaves the app
ready for Phase 1.

## Preconditions

- Working directory: the Codex-provided repository root. Verify with `Resolve-Path .`.
- Branch: `codex/assistant-companion-roadmap`.
- Prior checkpoint: commit `3fd9d94 Add phase 0 implementation readiness`.
- User-owned `AGENTS.md` may be untracked; it must not be staged.

## Required Artifacts

Run:

```powershell
$paths = @(
  'docs\superpowers\specs\2026-06-20-phase-0-5-housekeeping-formatting-design.md',
  'docs\superpowers\plans\2026-06-20-phase-0-5-housekeeping-formatting.md',
  'docs\superpowers\qa\2026-06-20-phase-0-5-housekeeping-formatting-qa.md',
  'docs\superpowers\reviews\2026-06-20-phase-0-5-consultant-housekeeping.md',
  'docs\superpowers\reviews\2026-06-20-phase-0-5-adversarial-housekeeping.md',
  'docs\work-log\player-toolkit-implementation.md',
  'src\warhammer_companion\los\geometry.py'
)
foreach ($path in $paths) {
  if (-not (Test-Path $path)) { throw "Missing Phase 0.5 artifact: $path" }
}
```

Expected: command exits with no error.

## Review Approval Evidence

Phase 0.5 requires:

- One consultant approval for scope and handoff readiness.
- One adversarial approval for behavior preservation, source-trust, and QA executability.

Record final approvals in:

- `docs/superpowers/reviews/2026-06-20-phase-0-5-consultant-housekeeping.md`
- `docs/superpowers/reviews/2026-06-20-phase-0-5-adversarial-housekeeping.md`
- `docs/work-log/player-toolkit-implementation.md`

## Static Checks

### 1. Worktree And Allowlist Check

Run:

```powershell
Resolve-Path .
git status --short --branch --untracked-files=all
$allowedPhase05 = @(
  'docs/superpowers/plans/2026-06-20-phase-0-5-housekeeping-formatting.md',
  'docs/superpowers/qa/2026-06-20-phase-0-5-housekeeping-formatting-qa.md',
  'docs/superpowers/reviews/2026-06-20-phase-0-5-adversarial-housekeeping.md',
  'docs/superpowers/reviews/2026-06-20-phase-0-5-consultant-housekeeping.md',
  'docs/superpowers/specs/2026-06-20-phase-0-5-housekeeping-formatting-design.md',
  'docs/work-log/player-toolkit-implementation.md',
  'src/warhammer_companion/los/geometry.py'
)
$allowedUserOwnedUntracked = @('AGENTS.md')
$modified = @(git diff --name-only)
$staged = @(git diff --cached --name-only)
$untracked = @(git ls-files --others --exclude-standard)
$allVisible = @($modified + $staged + $untracked) |
  Where-Object { $_ } |
  Sort-Object -Unique
$unexpected = $allVisible | Where-Object {
  ($_ -notin $allowedPhase05) -and ($_ -notin $allowedUserOwnedUntracked)
}
if ($unexpected) { throw "Unexpected changed/untracked files: $($unexpected -join ', ')" }
if ($staged -contains 'AGENTS.md') { throw 'AGENTS.md is user-owned and must not be staged' }
```

Expected: only Phase 0.5 files and user-owned untracked `AGENTS.md` are visible.

### 2. Draft-Marker And ASCII Checks

Run:

```powershell
$pattern = ('TB' + 'D|TO' + 'DO|FIX' + 'ME|\?\?')
Select-String -Path docs\superpowers\specs\2026-06-20-phase-0-5-housekeeping-formatting-design.md,docs\superpowers\plans\2026-06-20-phase-0-5-housekeeping-formatting.md,docs\superpowers\qa\2026-06-20-phase-0-5-housekeeping-formatting-qa.md,docs\superpowers\reviews\2026-06-20-phase-0-5-consultant-housekeeping.md,docs\superpowers\reviews\2026-06-20-phase-0-5-adversarial-housekeeping.md,docs\work-log\player-toolkit-implementation.md -Pattern $pattern

$paths = @(
  'docs\superpowers\specs\2026-06-20-phase-0-5-housekeeping-formatting-design.md',
  'docs\superpowers\plans\2026-06-20-phase-0-5-housekeeping-formatting.md',
  'docs\superpowers\qa\2026-06-20-phase-0-5-housekeeping-formatting-qa.md',
  'docs\superpowers\reviews\2026-06-20-phase-0-5-consultant-housekeeping.md',
  'docs\superpowers\reviews\2026-06-20-phase-0-5-adversarial-housekeeping.md',
  'docs\work-log\player-toolkit-implementation.md',
  'src\warhammer_companion\los\geometry.py'
)
foreach ($path in $paths) {
  $content = Get-Content -LiteralPath $path -Raw
  $matches = [regex]::Matches($content, '[^\x00-\x7F]')
  if ($matches.Count -gt 0) { "$path has non-ASCII" }
}
```

Expected: no draft-marker matches and no non-ASCII findings.

### 3. Diff And Formatter Checks

Run:

```powershell
git diff --check
.\.venv\Scripts\python.exe -m ruff format --check src tests
git diff -- src\warhammer_companion\los\geometry.py
```

Expected:

- `git diff --check` has no whitespace errors.
- Ruff reports all files already formatted.
- The geometry diff is formatter-only.

## Behavioral Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
```

Expected:

- Ruff check passes.
- mypy passes.
- pytest passes.
- All 45 official seed packets validate.
- Desktop smoke returns status `ok`.

## Browser And Computer Use

Browser and Computer Use checks are not required for Phase 0.5 because it changes no web, desktop,
packaged, or runtime behavior. Later phases must use them when their runtime surfaces change.

## Pass Criteria

Phase 0.5 passes only if:

- Required artifacts exist.
- Ruff formatting check passes.
- Source diff is formatter-only.
- Behavioral verification passes.
- Consultant and adversarial reviewers approve.
- `AGENTS.md` remains unstaged.
- Phase 0.5 is committed atomically.
