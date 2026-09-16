$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host 'Escapists Agent — desktop launcher'
Write-Host '1: List windows   2: Capture   3: Calibrate   4: Observe   5: Move (10 seconds)   6: Demo'
$choice = Read-Host 'Choose a number'
$title = 'The Escapists'
if ($choice -in @('2','4','5')) {
    $entered = Read-Host 'Exact game window title (Enter for The Escapists)'
    if ($entered) { $title = $entered }
    Write-Host 'After starting, switch to the game within 10 seconds. F8 stops movement.'
}
switch ($choice) {
    '1' { & .\Run.ps1 windows }
    '2' { & .\Run.ps1 capture --title $title --delay 10 }
    '3' { & .\Run.ps1 calibrate runs/capture.png }
    '4' { & .\Run.ps1 run --title $title --delay 10 }
    '5' { & .\Run.ps1 run --title $title --delay 10 --arm --seconds 10 }
    '6' { & .\Run.ps1 demo }
    default { Write-Host 'No action selected.' }
}
Read-Host 'Press Enter to close'
