# Phase 1.5 Housekeeping Source Foundation QA Pathway

Date: 2026-06-20

## Purpose

Prove Phase 1.5 is behavior-preserving and only tightens the test helper type contract around the
Phase 1 remote verifier.

## Required Checks

```powershell
$allowedPhase15 = @(
  'docs/superpowers/plans/2026-06-20-phase-1-5-housekeeping-source-foundation.md',
  'docs/superpowers/qa/2026-06-20-phase-1-5-housekeeping-source-foundation-qa.md',
  'docs/superpowers/reviews/2026-06-20-phase-1-5-adversarial-source-foundation.md',
  'docs/superpowers/reviews/2026-06-20-phase-1-5-consultant-source-foundation.md',
  'docs/superpowers/specs/2026-06-20-phase-1-5-housekeeping-source-foundation.md',
  'docs/work-log/player-toolkit-implementation.md',
  'tests/test_rules_sources.py'
)
$allowedUserOwnedUntracked = @('AGENTS.md')
$modified = @(git diff --name-only)
$staged = @(git diff --cached --name-only)
$untracked = @(git ls-files --others --exclude-standard)
$allVisible = @($modified + $staged + $untracked) |
  Where-Object { $_ } |
  Sort-Object -Unique
$unexpected = $allVisible | Where-Object {
  ($_ -notin $allowedPhase15) -and ($_ -notin $allowedUserOwnedUntracked)
}
if ($unexpected) { throw "Unexpected changed/untracked files: $($unexpected -join ', ')" }
if ($staged -contains 'AGENTS.md') { throw 'AGENTS.md is user-owned and must not be staged' }

.\.venv\Scripts\python.exe -m pytest tests\test_rules_sources.py -q
.\.venv\Scripts\mypy.exe tests\test_rules_sources.py
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
git diff --check
```

Expected: all commands pass, and the diff is limited to Phase 1.5 docs plus the
`_fake_get_factory()` type cleanup.

## Browser And Computer Use

Not required. This slice changes no runtime, web, desktop, packaged, or visual behavior.
