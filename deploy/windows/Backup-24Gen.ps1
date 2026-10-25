param(
    [Parameter(Mandatory=$false)]
    [string]$BackupRoot = 'C:\24Gen\Backups\Restricted'
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$manifestPath = Join-Path $repo 'deploy\backup-volumes.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$project = [string]$manifest.compose_project
$volumeKeys = @($manifest.volumes | ForEach-Object { [string]$_ })

if ($manifest.schema_version -ne 1 -or $project -ne 'gen24') {
    throw 'Unexpected backup manifest schema or Compose project.'
}
if ($volumeKeys.Count -ne 9 -or (@($volumeKeys | Select-Object -Unique)).Count -ne 9) {
    throw 'Backup manifest must contain exactly nine unique volumes.'
}
foreach ($key in $volumeKeys) {
    if ($key -notmatch '^[a-z][a-z0-9_]*$') { throw "Invalid logical volume name: $key" }
}
$expectedNames = @($volumeKeys | ForEach-Object { "${project}_$_" })
$backupRootFull = [System.IO.Path]::GetFullPath($BackupRoot)
if ($backupRootFull -match '(?i)(^|[\\/])OneDrive[^\\/]*([\\/]|$)') {
    throw 'Raw backups must remain outside OneDrive. Use a separately reviewed encrypted export.'
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker is not installed or is not on PATH.'
}
if (-not (Test-Path -LiteralPath (Join-Path $repo '.env'))) {
    throw 'Local .env is missing; refusing to operate on an unknown stack.'
}

Push-Location $repo
$stopAttempted = $false
$runningServices = @()
try {
    docker info --format '{{.ServerVersion}}' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Docker engine unavailable.' }
    docker compose --env-file .env -f deploy/compose.yaml config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Invalid Compose configuration.' }

    $actualNames = @(docker volume ls --filter "label=com.docker.compose.project=$project" --format '{{.Name}}' |
        Where-Object { $_ })
    if ($LASTEXITCODE -ne 0) { throw 'Could not list Compose-owned volumes.' }
    $missing = @($expectedNames | Where-Object { $_ -notin $actualNames })
    $extra = @($actualNames | Where-Object { $_ -notin $expectedNames })
    if ($missing.Count -gt 0 -or $extra.Count -gt 0 -or $actualNames.Count -ne 9) {
        throw "Volume set mismatch. Missing: $($missing -join ', '); extra: $($extra -join ', ')."
    }

    foreach ($key in $volumeKeys) {
        $name = "${project}_$key"
        $json = docker volume inspect --format '{{json .}}' $name
        if ($LASTEXITCODE -ne 0) { throw "Could not inspect volume $name." }
        $volume = $json | ConvertFrom-Json
        if ($volume.Name -ne $name -or
            $volume.Labels.'com.docker.compose.project' -ne $project -or
            $volume.Labels.'com.docker.compose.volume' -ne $key) {
            throw "Volume ownership labels do not match the manifest: $name"
        }
    }

    $runningServices = @(docker compose --env-file .env -f deploy/compose.yaml ps --status running --services |
        Where-Object { $_ })
    if ($LASTEXITCODE -ne 0) { throw 'Could not record currently running services.' }

    $timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmssZ')
    $backupDir = Join-Path $backupRootFull "gen24-cold-$timestamp"
    if (Test-Path -LiteralPath $backupDir) { throw "Backup directory already exists: $backupDir" }
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    # Restrict the directory before writing an incomplete marker or private archives.
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $allowedSids = @(
        $identity,
        [System.Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'), # Administrators
        [System.Security.Principal.SecurityIdentifier]::new('S-1-5-18')      # SYSTEM
    )
    $acl = Get-Acl -LiteralPath $backupDir
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($sid in $allowedSids) {
        $rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
            $sid, 'FullControl', 'ContainerInherit, ObjectInherit', 'None', 'Allow'
        )
        $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $backupDir -AclObject $acl
    $verifiedAcl = Get-Acl -LiteralPath $backupDir
    if (-not $verifiedAcl.AreAccessRulesProtected) { throw 'Backup directory ACL still inherits permissions.' }
    $permitted = @($allowedSids | ForEach-Object { $_.Value })
    foreach ($entry in $verifiedAcl.Access) {
        $sid = $entry.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
        if ($entry.AccessControlType -ne 'Allow' -or $sid -notin $permitted) {
            throw 'Backup directory ACL grants access outside the restricted principals.'
        }
    }
    Set-Content -LiteralPath (Join-Path $backupDir 'INCOMPLETE.txt') -Value 'Backup has not completed or been restored.' -Encoding utf8

    $stopAttempted = $true
    docker compose --env-file .env -f deploy/compose.yaml stop
    if ($LASTEXITCODE -ne 0) { throw 'Could not stop the Compose stack; backup is incomplete.' }

    $helperImage = if ($env:GEN_BACKUP_HELPER_IMAGE) { $env:GEN_BACKUP_HELPER_IMAGE } else { 'alpine:3.20' }
    foreach ($name in $expectedNames) {
        # Docker can create a missing named volume on mount; recheck immediately before use.
        $key = $name.Substring($project.Length + 1)
        $json = docker volume inspect --format '{{json .}}' $name
        if ($LASTEXITCODE -ne 0) { throw "Volume vanished before archiving: $name" }
        $volume = $json | ConvertFrom-Json
        if ($volume.Name -ne $name -or
            $volume.Labels.'com.docker.compose.project' -ne $project -or
            $volume.Labels.'com.docker.compose.volume' -ne $key) {
            throw "Volume ownership changed before archiving: $name"
        }
        Write-Host "Archiving verified volume: $name"
        docker run --rm --volume "${name}:/data:ro" --volume "${backupDir}:/backup" $helperImage sh -c "tar -czf /backup/$name.tgz -C /data ."
        if ($LASTEXITCODE -ne 0) { throw "Volume archive failed: $name" }
    }

    $archiveNames = @(Get-ChildItem -LiteralPath $backupDir -Filter '*.tgz' -File |
        ForEach-Object { $_.Name })
    $expectedArchives = @($expectedNames | ForEach-Object { "$_.tgz" })
    if ($archiveNames.Count -ne 9 -or
        @($archiveNames | Where-Object { $_ -notin $expectedArchives }).Count -gt 0 -or
        @($expectedArchives | Where-Object { $_ -notin $archiveNames }).Count -gt 0) {
        throw 'Archive set is incomplete or contains unexpected files.'
    }

    $hashLines = foreach ($archive in $expectedArchives) {
        $sum = (Get-FileHash -LiteralPath (Join-Path $backupDir $archive) -Algorithm SHA256).Hash
        "$sum  $archive"
    }
    $hashLines | Set-Content -LiteralPath (Join-Path $backupDir 'SHA256SUMS.txt') -Encoding ascii
    @"
24 Gen COLD VOLUME BACKUP
Created UTC: $timestamp
Compose project: $project
Required and archived volumes: 9
Services stopped during snapshot: YES
Restore tested: NO
Contains secrets, media and private genealogy data: YES
Keep locally restricted. Do not sync raw archives to OneDrive.
Helper image: $helperImage (pin by tested digest before release)
"@ | Set-Content -LiteralPath (Join-Path $backupDir 'BACKUP_NOTES.txt') -Encoding utf8
    Remove-Item -LiteralPath (Join-Path $backupDir 'INCOMPLETE.txt')
    Write-Host "Cold backup and SHA-256 manifest created at $backupDir"
    Write-Host 'NOT ACCEPTED: complete an isolated restore with media before release.'
}
finally {
    if ($stopAttempted -and $runningServices.Count -gt 0) {
        docker compose --env-file .env -f deploy/compose.yaml start $runningServices
        if ($LASTEXITCODE -ne 0) {
            Write-Warning 'Previously running services did not restart; inspect the stack immediately.'
        }
    }
    Pop-Location
}
