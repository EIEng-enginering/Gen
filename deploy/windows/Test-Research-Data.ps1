# Disposable test only. Does not import real family files.
param([switch]$ApplySyntheticDemo)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $repo
try {
  docker compose --env-file .env -f deploy/compose.yaml ps
  if ($LASTEXITCODE -ne 0) { throw 'Docker Compose stack unavailable' }
  docker compose --env-file .env -f deploy/compose.yaml exec -T research_web python -m app.research.schema_gate
  if ($LASTEXITCODE -ne 0) { throw 'Research DB schema gate failed' }
  $research = Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 10
  if ($research.status -ne 'up') { throw 'Research web liveness failed' }
  docker compose --env-file .env -f deploy/compose.yaml cp fixtures/english_parish_demo.csv research_web:/tmp/english_parish_demo.csv
  if ($LASTEXITCODE -ne 0) { throw 'Could not copy synthetic fixture' }
  docker compose --env-file .env -f deploy/compose.yaml exec -T research_web python -m app.research.importer /tmp/english_parish_demo.csv
  if ($LASTEXITCODE -ne 0) { throw 'Synthetic CSV dry-run failed' }
  if ($ApplySyntheticDemo) {
    Write-Warning 'Inserting synthetic demo observations into this research database.'
    docker compose --env-file .env -f deploy/compose.yaml exec -T research_web python -m app.research.importer /tmp/english_parish_demo.csv --apply
    if ($LASTEXITCODE -ne 0) { throw 'Synthetic CSV import failed' }
    docker compose --env-file .env -f deploy/compose.yaml exec -T research_web python -m app.research.importer /tmp/english_parish_demo.csv --apply
    if ($LASTEXITCODE -ne 0) { throw 'Synthetic CSV idempotence retest failed' }
  }
  Write-Host 'Research schema and dry-run preflight completed. Owner login, full restoration and image locks still require separate checks.'
} finally { Pop-Location }
