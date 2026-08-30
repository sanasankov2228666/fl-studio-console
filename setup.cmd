@echo off
setlocal
set "PROJECT_ROOT=%~dp0"

where powershell.exe >nul 2>nul
if errorlevel 1 (
    echo PowerShell was not found. Windows PowerShell 5.1 or newer is required.
    exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%setup.ps1" %*
exit /b %errorlevel%
