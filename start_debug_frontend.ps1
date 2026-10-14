param(
    [Parameter(Mandatory = $true)]
    [int]$BackendPort,
    [int]$FrontendPort = 8081,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$recordDirectory = Join-Path $projectRoot "tmp"
$frontendPidFile = Join-Path $recordDirectory "developer_debug_frontend_pid.txt"
$frontendPortFile = Join-Path $recordDirectory "developer_debug_frontend_port.txt"
$python = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

function Test-FrontendPage([int]$Port) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/website.html" -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -eq 200 -and $response.Content -match "RiskFlow"
    } catch {
        return $false
    }
}

function Test-PortListening([int]$Port) {
    return $null -ne (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Find-FreePort([int]$StartPort) {
    $candidate = $StartPort
    while (Test-PortListening $candidate) { $candidate++ }
    return $candidate
}

New-Item -ItemType Directory -Path $recordDirectory -Force | Out-Null
Remove-Item -LiteralPath $frontendPidFile -Force -ErrorAction SilentlyContinue

if (-not (Test-FrontendPage $FrontendPort)) {
    if (Test-PortListening $FrontendPort) {
        $FrontendPort = Find-FreePort $FrontendPort
    }
    $frontendProcess = Start-Process -FilePath $python -ArgumentList "-m", "http.server", "$FrontendPort", "--bind", "127.0.0.1" -WorkingDirectory (Join-Path $projectRoot "web") -WindowStyle Hidden -PassThru
    Set-Content -LiteralPath $frontendPidFile -Value $frontendProcess.Id -Encoding ascii
    for ($attempt = 0; $attempt -lt 20 -and -not (Test-FrontendPage $FrontendPort); $attempt++) {
        Start-Sleep -Milliseconds 300
    }
}

Set-Content -LiteralPath $frontendPortFile -Value $FrontendPort -Encoding ascii

$backendUrl = "http://127.0.0.1:$BackendPort"
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        $health = Invoke-WebRequest -Uri "$backendUrl/health" -UseBasicParsing -TimeoutSec 2
        if ($health.StatusCode -eq 200) { break }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

$frontendUrl = "http://127.0.0.1:$FrontendPort/website.html?api=$([uri]::EscapeDataString($backendUrl))&tab=supply"
Write-Host "Developer-debug frontend: $frontendUrl"
if (-not $NoBrowser) {
    Start-Process $frontendUrl
}
