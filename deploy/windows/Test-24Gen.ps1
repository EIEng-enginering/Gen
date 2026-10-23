$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $repo
try {
    docker compose --env-file .env -f deploy/compose.yaml ps
    if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect Compose stack.' }
    $research = Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 10
    if ($research.status -ne 'up') { throw 'Research API health check failed.' }
    $gramps = Invoke-WebRequest -Uri 'http://127.0.0.1:5055/' -TimeoutSec 20 -UseBasicParsing
    if ($gramps.StatusCode -ne 200) { throw 'Gramps Web did not return HTTP 200.' }
    # The Gramps auth and import workflow must be tested manually on the computer.
    Write-Host 'PASS: HTTP liveness for both locally published services.'
    Write-Host 'NOT RUN: Gramps owner login, GEDCOM import, volume persistence, media recovery, model validation.'
} finally { Pop-Location }
