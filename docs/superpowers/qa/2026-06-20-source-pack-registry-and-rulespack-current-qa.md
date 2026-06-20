# Source Pack Registry And Current RulesPack QA Pathway

Date: 2026-06-20

## Purpose

Prove Phase 1 adds a metadata-only source/rules foundation and does not redistribute protected
rules, mission, datasheet, roster, or community-pack content.

## Required Artifacts

```powershell
$paths = @(
  'src\warhammer_companion\ingestion\rules_sources.py',
  'tests\test_rules_sources.py',
  'docs\superpowers\specs\2026-06-20-source-pack-registry-and-rulespack-current-spec.md',
  'docs\superpowers\plans\2026-06-20-source-pack-registry-and-rulespack-current.md',
  'docs\superpowers\qa\2026-06-20-source-pack-registry-and-rulespack-current-qa.md',
  'docs\superpowers\reviews\2026-06-20-phase-1-consultant-source-foundation.md',
  'docs\superpowers\reviews\2026-06-20-phase-1-adversarial-source-foundation.md',
  'docs\work-log\player-toolkit-implementation.md'
)
foreach ($path in $paths) {
  if (-not (Test-Path $path)) { throw "Missing Phase 1 artifact: $path" }
}
```

Expected: command exits with no error.

## Source Freshness Evidence

Record current-source evidence in the work log:

- Warhammer Community downloads page MFM updated date.
- MFM upstream version.
- Core rules PDF candidate URL.
- New Recruit/BattleScribe/BSData trust boundary.

No source text, PDFs, sheets, images, roster data, or community data may be committed.

## Review Evidence

Phase 1 requires:

- Consultant approval for source freshness and architecture fit.
- Adversarial approval for source-trust/IP/security, no redistribution, and QA adequacy.

Approvals are recorded in:

- `docs/superpowers/reviews/2026-06-20-phase-1-consultant-source-foundation.md`
- `docs/superpowers/reviews/2026-06-20-phase-1-adversarial-source-foundation.md`
- `docs/work-log/player-toolkit-implementation.md`

## Static Checks

### 1. Changed-File Allowlist

```powershell
$allowedPhase1 = @(
  'docs/superpowers/plans/2026-06-20-source-pack-registry-and-rulespack-current.md',
  'docs/superpowers/qa/2026-06-20-source-pack-registry-and-rulespack-current-qa.md',
  'docs/superpowers/reviews/2026-06-20-phase-1-adversarial-source-foundation.md',
  'docs/superpowers/reviews/2026-06-20-phase-1-consultant-source-foundation.md',
  'docs/superpowers/specs/2026-06-20-source-pack-registry-and-rulespack-current-spec.md',
  'docs/work-log/player-toolkit-implementation.md',
  'src/warhammer_companion/ingestion/rules_sources.py',
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
  ($_ -notin $allowedPhase1) -and ($_ -notin $allowedUserOwnedUntracked)
}
if ($unexpected) { throw "Unexpected changed/untracked files: $($unexpected -join ', ')" }
if ($staged -contains 'AGENTS.md') { throw 'AGENTS.md is user-owned and must not be staged' }
```

Expected: only Phase 1 files and user-owned untracked `AGENTS.md` are visible.

### 2. Draft, ASCII, And Secret Checks

```powershell
$pattern = ('TB' + 'D|TO' + 'DO|FIX' + 'ME|\?\?')
Select-String -Path docs\superpowers\specs\2026-06-20-source-pack-registry-and-rulespack-current-spec.md,docs\superpowers\plans\2026-06-20-source-pack-registry-and-rulespack-current.md,docs\superpowers\qa\2026-06-20-source-pack-registry-and-rulespack-current-qa.md,docs\superpowers\reviews\2026-06-20-phase-1-consultant-source-foundation.md,docs\superpowers\reviews\2026-06-20-phase-1-adversarial-source-foundation.md,docs\work-log\player-toolkit-implementation.md,src\warhammer_companion\ingestion\rules_sources.py,tests\test_rules_sources.py -Pattern $pattern

$paths = @(
  'docs\superpowers\specs\2026-06-20-source-pack-registry-and-rulespack-current-spec.md',
  'docs\superpowers\plans\2026-06-20-source-pack-registry-and-rulespack-current.md',
  'docs\superpowers\qa\2026-06-20-source-pack-registry-and-rulespack-current-qa.md',
  'docs\superpowers\reviews\2026-06-20-phase-1-consultant-source-foundation.md',
  'docs\superpowers\reviews\2026-06-20-phase-1-adversarial-source-foundation.md',
  'docs\work-log\player-toolkit-implementation.md',
  'src\warhammer_companion\ingestion\rules_sources.py',
  'tests\test_rules_sources.py'
)
foreach ($path in $paths) {
  $content = Get-Content -LiteralPath $path -Raw
  $matches = [regex]::Matches($content, '[^\x00-\x7F]')
  if ($matches.Count -gt 0) { "$path has non-ASCII" }
}

$secretPattern = '(api[_-]?key|bearer\s+[A-Za-z0-9._-]+|sk-[A-Za-z0-9]{16,}|token\s*[:=]|secret\s*[:=]|password\s*[:=])'
Select-String -CaseSensitive -Path $paths -Pattern $secretPattern
```

Expected: no matches.

### 3. Protected-Content Guard

```powershell
Select-String -Path src\warhammer_companion\ingestion\rules_sources.py,tests\test_rules_sources.py -Pattern 'Datasheet|Stratagem|At the start|Until the end|roll one|roll a D6|invulnerable save|wound roll|saving throw'
```

Expected: no matches. Labels such as `Core Rules`, `Munitorum Field Manual`, `BattleScribe`, and
concept IDs are allowed; copied mechanics prose is not.

## Functional Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_rules_sources.py -q
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m warhammer_companion.cli validate-packets --packet-dir src\warhammer_companion\seed_data\map-packets
.\.venv\Scripts\python.exe -m warhammer_companion.desktop.app --smoke-test
git diff --check
```

Expected: all commands pass.

## Browser And Computer Use

Browser and Computer Use checks are not required for Phase 1 because this slice adds source/rules
metadata primitives and tests but no web, desktop, packaged, or runtime UI behavior.

## Pass Criteria

Phase 1 passes only if:

- Required artifacts exist.
- Current-source freshness evidence is recorded.
- Tests prove source metadata, readiness, source-pending concepts, and legacy assumption blockers.
- Tests prove remote verification streams bytes and computes SHA-256 through an injected fake
  response without live network access.
- Tests prove remote verification blocks non-200 responses, unsafe initial URLs, unsafe redirects,
  empty content, and missing content type.
- Tests prove mutable MFM freshness is `unknown` unless a refresh timestamp is supplied.
- Tests prove no initial concept is `trusted`.
- Protected-content guard passes.
- Consultant and adversarial reviewers approve.
- Verification commands pass.
- Phase 1 is committed atomically.
