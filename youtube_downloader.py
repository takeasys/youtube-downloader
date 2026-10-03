"""Simple Windows-friendly GUI for downloading YouTube videos using yt-dlp."""
from __future__ import annotations

import threading
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import logging
import re

LANGUAGE_STRINGS: dict[str, dict[str, str]] = {
    "zh": {
        "language_name": "繁體中文",
        "app_title": "YouTube 影片下載器",
        "url_label": "YouTube 網址：",
        "save_label": "儲存位置：",
        "browse_button": "瀏覽...",
        "paste_button": "貼上網址",
        "clear_button": "清除",
        "open_folder_button": "開啟資料夾",
        "download_button": "下載",
        "status_label": "狀態：",
        "language_label": "介面語言：",
        "status_log_label": "狀態日誌：",
        "details_log_label": "詳細日誌：",
        "mode_label": "下載模式：",
        "video_mode": "影片 (MP4)",
        "audio_mode": "音訊 (MP3)",
        "download_mp4_button": "下載 MP4",
        "download_mp3_button": "下載 MP3",
        "status_idle": "閒置",
        "status_downloading": "下載中...",
        "status_processing": "處理下載中...",
        "status_failed": "失敗",
        "status_completed": "完成",
        "status_progress": "下載中 {percent} | {speed} | 預估剩餘 {eta} 秒",
        "log_start": "開始下載到 {destination}...",
        "log_error": "錯誤：{error}",
        "log_success": "下載成功完成。",
        "warning_missing_url_title": "缺少網址",
        "warning_missing_url_body": "請貼上有效的 YouTube 連結。",
        "error_invalid_folder_title": "無效的資料夾",
        "error_invalid_folder_body": "無法建立資料夾：{error}",
    },
    "en": {
        "language_name": "English",
        "app_title": "YouTube Video Downloader",
        "url_label": "YouTube URL:",
        "save_label": "Save To:",
        "browse_button": "Browse...",
        "paste_button": "Paste URL",
        "clear_button": "Clear",
        "open_folder_button": "Open Folder",
        "download_button": "Download",
        "status_label": "Status:",
        "language_label": "Language:",
        "status_log_label": "Status Log:",
        "details_log_label": "Details Log:",
        "mode_label": "Download Mode:",
        "video_mode": "Video (MP4)",
        "audio_mode": "Audio (MP3)",
        "download_mp4_button": "Download MP4",
        "download_mp3_button": "Download MP3",
        "status_idle": "Idle",
        "status_downloading": "Downloading...",
        "status_processing": "Processing download...",
        "status_failed": "Failed",
        "status_completed": "Completed",
        "status_progress": "Downloading {percent} | {speed} | ETA {eta}s",
        "log_start": "Starting download to {destination}...",
        "log_error": "Error: {error}",
        "log_success": "Download finished successfully.",
        "warning_missing_url_title": "Missing URL",
        "warning_missing_url_body": "Please paste a valid YouTube link.",
        "error_invalid_folder_title": "Invalid Folder",
        "error_invalid_folder_body": "Cannot create directory: {error}",
    },
}

LANGUAGE_ORDER = list(LANGUAGE_STRINGS.keys())

try:
    import yt_dlp
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "yt-dlp is not installed. Install it with 'pip install yt-dlp'."
    ) from exc


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def bundled_ffmpeg_location() -> str | None:
    """Return the bundled FFmpeg directory when running as a packaged app."""
    if not getattr(sys, "frozen", False):
        return None

    ffmpeg_dir = Path(getattr(sys, "_MEIPASS")) / "ffmpeg"
    if not (ffmpeg_dir / "ffmpeg.exe").is_file() or not (ffmpeg_dir / "ffprobe.exe").is_file():
        raise FileNotFoundError("The bundled FFmpeg files are missing.")
    return str(ffmpeg_dir)


class UILogger:
    """Logger that redirects yt-dlp output to the UI log."""

    def __init__(self, ui_instance):
        self.ui_instance = ui_instance

    def _log(self, msg):
        clean_msg = strip_ansi_codes(msg)
        self.ui_instance.after(0, lambda: self.ui_instance._log_message(clean_msg))

    def debug(self, msg):
        self._log(f"[DEBUG] {msg}\n")

    def info(self, msg):
        self._log(f"[INFO] {msg}\n")

    def warning(self, msg):
        self._log(f"[WARNING] {msg}\n")

    def error(self, msg):
        self._log(f"[ERROR] {msg}\n")

    def critical(self, msg):
        self._log(f"[CRITICAL] {msg}\n")


