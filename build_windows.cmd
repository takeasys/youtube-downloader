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

python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    exit /b 1
)

python -m pip install --upgrade yt-dlp pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install yt-dlp and PyInstaller.
    exit /b 1
)

set "FFMPEG_ROOT=%CD%\build\ffmpeg"
set "FFMPEG_BIN=%FFMPEG_ROOT%\bin"
if exist "%FFMPEG_BIN%\ffmpeg.exe" if exist "%FFMPEG_BIN%\ffprobe.exe" goto ffmpeg_ready

echo [INFO] Downloading FFmpeg for bundling...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference = 'Stop';" ^
    "$root = '%FFMPEG_ROOT%';" ^
    "$extract = Join-Path $root 'extract';" ^
    "$zip = Join-Path $root 'ffmpeg.zip';" ^
    "New-Item -ItemType Directory -Force -Path $root | Out-Null;" ^
    "if (Test-Path $extract) { Remove-Item $extract -Recurse -Force };" ^
    "New-Item -ItemType Directory -Force -Path $extract | Out-Null;" ^
    "Invoke-WebRequest 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $zip;" ^
    "Expand-Archive -Path $zip -DestinationPath $extract -Force;" ^
    "$bin = Get-ChildItem $extract -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'bin\ffmpeg.exe') } | Select-Object -First 1;" ^
    "if (-not $bin) { throw 'The downloaded FFmpeg archive did not contain ffmpeg.exe.' };" ^
    "$bin = Join-Path $bin.FullName 'bin';" ^
    "if (Test-Path '%FFMPEG_BIN%') { Remove-Item '%FFMPEG_BIN%' -Recurse -Force };" ^
    "New-Item -ItemType Directory -Force -Path '%FFMPEG_BIN%' | Out-Null;" ^
    "Copy-Item (Join-Path $bin 'ffmpeg.exe') '%FFMPEG_BIN%\ffmpeg.exe';" ^
    "Copy-Item (Join-Path $bin 'ffprobe.exe') '%FFMPEG_BIN%\ffprobe.exe';" ^
    "Get-ChildItem $bin -Filter '*.dll' | Copy-Item -Destination '%FFMPEG_BIN%';" ^
    "Remove-Item $extract -Recurse -Force;" ^
    "Remove-Item $zip -Force"
if errorlevel 1 (
    echo [ERROR] Failed to download or stage FFmpeg.
    exit /b 1
)

:ffmpeg_ready
REM Keep only FFmpeg tools and their DLL dependencies in the staging directory.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Get-ChildItem '%FFMPEG_BIN%' -File | Where-Object { $_.Name -notmatch '^(ffmpeg|ffprobe)\.exe$' -and $_.Extension -ne '.dll' } | Remove-Item -Force"
if errorlevel 1 (
    echo [ERROR] Failed to clean the FFmpeg staging folder.
    exit /b 1
)

if not exist "%FFMPEG_BIN%\ffmpeg.exe" (
    echo [ERROR] FFmpeg was not found in the staging folder.
    exit /b 1
)

if not exist "%FFMPEG_BIN%\ffprobe.exe" (
    echo [ERROR] FFprobe was not found in the FFmpeg staging folder.
    exit /b 1
)

python -m PyInstaller --noconfirm youtube_downloader.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller failed. See output above for details.
    exit /b 1
)

echo [INFO] Build complete. Find the exe under dist\youtube_downloader.exe
echo [INFO] FFmpeg and FFprobe are bundled; no separate FFmpeg install is needed.
endlocal
