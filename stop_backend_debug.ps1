param(
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"

$portFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "tmp\developer_debug_port.txt"
$frontendPidFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "tmp\developer_debug_frontend_pid.txt"
$frontendPortFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "tmp\developer_debug_frontend_port.txt"
if ($Port -le 0 -and (Test-Path $portFile)) {
    $savedPort = (Get-Content $portFile -Raw).Trim()
    if ($savedPort -match '^\d+$') {
        $Port = [int]$savedPort
    }
}
if ($Port -le 0) {
    $Port = 8014
}

$listenerPids = @()
try {
    $listenerPids = @(
        Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
            Select-Object -ExpandProperty OwningProcess -Unique
    )
} catch {
    # Fall back to command-line matching when the networking cmdlet is unavailable.
}

$uvicornProcesses = @(
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -match "uvicorn\s+src\.main:app" -and
            $_.CommandLine -match "--port\s+$Port(\s|$)"
        }
)

$targetIds = [System.Collections.Generic.HashSet[int]]::new()
foreach ($processId in $listenerPids) {
    [void]$targetIds.Add([int]$processId)
}
foreach ($process in $uvicornProcesses) {
    [void]$targetIds.Add([int]$process.ProcessId)
    if ($process.ParentProcessId) {
        [void]$targetIds.Add([int]$process.ParentProcessId)
    }
}

if ($targetIds.Count -eq 0) {
    Write-Host "No debug backend is listening on port $Port."
    exit 0
}

$stopped = @()
foreach ($processId in $targetIds) {
    try {
        Stop-Process -Id $processId -Force -ErrorAction Stop
        $stopped += $processId
    } catch {
        # A reloader parent may already exit after its child is stopped.
    }
}

Write-Host ("Stopped developer-debug backend process IDs on port {0}: {1}" -f $Port, ($stopped -join ", "))
if ($stopped.Count -gt 0 -and (Test-Path $portFile)) {
    Remove-Item -LiteralPath $portFile -Force -ErrorAction SilentlyContinue
} elseif ($stopped.Count -eq 0) {
    Write-Warning "No matching process could be stopped; the port record was kept for another shutdown attempt."
}

if (Test-Path $frontendPidFile) {
    $frontendPid = (Get-Content $frontendPidFile -Raw).Trim()
    if ($frontendPid -match '^\d+$') {
        try {
            Stop-Process -Id ([int]$frontendPid) -Force -ErrorAction Stop
            Write-Host "Stopped developer-debug frontend process ID: $frontendPid"
        } catch {
            Write-Warning "The tracked developer-debug frontend process could not be stopped."
        }
    }
    Remove-Item -LiteralPath $frontendPidFile -Force -ErrorAction SilentlyContinue
}
Remove-Item -LiteralPath $frontendPortFile -Force -ErrorAction SilentlyContinue
