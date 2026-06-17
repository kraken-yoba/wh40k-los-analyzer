$ErrorActionPreference = "Stop"

& "$PSScriptRoot\verify-public.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
