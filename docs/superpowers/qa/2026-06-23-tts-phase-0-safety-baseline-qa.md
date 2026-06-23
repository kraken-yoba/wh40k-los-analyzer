# TTS Phase 0 Safety Baseline QA Pathway

Date: 2026-06-23

## Scope

Phase 0 is behavior-preserving. It adds documentation and ignore rules for the TTS bridge and
supervised self-play harness baseline. It must not add production Python, Lua, web, desktop,
packaging, generated data, raw saves, raw rosters, screenshots, or credentials.

## Changed-File Allowlist

Only these files may be changed or staged for Phase 0:

- `.gitignore`
- `docs/tts-harness-safety-baseline.md`
- `docs/superpowers/plans/2026-06-23-tts-phase-0-safety-baseline.md`
- `docs/superpowers/qa/2026-06-23-tts-phase-0-safety-baseline-qa.md`
- `docs/superpowers/reviews/2026-06-23-tts-phase-0-consultant-plan.md`
- `docs/superpowers/reviews/2026-06-23-tts-phase-0-adversarial-plan.md`
- `docs/superpowers/reviews/2026-06-23-tts-phase-0-consultant-closeout.md`
- `docs/superpowers/reviews/2026-06-23-tts-phase-0-adversarial-closeout.md`
- `docs/work-log/player-toolkit-implementation.md`

`AGENTS.md` may remain untracked and must not be staged unless the user explicitly requests it.

## Artifact Ignore Verification

Run:

```powershell
git check-ignore data/tts/example.json data/tts-harness/example.json data/tts-saves/example.json data/tts-screenshots/example.png data/snapshots/example.json data/replays/example.json data/rosters/raw/example.rosz data/steam-state/example.json data/war-organ/example.json data/codex-state/auth.json data/openai-state/session.json logs/tts-harness.log data/codex-home/auth.json .env.local
```

Expected: every path is printed.

## Placeholder And ASCII Scan

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

## Protected Artifact Scan

Run:

```powershell
git status --porcelain=v1
git diff --name-only
git diff --cached --name-only
```

Expected: only Phase 0 allowlisted files are modified or staged. `AGENTS.md` may appear only as an
untracked user-owned file.

Reject any staged or modified path under generated/raw/cache locations except `.gitignore`
patterns. Reject raw TTS saves, raw rosters, official PDFs, screenshots, generated snapshots,
generated replay logs, Codex/OpenAI state, Steam state, War Organ local data, and credentials.

## Standard Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest tests\test_codex_backend.py -q
```

Expected: all commands pass. Full pytest may be run as an unchanged-baseline check; if run, record
the result in the work log.

## Manual QA With Computer Use

Manual QA is non-invasive. The reviewer may use Computer Use or shell checks to confirm local
availability, but must not open, copy, screenshot, or paste raw protected local data.

Report only boolean results and short blocker labels. Do not include screenshots, raw file contents,
full local paths, shortcut targets, Steam account details, TTS save names, copied metadata, War
Organ local data, or credential material in this QA file or the work log.

Checks:

- `tts_executable_present`: Tabletop Simulator executable exists.
- `tts_mods_directory_present`: TTS local mods directory exists.
- `tts_saves_directory_present`: TTS local saves directory exists.
- `hutber_metadata_present`: local TTS metadata contains a Hutber marker.
- `forceorg_metadata_present`: local TTS metadata contains a ForceOrg marker.
- `war_organ_shortcut_present`: War Organ shortcut exists.
- `war_organ_target_present`: War Organ shortcut target exists.
- `no_protected_artifacts_staged`: staged files contain no raw saves, screenshots, rosters,
  generated logs, Codex/OpenAI state, Steam state, War Organ local data, or credentials.

Browser QA is not required for Phase 0 because no web route, template, SVG, raster, or frontend
behavior changes.

## Pass Criteria

Phase 0 passes only if:

- plan review passes after any P0/P1 fixes;
- consultant and adversarial closeout review pass;
- changed files match the allowlist;
- ignore rules cover the protected local artifact buckets;
- standard verification passes or nonblocking omissions are logged with reasons;
- manual QA reports sanitized boolean results only;
- CodeRabbit review either passes or an exact install/auth blocker is logged;
- the Phase 0 work is committed atomically.
