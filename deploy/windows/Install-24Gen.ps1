# Installs/starts 24 Gen on an ALREADY prepared Windows Docker Desktop host.
# Does not install WSL/Docker, migrate populated DBs, remove volumes, import real records or enable Gramps writes.
[CmdletBinding()]
param([switch]$DisposableTestOnly, [switch]$NoBrowser, [switch]$NoShortcuts, [int]$TimeoutSeconds=360)
$ErrorActionPreference='Stop'
if (-not $DisposableTestOnly) { throw 'First installation must specify -DisposableTestOnly until backup/restore is accepted.' }
$repo=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
& (Join-Path $PSScriptRoot 'Preflight-24Gen.ps1') -RequireDocker
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw 'Preflight failed.' }
$envFile=Join-Path $repo '.env'
if (-not (Test-Path -LiteralPath $envFile)) {
    & (Join-Path $PSScriptRoot 'New-Local-Config.ps1')
    if (-not (Test-Path -LiteralPath $envFile)) { throw 'Private config creation failed.' }
}
# Apply restrictive Windows ACLs to the secret file (the user, Administrators and SYSTEM only).
$userSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
& icacls.exe $envFile /inheritance:r /grant:r "*${userSid}:(F)" '*S-1-5-18:(F)' '*S-1-5-32-544:(F)' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not secure private .env ACL; refusing startup.' }
# Run preflight again once .env exists so Compose port policy is validated.
& (Join-Path $PSScriptRoot 'Preflight-24Gen.ps1') -RequireDocker
# A first-time disposable install MUST NOT silently reuse an existing family-data volume.
$existingVolumes = @(& docker volume ls --filter 'label=com.docker.compose.project=gen24' --format '{{.Name}}' | Where-Object { $_ })
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect existing 24 Gen volumes.' }
if ($existingVolumes.Count -gt 0) { throw '24 Gen persistent volumes already exist. Use Launch-24Gen.ps1 or obtain a reviewed recovery plan; do not run first-install on existing data.' }
Push-Location $repo
try {
    Write-Host 'Pulling selected development container images. Current tags are not release locks.'
    & docker compose --env-file .env -f deploy/compose.yaml pull grampsweb grampsweb_celery grampsweb_redis research_db
    if ($LASTEXITCODE -ne 0) { throw 'Container image pull failed.' }
    Write-Host 'Building research UI and starting persistent local containers...'
    & docker compose --env-file .env -f deploy/compose.yaml up --build -d
    if ($LASTEXITCODE -ne 0) { throw 'Container build/start failed; inspect Docker Desktop and service state.' }
    $deadline=(Get-Date).AddSeconds($TimeoutSeconds)
    $ready=$false
    do {
        Start-Sleep -Seconds 5
        try {
            & (Join-Path $PSScriptRoot 'Test-24Gen-UI.ps1') -RequireDatabase -TimeoutSeconds 8 | Out-Null
            $ready=$true
        } catch { $ready=$false }
    } while (-not $ready -and (Get-Date) -lt $deadline)
    if (-not $ready) {
        & docker compose --env-file .env -f deploy/compose.yaml ps
        throw 'Startup not yet healthy. Do not import records. Inspect services locally; never share secret-containing .env or raw logs.'
    }
    & (Join-Path $PSScriptRoot 'Test-24Gen-UI.ps1') -RequireDatabase
    if (-not $NoShortcuts) { & (Join-Path $PSScriptRoot 'Create-24Gen-Shortcuts.ps1') -AllowDesktopChanges }
    Write-Host 'DISPOSABLE FIRST-BOOT UI HEALTH CHECK COMPLETE (NOT RELEASE ACCEPTANCE).'
    Write-Host 'Research interface: http://127.0.0.1:8765 ; use GEN_ADMIN_USER and GEN_ADMIN_PASSWORD from private .env.'
    Write-Host 'Gramps Web: http://127.0.0.1:5055 ; complete separate Gramps first-run owner setup.'
    Write-Host 'Next required gates: disposable Gramps XML import, restart persistence, verified nine-volume cold backup and isolated restore.'
    if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765/'; Start-Process 'http://127.0.0.1:5055/' }
} finally { Pop-Location }
