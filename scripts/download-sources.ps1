$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:UV_CACHE_DIR = Join-Path $repoRoot ".uv-cache"
$env:PYTHONPATH = Join-Path $repoRoot "backend"

python -m uv run python -m fortyk_los_backend.download_sources --repo-root $repoRoot @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
