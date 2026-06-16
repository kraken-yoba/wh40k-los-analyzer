$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:UV_CACHE_DIR = Join-Path $repoRoot ".uv-cache"

python -m uv run uvicorn fortyk_los_backend.app:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
