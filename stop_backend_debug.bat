@echo off
setlocal

set "DEBUG_PORT=%~1"

if defined DEBUG_PORT (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_backend_debug.ps1" -Port %DEBUG_PORT%
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_backend_debug.ps1"
)

echo.
echo Developer-debug backend shutdown check completed. Press any key to close this window.
pause >nul
