@echo off
setlocal
echo [INFO] Starting Windows build for youtube_downloader.py

REM Ensure script runs from its own directory
cd /d "%~dp0"

if not exist "%LocalAppData%\Programs\Python" (
    echo [WARN] Python installation not detected in default locations.
    echo Install Python 3.11+ from https://www.python.org/downloads/windows/ and rerun.
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] python not found in PATH.
    echo Add Python to PATH or run this script from the "Python Command Prompt".
    exit /b 1
)

python -m pip install --upgrade pip >nul
python -m pip install --upgrade yt-dlp pyinstaller >nul

pyinstaller --onefile --noconsole youtube_downloader.py
if errorlevel 1 (
    echo [ERROR] PyInstaller failed. See output above for details.
    exit /b 1
)

echo [INFO] Build complete. Find the exe under dist\youtube_downloader.exe
endlocal
