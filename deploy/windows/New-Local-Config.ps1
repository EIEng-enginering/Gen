$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$configPath = Join-Path $repo '.env'
if (Test-Path $configPath) {
    Write-Host 'Local .env already exists; no changes made.'
    exit 0
}
# Full .NET crypto randomness. Generate hex-only passwords that are safe in env and URLs.
$adminBytes = [byte[]]::new(24)
$dbBytes = [byte[]]::new(24)
$generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $generator.GetBytes($adminBytes)
    $generator.GetBytes($dbBytes)
} finally { $generator.Dispose() }
$adminPass = [System.BitConverter]::ToString($adminBytes).Replace("-", "")
$dbPass = [System.BitConverter]::ToString($dbBytes).Replace("-", "")
$body = @"
GRAMPS_IMAGE=ghcr.io/gramps-project/grampsweb:latest
VALKEY_IMAGE=valkey/valkey:8-alpine
POSTGRES_IMAGE=postgres:17-alpine
GRAMPS_PORT=5055
RESEARCH_PORT=8765
GEN_ADMIN_USER=admin
GEN_ADMIN_PASSWORD=$adminPass
GEN_DB_PASSWORD=$dbPass
"@
# .env is in local checkout; code should never commit it or put it inside OneDrive.
[System.IO.File]::WriteAllText($configPath, $body, [System.Text.UTF8Encoding]::new($false))
Write-Host "Created local .env at $configPath"
Write-Host 'The generated passwords are in .env. Keep it private; do not commit or upload it.'
Write-Host 'IMPORTANT: Development image tags must be pinned by tested digest before accepted release.'
