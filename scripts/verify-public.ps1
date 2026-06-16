$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:UV_CACHE_DIR = Join-Path $repoRoot ".uv-cache"

python -m uv run ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m uv run mypy backend
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m uv run pytest backend/tests -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
