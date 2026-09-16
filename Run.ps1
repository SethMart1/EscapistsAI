param([Parameter(ValueFromRemainingArguments=$true)][string[]]$AgentArgs)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$localPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path $localPython) { $agentPython = $localPython }
elseif (Test-Path $bundledPython) { $agentPython = $bundledPython }
else { $agentPython = 'python' }
& $agentPython -m escapists_agent.cli @AgentArgs
exit $LASTEXITCODE
