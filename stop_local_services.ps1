[CmdletBinding(SupportsShouldProcess)]
param()

$ErrorActionPreference = "Stop"
$projectPorts = @(5173, 8000, 8002, 8003, 8005, 8010, 8011, 8012)
$portPattern = ":(" + ($projectPorts -join "|") + ")\s+.*LISTENING\s+(\d+)$"
$listenerPids = @(
    netstat -ano -p tcp |
        ForEach-Object {
            $match = [regex]::Match($_, $portPattern)
            if ($match.Success) { [int]$match.Groups[2].Value }
        } |
        Select-Object -Unique
)

$processes = @(
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -match "uvicorn\s+src\.main:app" -or
            $_.CommandLine -match "python(?:\.exe)?\s+-m\s+http\.server"
        }
)

$relatedPids = [System.Collections.Generic.HashSet[int]]::new()
foreach ($processId in $listenerPids) { [void]$relatedPids.Add([int]$processId) }
foreach ($process in $processes) {
    if ($listenerPids -contains $process.ProcessId -or $listenerPids -contains $process.ParentProcessId) {
        [void]$relatedPids.Add([int]$process.ProcessId)
        if ($process.ParentProcessId) { [void]$relatedPids.Add([int]$process.ParentProcessId) }
    }
}

if ($relatedPids.Count -eq 0) {
    Write-Host "No Legal_Risk_Check local services are running."
    exit 0
}

$stopped = @()
foreach ($processId in $relatedPids) {
    try {
        if (-not $PSCmdlet.ShouldProcess("process $processId", "Stop Legal_Risk_Check local service")) {
            continue
        }
        Stop-Process -Id $processId -Force -ErrorAction Stop
        $stopped += $processId
    } catch {
        # A parent may already have exited after its child was stopped.
    }
}

if ($WhatIfPreference) {
    Write-Host "WhatIf completed. No local services were stopped."
} else {
    Write-Host ("Stopped local service process IDs: " + ($stopped -join ", "))
}
