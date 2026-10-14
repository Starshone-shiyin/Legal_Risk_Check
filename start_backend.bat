@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_backend.ps1" %*

echo.
echo Backend process has stopped. Press any key to close this window.
pause >nul
