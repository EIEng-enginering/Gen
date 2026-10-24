# Creates desktop launch/stop/test links. Does not move data or store passwords.
[CmdletBinding()]
param([switch]$AllowDesktopChanges)
$ErrorActionPreference='Stop'
if (-not $AllowDesktopChanges) { throw 'Explicitly supply -AllowDesktopChanges to create shortcuts.' }
$repo=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$desktop=[Environment]::GetFolderPath('DesktopDirectory')
if (-not $desktop -or -not (Test-Path -LiteralPath $desktop)) { throw 'Desktop folder unavailable.' }
$ws=New-Object -ComObject WScript.Shell
$psExe=Join-Path $PSHOME 'powershell.exe'
if (-not (Test-Path -LiteralPath $psExe)) { $psExe='powershell.exe' }
$items=@(
    @{Title='24 Gen - Start and Open'; Script='Launch-24Gen.ps1'},
    @{Title='24 Gen - Stop'; Script='Stop-24Gen.ps1'},
    @{Title='24 Gen - Check UI'; Script='Test-24Gen-UI.ps1'}
)
foreach($item in $items) {
    $file=Join-Path $desktop ($item.Title+'.lnk')
    if (Test-Path -LiteralPath $file) { Write-Host ('Existing shortcut retained: '+$file); continue }
    $link=$ws.CreateShortcut($file)
    $link.TargetPath=$psExe
    $link.Arguments='-NoProfile -ExecutionPolicy RemoteSigned -File "'+(Join-Path $PSScriptRoot $item.Script)+'"'
    $link.WorkingDirectory=$repo
    $link.Description='24 Gen local genealogy - '+$item.Title
    $link.Save()
    Write-Host ('Created: '+$file)
}
