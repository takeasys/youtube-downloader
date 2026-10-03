# YouTube Downloader GUI

Simple Tkinter client that downloads single YouTube videos via `yt-dlp`.

## Requirements

- Python 3.11+ (Windows x64 installer from python.org works well)
- `yt-dlp` (installed automatically during build)
- `pyinstaller` (installed automatically during build)

## Run from Source

```bash
pip install yt-dlp
python youtube_downloader.py
```

## Build Windows Executable

1. Open **Command Prompt** on a Windows machine.
2. Navigate to the project directory.
3. Run:
   ```cmd
   build_windows.cmd
   ```
4. The bundled executable appears under `dist/youtube_downloader.exe`.

> PyInstaller cannot cross-compile. Run the script on Windows to produce a Windows binary.
