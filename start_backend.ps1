param(
    [int]$Port = 8000,
    [string]$Address = "127.0.0.1",
    [switch]$NoReload,
    [switch]$EnableLiveMarket,
    [switch]$DisableLiveMarket,
    [switch]$EnableLiveIntelligence,
    [switch]$DisableLiveIntelligence,
    [switch]$EnableWebSearch,
    [switch]$DisableWebSearch,
    [switch]$EnableDemoIdentity,
    [switch]$DisableDemoIdentity,
    [switch]$EnableDeveloperDebug,
    [switch]$SkipDbCheck
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Get-ListeningProcessDetails {
    param([Parameter(Mandatory = $true)][int]$ListenPort)

    # netstat covers wildcard listeners (0.0.0.0 and ::), which a probe to
    # just one address can miss, and is available on supported Windows hosts.
    # It is deliberately used instead of the slower networking cmdlets so the
    # preflight remains immediate during a normal local launch.
    $listenerProcessIds = @(
        & netstat.exe -ano -p tcp 2>$null |
            ForEach-Object {
                if ($_ -match '^\s*TCP\s+\S+:(?<port>\d+)\s+\S+\s+LISTENING\s+(?<pid>\d+)\s*$' -and [int]$matches.port -eq $ListenPort) {
                    [int]$matches.pid
                }
            } |
            Select-Object -Unique
    )
    foreach ($processId in $listenerProcessIds) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            ProcessId   = $processId
            ProcessName = if ($process) { $process.Name } else { "unknown" }
            CommandLine = if ($process -and $process.CommandLine) { $process.CommandLine } else { "(command unavailable)" }
        }
    }
}

function Assert-BackendPortAvailable {
    param([Parameter(Mandatory = $true)][int]$ListenPort)

    $owners = @(Get-ListeningProcessDetails -ListenPort $ListenPort)
    if ($owners.Count -eq 0) { return }

    Write-Host ""
    Write-Host "Backend was not started: http port $ListenPort is already listening." -ForegroundColor Red
    Write-Host "Refusing to continue so this launcher cannot appear to start a new service while an older instance answers requests." -ForegroundColor Yellow
    foreach ($owner in $owners) {
        Write-Host ("  PID {0} ({1}): {2}" -f $owner.ProcessId, $owner.ProcessName, $owner.CommandLine)
    }
    Write-Host "Stop the listed process (including any uvicorn --reload parent/worker) or choose an unused -Port, then run this script again."
    throw "Port $ListenPort is already occupied."
}

# This must happen before the startup banner and before uvicorn is invoked.
# Otherwise a failed bind can leave an old reload worker serving the port while
# the console misleadingly looks like a successful new launch.
Assert-BackendPortAvailable -ListenPort $Port

$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

$ReloadArgs = @()
if (-not $NoReload) {
    $ReloadArgs += "--reload"
}

$QdrantHost = $env:QDRANT_HOST
if (-not $QdrantHost) {
    $QdrantHost = "localhost"
    $env:QDRANT_HOST = $QdrantHost
}

$QdrantPort = $env:QDRANT_PORT
if (-not $QdrantPort) {
    $QdrantPort = "6333"
    $env:QDRANT_PORT = $QdrantPort
}

$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    foreach ($line in Get-Content -LiteralPath $EnvFile) {
        if ($line -notmatch '^\s*(EXTERNAL_RISK_[A-Za-z0-9_]+)\s*=\s*(.*)\s*$') { continue }
        $key = $matches[1]
        if (Test-Path "Env:$key") { continue }
        $value = $matches[2].Trim()
        if ($value.StartsWith('"') -and $value.EndsWith('"')) {
            try { $value = $value | ConvertFrom-Json } catch { continue }
        }
        Set-Item -Path "Env:$key" -Value $value
    }
}

if ($DisableLiveMarket) {
    $env:EXTERNAL_RISK_LIVE_ENABLED = "false"
    $env:EXTERNAL_RISK_HTTP_ENABLED = "false"
} elseif ($EnableLiveMarket -or -not $env:EXTERNAL_RISK_LIVE_ENABLED) {
    $env:EXTERNAL_RISK_LIVE_ENABLED = "true"
    $env:EXTERNAL_RISK_HTTP_ENABLED = "true"
} elseif (-not $env:EXTERNAL_RISK_HTTP_ENABLED) {
    $env:EXTERNAL_RISK_HTTP_ENABLED = $env:EXTERNAL_RISK_LIVE_ENABLED
}

if ($DisableLiveIntelligence) {
    $env:EXTERNAL_RISK_INTELLIGENCE_ENABLED = "false"
    $env:EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED = "false"
} elseif ($EnableLiveIntelligence -or -not $env:EXTERNAL_RISK_INTELLIGENCE_ENABLED) {
    $env:EXTERNAL_RISK_INTELLIGENCE_ENABLED = "true"
    $env:EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED = "true"
} elseif (-not $env:EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED) {
    $env:EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED = $env:EXTERNAL_RISK_INTELLIGENCE_ENABLED
}

