@echo off
rem One-shot bootstrap + launch for Windows. Safe to re-run; reuses the venv.
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python 3.11+ is required. Install from https://www.python.org/downloads/ and re-run.
    exit /b 1
)

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv || exit /b 1
)
call .venv\Scripts\activate.bat

echo Installing dictate with STT + Windows extras (first run takes a few minutes)...
python -m pip install --quiet --upgrade pip
pip install --quiet -e ".[stt,windows]" || exit /b 1

echo.
echo Starting dictate. Gray tray dot = idle, red = recording. Hotkey: Ctrl+Alt+D
echo (first run also downloads the Whisper model)
python -m dictate %*
