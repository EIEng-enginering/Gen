# 24 Gen Windows host check. Never installs software, changes data or displays secrets.
[CmdletBinding()]
param([switch]$RequireDocker)
$ErrorActionPreference = 'Stop'
$repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
if ($repo -match '(?i)(^|[\\/])OneDrive[^\\/]*([\\/]|$)') { throw '24 Gen active checkout must be outside OneDrive.' }
if (-not (Test-Path -LiteralPath (Join-Path $repo 'deploy\compose.yaml'))) { throw 'Not inside a 24 Gen source checkout.' }
if (-not (Test-Path -LiteralPath (Join-Path $repo 'apps\research-web\Dockerfile'))) { throw 'Missing research application Dockerfile.' }
Write-Host ('24 Gen source: ' + $repo)
if ($env:OS -ne 'Windows_NT') { throw 'This installation script requires Windows 10/11.' }
$os = Get-CimInstance Win32_OperatingSystem
$memory = Get-CimInstance Win32_ComputerSystem
Write-Host ('Windows: ' + $os.Caption + ' build ' + $os.BuildNumber)
Write-Host ('RAM (GiB): ' + [math]::Round($memory.TotalPhysicalMemory / 1GB, 1))
if ($memory.TotalPhysicalMemory -lt 8GB) { throw 'Docker Desktop requires at least 8 GiB RAM; review system prerequisites.' }
if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
    & wsl.exe --status 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Host 'WSL: installed (confirm WSL version meets Docker requirements).' }
    else { Write-Warning 'WSL not ready. Install WSL2 from Administrator PowerShell using wsl --install, then reboot.' }
} else { Write-Warning 'WSL not installed. Install WSL2 before Docker Desktop.' }
if (-not (Get-Command docker.exe -ErrorAction SilentlyContinue)) {
    Write-Warning 'Docker Desktop CLI not found. Install/start Docker Desktop with Linux containers.'
    if ($RequireDocker) { throw 'Docker missing; installation cannot proceed.' }
    return
}
& docker info --format '{{.OSType}}' | Out-Null
if ($LASTEXITCODE -ne 0) { if ($RequireDocker) { throw 'Docker engine not running. Start Docker Desktop.' }; Write-Warning 'Docker engine unavailable.'; return }
$dockerType = (& docker info --format '{{.OSType}}') | Out-String
if ($LASTEXITCODE -ne 0 -or $dockerType.Trim() -ne 'linux') { throw 'Docker Desktop must use Linux containers.' }
& docker compose version | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose V2 is required.' }
Write-Host 'Docker Desktop Linux engine and Docker Compose V2: available.'
$envPath = Join-Path $repo '.env'
if (Test-Path -LiteralPath $envPath) {
    Push-Location $repo
    try {
        # Configuration may include secrets. Capture JSON in memory; never print it.
        $raw = & docker compose --env-file .env -f deploy/compose.yaml config --format json
        if ($LASTEXITCODE -ne 0) { throw 'Compose config failed. Inspect private .env; do not upload it.' }
        $cfg = ($raw -join "`n") | ConvertFrom-Json
        foreach ($entry in $cfg.services.PSObject.Properties) {
            $ports = @($entry.Value.ports)
            foreach ($port in $ports) {
                if ($port -and $port.published -and [string]$port.host_ip -ne '127.0.0.1') {
                    throw ('Unsafe published port on ' + $entry.Name + ': host must be 127.0.0.1')
                }
            }
        }
        foreach ($name in @('grampsweb','grampsweb_celery','grampsweb_redis','research_db','research_web')) {
            if (-not $cfg.services.PSObject.Properties[$name]) { throw ('Missing Compose service: ' + $name) }
        }
        if ($cfg.services.research_db.ports -or $cfg.services.grampsweb_redis.ports) {
            throw 'Database/broker ports must remain private.'
        }
        Write-Host 'Compose services and loopback-only port policy: PASS.'
    } finally { Pop-Location }
} else { Write-Host 'No .env yet. Installer will create private local credentials.' }