if ($DisableWebSearch) {
    $env:EXTERNAL_RISK_WEB_SEARCH_ENABLED = "false"
} elseif ($EnableWebSearch) {
    $env:EXTERNAL_RISK_WEB_SEARCH_ENABLED = "true"
} elseif (-not $env:EXTERNAL_RISK_WEB_SEARCH_ENABLED) {
    $env:EXTERNAL_RISK_WEB_SEARCH_ENABLED = "false"
}

$LiveMarketEnabled = if ($env:EXTERNAL_RISK_LIVE_ENABLED) { $env:EXTERNAL_RISK_LIVE_ENABLED } else { "false" }
$HttpMarketEnabled = if ($env:EXTERNAL_RISK_HTTP_ENABLED) { $env:EXTERNAL_RISK_HTTP_ENABLED } else { "false" }
$LiveIntelligenceEnabled = if ($env:EXTERNAL_RISK_INTELLIGENCE_ENABLED) { $env:EXTERNAL_RISK_INTELLIGENCE_ENABLED } else { "false" }
$IntelligenceSchedulerEnabled = if ($env:EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED) { $env:EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED } else { "false" }
$IntelligenceFeedMode = if ($env:EXTERNAL_RISK_INTELLIGENCE_FEEDS) { "custom" } else { "core-defaults (7)" }
$WebSearchEnabled = if ($env:EXTERNAL_RISK_WEB_SEARCH_ENABLED) { $env:EXTERNAL_RISK_WEB_SEARCH_ENABLED } else { "false" }
$WebSearchProvider = if ($env:EXTERNAL_RISK_WEB_SEARCH_PROVIDER) { $env:EXTERNAL_RISK_WEB_SEARCH_PROVIDER } else { "tavily" }
$QdrantUrl = "http://$QdrantHost`:$QdrantPort"

if (-not $env:MINEU_MODE) {
    $env:MINEU_MODE = "lightweight"
}

if ($EnableDemoIdentity -and $DisableDemoIdentity) {
    throw "-EnableDemoIdentity and -DisableDemoIdentity cannot be used together."
}

$IsLoopbackAddress = $Address -in @("127.0.0.1", "::1", "localhost")
if ($DisableDemoIdentity) {
    $env:RISK_DEMO_IDENTITY_ENABLED = "false"
} elseif ($EnableDemoIdentity) {
    # The browser UI has no enterprise gateway in a local workspace. Keep the
    # fixed demo identity available only for the default loopback launch.
    $env:RISK_DEMO_IDENTITY_ENABLED = "true"
} elseif (-not $IsLoopbackAddress) {
    # A previous local run may have left this variable in the shell. Never
    # inherit that demo setting for a non-loopback listener.
    $env:RISK_DEMO_IDENTITY_ENABLED = "false"
} elseif (-not $env:RISK_DEMO_IDENTITY_ENABLED) {
    $env:RISK_DEMO_IDENTITY_ENABLED = "true"
}

if (-not $IsLoopbackAddress) {
    $env:RISK_LOCAL_FILE_OPEN_ENABLED = "false"
} elseif (-not $env:RISK_LOCAL_FILE_OPEN_ENABLED) {
    $env:RISK_LOCAL_FILE_OPEN_ENABLED = "true"
}

if ($EnableDeveloperDebug) {
    $env:RISK_DEVELOPER_DEBUG_ENABLED = "true"
} elseif (-not $env:RISK_DEVELOPER_DEBUG_ENABLED) {
    $env:RISK_DEVELOPER_DEBUG_ENABLED = "false"
}

Write-Host ""
Write-Host "Starting Legal_Risk_Check backend..."
Write-Host "App:     src.main:app"
Write-Host "Address: http://$Address`:$Port"
Write-Host "Docs:    http://$Address`:$Port/docs"
Write-Host "OpenAPI: http://$Address`:$Port/openapi.json"
Write-Host "Qdrant:  $QdrantUrl"
Write-Host "MineU:   $env:MINEU_MODE"
Write-Host "Market:  live=$LiveMarketEnabled http=$HttpMarketEnabled"
Write-Host "Intel:   live=$LiveIntelligenceEnabled scheduler=$IntelligenceSchedulerEnabled feeds=$IntelligenceFeedMode"
Write-Host "Search:  enabled=$WebSearchEnabled provider=$WebSearchProvider"
Write-Host "Identity: demo=$env:RISK_DEMO_IDENTITY_ENABLED (production requires a gateway-signed identity)"
Write-Host "Local file open: enabled=$env:RISK_LOCAL_FILE_OPEN_ENABLED (loopback only)"
Write-Host "Developer debug: $env:RISK_DEVELOPER_DEBUG_ENABLED (local isolated scenarios only)"
if (-not $SkipDbCheck) {
    try {
        Invoke-WebRequest -Uri "$QdrantUrl/collections" -UseBasicParsing -TimeoutSec 3 | Out-Null
        Write-Host "Qdrant:  reachable"
    } catch {
        Write-Warning "Qdrant is not reachable at $QdrantUrl. Backend will still start; RAG/vector features may be unavailable until the database is running."
    }
}
Write-Host ""
Write-Host "Press Ctrl+C to stop."
Write-Host ""

& $Python -m uvicorn src.main:app @ReloadArgs --host $Address --port $Port
