param(
    [Parameter(Mandatory=$false)]
    [string]$BackupRoot = 'C:\Users\Admin\OneDrive - Enhance Integration Engineering\Company\006 Calculation Methods\24 Gen\06_Database_Backups'
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmssZ')
$backupDir = Join-Path $BackupRoot "gen24-cold-$timestamp"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
Push-Location $repo
$stopped = $false
try {
    # CONSISTENT cold backup: stop all containers before archiving all named volumes.
    docker compose --env-file .env -f deploy/compose.yaml stop
    if ($LASTEXITCODE -ne 0) { throw 'Cannot stop stack; refusing possibly inconsistent backup.' }
    $stopped = $true
    $volumes = @(docker volume ls --format '{{.Name}}' | Where-Object { $_ -like 'gen24_*' })
    if ($volumes.Count -lt 8) { throw "Expected named volumes not found (count $($volumes.Count)); abort." }
    foreach ($v in $volumes) {
        if ($v -notmatch '^gen24_[A-Za-z0-9_]+$') { throw "Unexpected volume name $v" }
        Write-Host "Archiving volume: $v"
        docker run --rm --volume "${v}:/data:ro" --volume "${backupDir}:/backup" alpine:3.20 sh -c "tar -czf /backup/${v}.tgz -C /data ."
        if ($LASTEXITCODE -ne 0) { throw "Volume archive failed: $v" }
    }
    $archives = @(Get-ChildItem -Path $backupDir -Filter '*.tgz')
    $list = foreach ($a in $archives) {
        $sum = (Get-FileHash -LiteralPath $a.FullName -Algorithm SHA256).Hash
        "${sum}  $($a.Name)"
    }
    $list | Set-Content -LiteralPath (Join-Path $backupDir 'SHA256SUMS.txt') -Encoding ASCII
    @"
24 Gen COLD VOLUME BACKUP
Created UTC: $timestamp
Data stopped during snapshot: YES
Volume count: $($volumes.Count)
Restore tested: NO (must validate in separate isolated environment)
Contains secrets, media and private genealogy data: YES
Keep restricted; verify cloud sync access. Do not share as public attachment.
"@ | Set-Content -LiteralPath (Join-Path $backupDir 'BACKUP_NOTES.txt') -Encoding UTF8
    Write-Host "Backup archives and hashes created at $backupDir"
    Write-Host 'IMPORTANT: backup is not accepted until isolated restore test is performed.'
} finally {
    if ($stopped) {
        docker compose --env-file .env -f deploy/compose.yaml start
        if ($LASTEXITCODE -ne 0) { Write-Warning 'Stack did not automatically restart; run Start-24Gen.ps1.' }
    }
    Pop-Location
}
