param(
  [Parameter(Mandatory=$true)][string]$BackupDirectory,
  [string]$RestoreProject='gen24wp027restore',
  [switch]$Execute,
  [switch]$RequireNonemptyMedia
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$backup = (Resolve-Path -LiteralPath $BackupDirectory).Path
if ($backup -match '(?i)OneDrive') { throw 'Raw backups must be outside OneDrive.' }
if ($RestoreProject -notmatch '^gen24wp027[a-z0-9_-]{1,35}$' -or $RestoreProject -eq 'gen24') {
  throw 'Restore project must be an explicitly disposable gen24wp027* namespace, never gen24.'
}
$manifest = Get-Content -LiteralPath (Join-Path $repo 'deploy\backup-volumes.json') -Raw | ConvertFrom-Json
if ($manifest.schema_version -ne 1 -or $manifest.compose_project -ne 'gen24' -or @($manifest.volumes).Count -ne 9) {
  throw 'Unexpected exact-volume manifest.'
}
$keys = @($manifest.volumes | ForEach-Object { [string]$_ })
if ((@($keys | Select-Object -Unique)).Count -ne 9) { throw 'Duplicate volume keys.' }
# Verify the source archives fully, including absence of dangerous member types, before any volume is created.
$pythonExe = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if (-not $cmd) { throw 'Python required; project virtual environment missing.' }
  $pythonExe = $cmd.Source
}
$preflight = @((Join-Path $repo 'tools\verify_24gen_backup.py'), $backup)
if ($RequireNonemptyMedia) { $preflight += '--require-media' }
& $pythonExe @preflight
if ($LASTEXITCODE -ne 0) { throw 'Backup preflight failed. No volumes created.' }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop unavailable.' }
docker info --format '{{.ServerVersion}}' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Docker engine unavailable.' }
$helper = if ($env:GEN_RESTORE_HELPER_IMAGE) { $env:GEN_RESTORE_HELPER_IMAGE } else { 'alpine:3.20' }
$names = @($keys | ForEach-Object { "${RestoreProject}_$_" })
foreach ($n in $names) {
  $existing = @(docker volume ls --format '{{.Name}}' --filter "name=^${n}$" | Where-Object { $_ })
  if ($LASTEXITCODE -ne 0) { throw 'Docker volume query failed.' }
  if ($existing.Count -gt 0) { throw "Refusing to overwrite any pre-existing restore volume: $n" }
}
Write-Host "Source backup: $backup"
Write-Host "Isolated namespace: $RestoreProject"
Write-Host "Restore volumes planned: $($names.Count). Production project 'gen24' will not be touched."
if (-not $Execute) { Write-Host 'DRY RUN ONLY. Pass -Execute to create NEW isolated volumes and extract trusted archives.'; exit 0 }
# No automatic cleanup, because the operator must be able to inspect restored media and database.
# No production containers are stopped, attached or modified.
foreach ($key in $keys) {
  $name = "${RestoreProject}_$key"
  docker volume create --label "com.docker.compose.project=$RestoreProject" --label "com.docker.compose.volume=$key" $name | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Could not create isolated volume: $name" }
  $archive = "gen24_${key}.tgz"
  # --network none prevents the helper from contacting providers or unrelated services.
  docker run --rm --network none --read-only --mount "type=volume,source=$name,target=/target" --mount "type=bind,source=$backup,target=/backup,readonly" $helper tar -xzf "/backup/$archive" -C /target
  if ($LASTEXITCODE -ne 0) { throw "Isolated extraction failed: $name. DO NOT release; inspect volumes." }
}
Write-Host 'All nine archives extracted to separate isolated Docker volumes.'
Write-Host 'NOT FULL ACCEPTANCE: start the isolated app stack, inspect actual people, citations, research rows and restored nonempty media.'
Write-Host 'No volumes will be automatically removed. Retain isolated volumes for inspection and audit.'
