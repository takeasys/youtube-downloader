@echo off
REM FFmpeg installer script
setlocal

set "TEMP_DIR=%TEMP%\ffmpeg-install"
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

echo Downloading latest FFmpeg (essentials build)...
powershell -Command "try { Invoke-WebRequest 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile '%TEMP_DIR%\ffmpeg.zip' -UseBasicParsing } catch { Write-Error 'Download failed'; exit 1 }"
if errorlevel 1 goto error

echo Extracting...
powershell -Command "try { Expand-Archive -Path '%TEMP_DIR%\ffmpeg.zip' -DestinationPath '%TEMP_DIR%' -Force } catch { Write-Error 'Extraction failed'; exit 1 }"
if errorlevel 1 goto error

echo Preparing install directory...
set "INSTALL_DIR="
set "INSTALL_TO_PROGRAMFILES=0"
mkdir "%ProgramFiles%\ffmpeg" 2>nul
if %errorlevel%==0 (
  set "INSTALL_TO_PROGRAMFILES=1"
  set "INSTALL_DIR=%ProgramFiles%\ffmpeg"
) else (
  echo No permission to write to Program Files, installing to user folder.
  set "INSTALL_DIR=%USERPROFILE%\ffmpeg"
  mkdir "%INSTALL_DIR%" 2>nul
)

echo Moving files...
for /d %%D in ("%TEMP_DIR%\ffmpeg-*") do (
  xcopy "%%~fD\*" "%INSTALL_DIR%\" /E /I /Y >nul
  goto moved
)
:moved

echo Adding to PATH...
if "%INSTALL_TO_PROGRAMFILES%"=="1" (
  rem attempt machine-wide PATH update (requires admin), fallback to user PATH
  setx PATH "%PATH%;%INSTALL_DIR%\bin" /M >nul 2>&1 || setx PATH "%PATH%;%INSTALL_DIR%\bin" >nul
) else (
  setx PATH "%PATH%;%INSTALL_DIR%\bin" >nul
)

echo Cleaning up...
rd /s /q "%TEMP_DIR%"

echo FFmpeg installed to %INSTALL_DIR%\bin and PATH updated.
echo You may need to restart your shell or computer for PATH changes to take effect.
exit /b 0

:error
echo Installation failed.
exit /b 1
