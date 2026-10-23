$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $repo
try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker not found. Install and start Docker Desktop (WSL2 Linux containers).' }
    if (-not (Test-Path '.env')) { throw 'Missing local .env: run deploy/windows/New-Local-Config.ps1 first.' }
    docker info | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Docker engine unavailable.' }
    docker compose --env-file .env -f deploy/compose.yaml config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Invalid Compose configuration.' }
    docker compose --env-file .env -f deploy/compose.yaml up -d --build
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose startup failed.' }
    Write-Host 'Started containers. Gramps first-run owner setup: http://127.0.0.1:5055'
    Write-Host '24 Gen read-only research scaffold: http://127.0.0.1:8765'
    Start-Process 'http://127.0.0.1:8765'
} finally { Pop-Location }
