# Non-destructive live smoke: Gramps homepage + authenticated research UI and database.
[CmdletBinding()]
param([switch]$RequireDatabase, [int]$TimeoutSeconds=20)
$ErrorActionPreference = 'Stop'
$repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$envFile = Join-Path $repo '.env'
if (-not (Test-Path -LiteralPath $envFile)) { throw 'Private .env missing. Run Install-24Gen.ps1 first.' }
$composeFile = Join-Path $repo 'deploy\compose.yaml'
$runningServices = @(& docker compose --project-directory $repo --env-file $envFile -f $composeFile ps --status running --services | Where-Object { $_ })
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect 24 Gen Docker services.' }
$requiredServices = @('grampsweb','grampsweb_celery','grampsweb_redis','research_db','research_web')
$missingServices = @($requiredServices | Where-Object { $_ -notin $runningServices })
if ($missingServices.Count -gt 0) { throw ('24 Gen services not running: ' + ($missingServices -join ', ')) }
Write-Host 'PASS: all five Docker services running'
$values = @{}
foreach ($line in (Get-Content -LiteralPath $envFile -Encoding UTF8)) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') { $values[$matches[1]] = $matches[2] }
}
foreach ($name in @('GEN_ADMIN_USER','GEN_ADMIN_PASSWORD','GEN_DB_PASSWORD')) {
    if (-not $values.ContainsKey($name) -or [string]::IsNullOrWhiteSpace($values[$name]) -or $values[$name] -like 'REPLACE_*') {
        throw ('Missing valid private configuration setting: ' + $name)
    }
}
$researchPort = if ($values['RESEARCH_PORT']) { [int]$values['RESEARCH_PORT'] } else { 8765 }
$grampsPort = if ($values['GRAMPS_PORT']) { [int]$values['GRAMPS_PORT'] } else { 5055 }
$research = 'http://127.0.0.1:' + $researchPort
$gramps = 'http://127.0.0.1:' + $grampsPort
$credentialBytes = [System.Text.Encoding]::UTF8.GetBytes($values['GEN_ADMIN_USER'] + ':' + $values['GEN_ADMIN_PASSWORD'])
$auth = [Convert]::ToBase64String($credentialBytes)
$headers = @{ Authorization = 'Basic ' + $auth }
try {
    $health = Invoke-RestMethod -Uri ($research + '/health') -TimeoutSec $TimeoutSeconds
    if ($health.status -ne 'up') { throw 'Research service did not report healthy.' }
    Write-Host 'PASS: research service HTTP /health'
    $landing = Invoke-WebRequest -Uri ($research + '/') -Headers $headers -TimeoutSec $TimeoutSeconds -UseBasicParsing
    if ($landing.StatusCode -ne 200 -or $landing.Content -notmatch '24 Gen') { throw 'Authenticated 24 Gen landing page is unavailable.' }
    Write-Host 'PASS: authenticated 24 Gen landing page'
    $workspace = Invoke-WebRequest -Uri ($research + '/workspace') -Headers $headers -TimeoutSec $TimeoutSeconds -UseBasicParsing
    if ($workspace.StatusCode -ne 200 -or $workspace.Content -notmatch '24 Gen') { throw 'Authenticated research workspace is unavailable.' }
    Write-Host 'PASS: authenticated research workspace HTML'
    # Verify anonymous visitors cannot read the workspace. Do not log response content.
    $unauthenticatedCode = 0
    try {
        $anonymous = Invoke-WebRequest -Uri ($research + '/workspace') -TimeoutSec $TimeoutSeconds -UseBasicParsing -ErrorAction Stop
        $unauthenticatedCode = [int]$anonymous.StatusCode
    } catch {
        if ($_.Exception.Response) { $unauthenticatedCode = [int]$_.Exception.Response.StatusCode }
        else { throw 'Anonymous-access policy test encountered a connection error.' }
    }
    if ($unauthenticatedCode -ne 401) { throw 'Anonymous research workspace must return HTTP 401.' }
    Write-Host 'PASS: unauthenticated workspace denied (HTTP 401)'
    $status = Invoke-RestMethod -Uri ($research + '/api/v1/status') -Headers $headers -TimeoutSec $TimeoutSeconds
    if ($RequireDatabase -and -not $status.research_database_connected) { throw 'Research service responds, but PostgreSQL connection failed.' }
    Write-Host ('Research database connected: ' + [string]$status.research_database_connected)
    $policy = Invoke-RestMethod -Uri ($research + '/api/v1/research/gramps/execution-policy') -Headers $headers -TimeoutSec $TimeoutSeconds
    if ($policy.accepted_tree_mutation_enabled -ne $false) { throw 'UNSAFE: accepted-tree mutation policy is not explicitly false.' }
    Write-Host 'PASS: accepted Gramps tree mutation remains disabled'
    $gw = Invoke-WebRequest -Uri ($gramps + '/') -TimeoutSec $TimeoutSeconds -UseBasicParsing
    if ($gw.StatusCode -ne 200) { throw ('Gramps web returned HTTP ' + $gw.StatusCode) }
    Write-Host 'PASS: Gramps Web homepage responds'
    Write-Host ('Research UI: ' + $research)
    Write-Host ('Gramps UI:   ' + $gramps)
    Write-Host 'NOT VERIFIED: Gramps owner login, import, real interactive browser actions, database persistence, backup/restore.'
} finally {
    $auth = $null
    $headers = $null
    $values = $null
    [Array]::Clear($credentialBytes, 0, $credentialBytes.Length)
}
