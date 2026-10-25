param(
  [Parameter(Mandatory=$true)][string]$BackupDirectory,
  [switch]$RequireNonemptyMedia
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$path = (Resolve-Path -LiteralPath $BackupDirectory).Path
if ($path -match '(?i)OneDrive') { throw 'Raw backups must be outside OneDrive.' }
$script = Join-Path $root 'tools\verify_24gen_backup.py'
if (-not (Test-Path -LiteralPath $script)) { throw 'Backup integrity verifier missing.' }
$pythonExe = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if (-not $cmd) { throw 'Python required; project virtual environment is missing.' }
  $pythonExe = $cmd.Source
}
$invokeArgs = @($script,$path)
if ($RequireNonemptyMedia) { $invokeArgs += '--require-media' }
& $pythonExe @invokeArgs
if ($LASTEXITCODE -ne 0) { throw 'Archive integrity validation failed.' }
Write-Host 'Archive hashes and tar entries verified. THIS IS NOT A RESTORE TEST.'
