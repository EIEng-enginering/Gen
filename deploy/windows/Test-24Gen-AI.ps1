# Non-mutating inspection of the private AI research interface.
[CmdletBinding()]
param([int]$Port=8765,[int]$TimeoutSeconds=15)
$ErrorActionPreference='Stop'
$repo=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$envFile=Join-Path $repo '.env'
if (-not (Test-Path -LiteralPath $envFile)) { throw 'Private .env not configured' }
$settings=@{}
foreach($line in Get-Content -LiteralPath $envFile -Encoding UTF8) {
 if($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') { $settings[$matches[1]]=$matches[2] }
}
if(-not $settings['GEN_ADMIN_USER'] -or -not $settings['GEN_ADMIN_PASSWORD']){ throw 'Missing private credentials' }
if(-not $PSBoundParameters.ContainsKey('Port') -and $settings['RESEARCH_PORT']){$Port=[int]$settings['RESEARCH_PORT']}
$bytes=[System.Text.Encoding]::UTF8.GetBytes($settings['GEN_ADMIN_USER']+':'+$settings['GEN_ADMIN_PASSWORD'])
try {
 $authorization='Basic '+[Convert]::ToBase64String($bytes)
 $headers=@{Authorization=$authorization}
 $base='http://127.0.0.1:'+$Port
 $cap=Invoke-RestMethod -Uri ($base+'/api/v1/research/ai/capabilities') -Headers $headers -TimeoutSec $TimeoutSeconds
 if($cap.accepted_gramps_writes_enabled -ne $false -or $cap.provider_network_search_enabled -ne $false){throw 'UNSAFE AI policy'}
 $workspace=Invoke-WebRequest -Uri ($base+'/workspace') -Headers $headers -TimeoutSec $TimeoutSeconds -UseBasicParsing
 if($workspace.StatusCode -ne 200 -or $workspace.Content -notmatch 'AI Research'){throw 'AI Research screen unavailable'}
 Write-Host 'PASS: authenticated AI Research UI, local-only policy, no Gramps writes or provider execution.'
 Write-Host ('Local model configuration status: '+$cap.local_model.status)
 Write-Host 'NOT VERIFIED: real Ollama inference, local record retrieval, restart persistence, full Gramps/volume restoration.'
} finally {
 [Array]::Clear($bytes,0,$bytes.Length)
 $authorization=$null;$headers=$null;$settings=$null
}
