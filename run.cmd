@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
set "PYTHON=%PROJECT_ROOT%.venv-win\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo ConsoleSeq is not built. Run setup.cmd first.
    exit /b 1
)

"%PYTHON%" -c "import sys" >nul 2>nul
if errorlevel 1 (
    echo ConsoleSeq Windows environment is broken. Run setup.cmd to repair it.
    exit /b 1
)

"%PYTHON%" "%PROJECT_ROOT%main.py" %*
exit /b %errorlevel%
