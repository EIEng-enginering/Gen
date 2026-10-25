param([string]$OutputDirectory='C:\24Gen\Reports\Deployment')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if ($OutputDirectory -match '(?i)OneDrive') { throw 'Deployment reports must be stored outside synced OneDrive directories.' }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker unavailable.' }
if (-not (Test-Path -LiteralPath (Join-Path $root '.env'))) { throw 'Project .env not found.' }
Push-Location $root
try {
  $version=(docker version --format '{{.Server.Version}}')
  if ($LASTEXITCODE -ne 0) { throw 'Docker engine unavailable.' }
  docker compose --env-file .env -f deploy/compose.yaml config --quiet
  if ($LASTEXITCODE -ne 0) { throw 'Docker configuration invalid.' }
  $services=@(docker compose --env-file .env -f deploy/compose.yaml ps --services --status running | Where-Object { $_ })
  if ($LASTEXITCODE -ne 0) { throw 'Could not list services.' }
  $expected=@('grampsweb','grampsweb_celery','grampsweb_redis','research_db','research_web')
  $missing=@($expected | Where-Object { $_ -notin $services })
  if ($missing.Count -gt 0) { throw "Missing running services: $($missing -join ', ')" }
  $json=@()
  foreach ($svc in $expected) {
    $id=(docker compose --env-file .env -f deploy/compose.yaml ps -q $svc).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $id) { throw "Missing container ID: $svc" }
    $img=(docker inspect --format '{{.Image}}' $id).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect container image: $svc" }
    $repoDigest=@(docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' $img | Where-Object { $_ })
    # Compose builds research_web locally. Docker may display a synthetic
    # project-name@sha256 identity for it, which is not a registry-pinned image.
    $localBuild=($svc -eq 'research_web')
    $json+=@{ service=$svc; image_id=$img; registry_digests=$repoDigest;
              locally_built=$localBuild;
              has_registry_digest=(-not $localBuild -and $repoDigest.Count -gt 0) }
  }
  New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
  $report=@{ collected_utc=(Get-Date).ToUniversalTime().ToString('o'); docker_server_version=$version;
             running_services=$expected.Count; services=$json; image_digests_pinned_in_compose=$false;
             r01_accepted=$false; credentials_excluded=$true }
  $file=Join-Path $OutputDirectory '24Gen_Deployment_Evidence.json'
  $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $file -Encoding utf8
  Write-Host "Saved non-secret deployment evidence: $file"
  Write-Host 'WARNING: registry digest evidence is not equivalent to pinning tested image versions. Release remains NOT ACCEPTED.'
} finally { Pop-Location }
