# Normal launch after completed first-install. Persistent volumes retained.
[CmdletBinding()]
param([switch]$NoBrowser)
$ErrorActionPreference='Stop'
$repo=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
& (Join-Path $PSScriptRoot 'Preflight-24Gen.ps1') -RequireDocker
if (-not (Test-Path -LiteralPath (Join-Path $repo '.env'))) { throw 'Not installed. Run Install-24Gen.ps1 -DisposableTestOnly first.' }
Push-Location $repo
try {
    $existing = @(& docker compose --env-file .env -f deploy/compose.yaml ps --all --services | Where-Object { $_ })
    if ($LASTEXITCODE -ne 0 -or $existing.Count -lt 5) { throw 'Expected existing containers missing; run the reviewed installer.' }
    & docker compose --env-file .env -f deploy/compose.yaml start
    if ($LASTEXITCODE -ne 0) { throw 'Start failed; inspect Docker Desktop.' }
    $deadline=(Get-Date).AddSeconds(180)
    $ready=$false
    do {
        Start-Sleep -Seconds 4
        try { & (Join-Path $PSScriptRoot 'Test-24Gen-UI.ps1') -RequireDatabase -TimeoutSeconds 8 | Out-Null; $ready=$true } catch { $ready=$false }
    } while (-not $ready -and (Get-Date) -lt $deadline)
    if (-not $ready) { throw 'Containers started, but UI/backend health check did not pass. Do not import records.' }
    Write-Host '24 Gen UI and Gramps homepage are responding.'
    if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765/'; Start-Process 'http://127.0.0.1:5055/' }
} finally { Pop-Location }
