$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $repo
try {
    docker compose --env-file .env -f deploy/compose.yaml stop
    if ($LASTEXITCODE -ne 0) { throw 'Stop failed; inspect containers before restart.' }
    Write-Host '24 Gen stopped. Persistent Docker volumes retained.'
} finally { Pop-Location }
