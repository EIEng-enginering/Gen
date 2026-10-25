param([string]$Url='http://127.0.0.1:8765')
$ErrorActionPreference='Stop'
if ($Url -ne 'http://127.0.0.1:8765' -and $Url -ne 'http://localhost:8765') { throw 'Only loopback local service allowed.' }
$repo=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$envFile=Join-Path $repo '.env'
if (-not (Test-Path -LiteralPath $envFile)) { throw 'Private local .env missing.' }
$values=@{}
foreach ($line in (Get-Content -LiteralPath $envFile -Encoding UTF8)) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') { $values[$matches[1]]=$matches[2] }
}
$u=$values['GEN_ADMIN_USER'];$p=$values['GEN_ADMIN_PASSWORD']
if (-not $u -or -not $p -or $p -like 'REPLACE_*') { throw 'Local admin configuration is not ready.' }
$raw=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${u}:$p"))
$h=@{ Authorization="Basic $raw" }
try {
  $pol=Invoke-RestMethod -Uri "$Url/api/v1/research/acquisition/provider-policies" -Headers $h -TimeoutSec 20
  if ($pol.provider_execution_enabled -ne $false) { throw 'Unsafe provider execution policy.' }
  $page=Invoke-WebRequest -Uri "$Url/acquisition" -Headers $h -TimeoutSec 20 -UseBasicParsing
  if ($page.StatusCode -ne 200 -or $page.Content -notmatch 'Evidence acquisition') { throw 'Acquisition UI unavailable.' }
  Write-Host 'PASS: acquisition page and provider policies accessible; no provider execution enabled.'
} finally {
  $raw=$null;$h=$null;$values.Clear();$u=$null;$p=$null
}
