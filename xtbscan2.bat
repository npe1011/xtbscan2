@echo off
cd /d "%~dp0"

where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: 'uv' is not installed or not found in PATH.
    echo Please install 'uv' first to run this application.
    echo Visit: https://docs.astral.sh/uv/
    echo.
    pause
    exit /b 1
)

uv sync

powershell -WindowStyle Hidden -Command "Start-Process uv -ArgumentList 'run', 'pythonw', 'src/gui/app.py' -WindowStyle Hidden"
