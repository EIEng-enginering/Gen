# Built-in Windows PowerShell parser preflight for all supplied scripts.
$ErrorActionPreference='Stop'
$names=@('Preflight-24Gen.ps1','Test-24Gen-UI.ps1','Install-24Gen.ps1',
         'Launch-24Gen.ps1','Create-24Gen-Shortcuts.ps1','Validate-24Gen-Scripts.ps1')
foreach($name in $names) {
    $file=Join-Path $PSScriptRoot $name
    $tokens=$null; $errors=$null
    [void][System.Management.Automation.Language.Parser]::ParseFile($file,[ref]$tokens,[ref]$errors)
    if ($errors.Count -gt 0) {
        foreach($issue in $errors) { Write-Error ($name + ': '+$issue.Message) }
        throw ('PowerShell parser rejected '+$name)
    }
    Write-Host ('PASS: PowerShell syntax '+$name)
}
