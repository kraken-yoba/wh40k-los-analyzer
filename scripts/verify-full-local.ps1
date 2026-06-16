param(
  [switch]$RequireOfficialPdfRegression
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:UV_CACHE_DIR = Join-Path $repoRoot ".uv-cache"

& "$PSScriptRoot\verify-public.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$PSScriptRoot\verify-gui.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$officialRegression = Join-Path $PSScriptRoot "..\backend\tests\test_official_pdf_regression.py"
if (Test-Path -LiteralPath $officialRegression) {
  python -m uv run pytest $officialRegression -q
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} elseif ($RequireOfficialPdfRegression) {
  Write-Error "Official-PDF regression harness is required but is not present yet."
} else {
  Write-Host "Official-PDF regression harness is not present yet; skipping optional local gate."
}
