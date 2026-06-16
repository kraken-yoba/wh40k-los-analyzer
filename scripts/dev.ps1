$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:UV_CACHE_DIR = Join-Path $repoRoot ".uv-cache"

$host = $env:FORTYK_LOS_HOST
if ([string]::IsNullOrWhiteSpace($host)) {
  $host = "127.0.0.1"
}

$port = $env:FORTYK_LOS_PORT
if ([string]::IsNullOrWhiteSpace($port)) {
  $port = "8765"
}

python -m uv run uvicorn fortyk_los_backend.app:app --app-dir backend --host $host --port $port --reload
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
