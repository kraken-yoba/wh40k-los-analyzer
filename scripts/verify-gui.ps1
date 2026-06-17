$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:UV_CACHE_DIR = Join-Path $repoRoot ".uv-cache"

python -m uv run pytest backend/tests/test_gui.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