class YouTubeDownloader(tk.Tk):
    """Minimal Tkinter client that wraps yt-dlp downloads."""

    def __init__(self) -> None:
        super().__init__()
        self.geometry("600x450")
        self.resizable(False, False)

        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.status_var = tk.StringVar()

        self.download_mode = tk.StringVar(value="video")  # "video" or "audio"

        self.language_code = "zh"
        self.language_display_names = {
            code: data["language_name"] for code, data in LANGUAGE_STRINGS.items()
        }
        self.display_name_to_code = {
            name: code for code, name in self.language_display_names.items()
        }
        self.language_display_var = tk.StringVar(value=self.language_display_names[self.language_code])
        self._status_context: tuple[str, dict[str, object]] = ("status_idle", {})

        self._build_ui()
        self._apply_language()

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        self.language_label = ttk.Label(self, text="")
        self.language_label.grid(row=0, column=1, sticky="e", **padding)
        self.language_selector = ttk.Combobox(
            self,
            textvariable=self.language_display_var,
            state="readonly",
            values=[self.language_display_names[code] for code in LANGUAGE_ORDER],
            width=12,
        )
        self.language_selector.grid(row=0, column=2, sticky="ew", **padding)
        self.language_selector.bind("<<ComboboxSelected>>", self._handle_language_change)

        self.url_label = ttk.Label(self, text="")
        self.url_label.grid(row=0, column=0, sticky="w", **padding)
        url_entry = ttk.Entry(self, textvariable=self.url_var, width=42)
        url_entry.grid(row=1, column=0, columnspan=3, sticky="ew", **padding)
        url_entry.focus()
        self.paste_button = ttk.Button(self, text="", width=12, command=self._paste_url)
        self.paste_button.grid(row=2, column=1, sticky="ew", **padding)
        self.clear_button = ttk.Button(self, text="", width=12, command=self._clear_url)
        self.clear_button.grid(row=2, column=2, sticky="ew", **padding)

        self.save_label = ttk.Label(self, text="")
        self.save_label.grid(row=3, column=0, sticky="w", **padding)
        ttk.Entry(self, textvariable=self.output_dir_var, width=42).grid(
            row=4, column=0, columnspan=3, sticky="ew", **padding
        )
        self.browse_button = ttk.Button(self, text="", width=12, command=self._select_directory)
        self.browse_button.grid(
            row=5, column=1, sticky="ew", **padding
        )
        self.open_folder_button = ttk.Button(self, text="", width=12, command=self._open_directory)
        self.open_folder_button.grid(row=5, column=2, sticky="ew", **padding)

        self.download_mp4_button = ttk.Button(self, text="", width=12, command=lambda: self._handle_download("video"))
        self.download_mp4_button.grid(row=6, column=1, sticky="ew", **padding)
        self.download_mp3_button = ttk.Button(self, text="", width=12, command=lambda: self._handle_download("audio"))
        self.download_mp3_button.grid(row=6, column=2, sticky="ew", **padding)

        self.status_label = ttk.Label(self, text="")
        self.status_label.grid(row=7, column=0, sticky="w", **padding)
        ttk.Label(self, textvariable=self.status_var).grid(row=7, column=1, columnspan=2, sticky="w", **padding)
        self.status_indicator = ttk.Label(self, text="")
        self.status_indicator.grid(row=7, column=2, sticky="e", **padding)

        # Status log
        self.status_log_label = ttk.Label(self, text="")
        self.status_log_label.grid(row=8, column=0, sticky="w", **padding)
        self.status_log = tk.Text(self, height=4, state="disabled", wrap="word", background="#222222", foreground="#00FF00")
        self.status_log.grid(row=9, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 6))

        # Details log (hidden)
        self.log = tk.Text(self, height=8, state="disabled", wrap="word", background="#111111", foreground="#00FF00")

        self.grid_rowconfigure(9, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

    def _apply_language(self) -> None:
        strings = LANGUAGE_STRINGS[self.language_code]
        self.title(strings["app_title"])
        self.url_label.configure(text=strings["url_label"])
        self.save_label.configure(text=strings["save_label"])
        self.browse_button.configure(text=strings["browse_button"])
        self.paste_button.configure(text=strings["paste_button"])
        self.clear_button.configure(text=strings["clear_button"])
        self.open_folder_button.configure(text=strings["open_folder_button"])
        self.download_mp4_button.configure(text=strings["download_mp4_button"])
        self.download_mp3_button.configure(text=strings["download_mp3_button"])
        self.status_label.configure(text=strings["status_label"])
        self.language_label.configure(text=strings["language_label"])
        # Update log labels
        self.status_log_label.configure(text=strings["status_log_label"])
        language_values = [self.language_display_names[code] for code in LANGUAGE_ORDER]
        self.language_selector.configure(values=language_values)
        self.language_selector.set(self.language_display_names[self.language_code])
        self._refresh_status()

    def _handle_language_change(self, _event: tk.Event | None = None) -> None:
        selection = self.language_selector.get()
        new_code = self.display_name_to_code.get(selection, self.language_code)
        if new_code != self.language_code:
            self.language_code = new_code
            self._apply_language()

    def _text(self, key: str, **kwargs: object) -> str:
        template = LANGUAGE_STRINGS[self.language_code][key]
        return template.format(**kwargs)

    def _set_status(self, key: str, **kwargs: object) -> None:
        self._status_context = (key, dict(kwargs))
        self.status_var.set(self._text(key, **kwargs))
        if key == "status_completed":
            self.status_indicator.configure(text="●", foreground="green")
        else:
            self.status_indicator.configure(text="")

    def _refresh_status(self) -> None:
        if self._status_context:
            key, kwargs = self._status_context
            self.status_var.set(self._text(key, **kwargs))
            if key == "status_completed":
                self.status_indicator.configure(text="●", foreground="green")
            else:
                self.status_indicator.configure(text="")

    def _paste_url(self) -> None:
        try:
            clipboard_content = self.clipboard_get()
            self.url_var.set(clipboard_content.strip())
        except tk.TclError:
            # Clipboard empty or error
            pass

    def _clear_url(self) -> None:
        self.url_var.set("")

    def _select_directory(self) -> None:
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)

    def _open_directory(self) -> None:
        import subprocess
        import platform
        path = self.output_dir_var.get()
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open directory: {e}")

    def _handle_download(self, mode: str) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(
                self._text("warning_missing_url_title"),
                self._text("warning_missing_url_body"),
            )
            return

        output_dir = Path(self.output_dir_var.get()).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            messagebox.showerror(
                self._text("error_invalid_folder_title"),
                self._text("error_invalid_folder_body", error=err),
            )
            return

        self._status_log_message(self._text("log_start", destination=output_dir) + "\n")
        self._set_status("status_downloading")
        self.download_mp4_button.configure(state="disabled")
        self.download_mp3_button.configure(state="disabled")

        thread = threading.Thread(
            target=self._download_video,
            args=(url, output_dir, mode),
            daemon=True,
        )
        thread.start()

    def _download_video(self, url: str, output_dir: Path, mode: str) -> None:
        def progress_hook(data: dict[str, str]) -> None:
            if data.get("status") == "downloading":
                percent = strip_ansi_codes(data.get("_percent_str", "0%")).strip()
                speed = strip_ansi_codes(data.get("_speed_str", "0KiB/s")).strip()
                eta = strip_ansi_codes(data.get("_eta_str", "?")).strip()
                self._async_update_status("status_progress", percent=percent, speed=speed, eta=eta)
            elif data.get("status") == "finished":
                self._async_update_status("status_processing")

        ui_logger = UILogger(self)

        if mode == "audio":
            ydl_opts = {
                "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook],
                "noplaylist": True,
                "ignoreerrors": False,
                "retries": 3,
                "format": "bestaudio/best",
                "logger": ui_logger,
                "logtostderr": False,
                "overwrites": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        else:  # video
            ydl_opts = {
                "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook],
                "noplaylist": True,
                "ignoreerrors": False,
                "retries": 3,
                "format": "bestvideo*+bestaudio/best",
                "merge_output_format": "mp4",
                "logger": ui_logger,
                "logtostderr": False,
                "overwrites": True,
                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4",
                    }
                ],
            }

        try:
            ffmpeg_dir = bundled_ffmpeg_location()
            if ffmpeg_dir is not None:
                ydl_opts["ffmpeg_location"] = ffmpeg_dir
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as exc:
            self._async_update_status("status_failed")
            self._status_log_message(self._text("log_error", error=exc) + "\n")
        else:
            self._async_update_status("status_completed")
            self._status_log_message(self._text("log_success") + "\n")
        finally:
            self.after(0, lambda: self.download_mp4_button.configure(state="normal"))
            self.after(0, lambda: self.download_mp3_button.configure(state="normal"))

    def _log_message(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _status_log_message(self, message: str) -> None:
        self.status_log.configure(state="normal")
        self.status_log.insert("end", message)
        self.status_log.see("end")
        self.status_log.configure(state="disabled")

    def _async_update_status(self, key: str, **kwargs: object) -> None:
        self.after(0, lambda: self._set_status(key, **kwargs))
        self.after(0, lambda: self._status_log_message(self._text(key, **kwargs) + "\n"))


def main() -> None:
    app = YouTubeDownloader()
    app.mainloop()


if __name__ == "__main__":
    main()
