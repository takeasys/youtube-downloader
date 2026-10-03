# YouTube Downloader GUI

Simple Tkinter client that downloads single YouTube videos via `yt-dlp`.

## Requirements

- Python 3.11+ (Windows x64 installer from python.org works well)
- `yt-dlp` (installed automatically during build)
- `pyinstaller` (installed automatically during build)
- Internet access during the build to download FFmpeg

## Run from Source

```bash
pip install yt-dlp
python youtube_downloader.py
```

For audio conversion and MP4 processing when running from source, install
FFmpeg separately and make `ffmpeg` and `ffprobe` available on `PATH`.

## Build Windows Executable

1. Open **Command Prompt** on a Windows machine.
2. Navigate to the project directory.
3. Run:
   ```cmd
   build_windows.cmd
   ```
4. The bundled executable appears under `dist/youtube_downloader.exe`.

The build downloads FFmpeg, FFprobe, and their required DLLs into the ignored
`build/ffmpeg` staging folder and bundles them into the one-file executable.
The resulting app does not require a separate FFmpeg installation. The build
machine needs internet access when FFmpeg has not already been staged.

FFmpeg is a third-party component. Review the license and redistribution terms
for the downloaded build before distributing the executable to others.

> PyInstaller cannot cross-compile. Run the script on Windows to produce a Windows binary.
