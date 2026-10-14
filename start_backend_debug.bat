@echo off
setlocal

rem Developer-debug backend: isolated scenarios, live market quotes and RSS.
set "RISK_DEVELOPER_DEBUG_ENABLED=true"
set "EXTERNAL_RISK_LIVE_ENABLED=true"
set "EXTERNAL_RISK_HTTP_ENABLED=true"
set "EXTERNAL_RISK_INTELLIGENCE_ENABLED=true"
set "EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED=true"

set "DEBUG_PORT=%~1"
if not defined DEBUG_PORT (
    for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$port=8014; while (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { $port++ }; $port"`) do set "DEBUG_PORT=%%P"
)

if not defined DEBUG_PORT set "DEBUG_PORT=8014"
if not exist "%~dp0tmp" mkdir "%~dp0tmp" >nul 2>&1
> "%~dp0tmp\developer_debug_port.txt" echo %DEBUG_PORT%

echo Developer-debug backend will use port %DEBUG_PORT%.
echo Frontend will open with this backend address after it is ready.
start "DeveloperDebugFrontend" /b powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_debug_frontend.ps1" -BackendPort %DEBUG_PORT%

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_backend.ps1" ^
    -Port %DEBUG_PORT% ^
    -EnableDeveloperDebug ^
    -EnableLiveMarket ^
    -EnableLiveIntelligence ^
    -SkipDbCheck

echo.
echo Developer-debug backend has stopped. Press any key to close this window.
pause >nul
