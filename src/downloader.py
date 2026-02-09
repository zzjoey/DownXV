"""Download worker thread wrapping yt-dlp."""

import glob
import os
import shutil
import tempfile

import yt_dlp
from PySide6.QtCore import QThread, Signal


class _CancelledError(Exception):
    """Raised inside yt-dlp hooks to abort a cancelled download."""


class _QuietLogger:
    """Suppress all yt-dlp console output."""

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


class DownloadWorker(QThread):
    """Background thread that downloads a video from an X/Twitter post."""

    progress = Signal(int)
    status_update = Signal(str)
    finished_ok = Signal(str)
    error = Signal(str)

    # Quality → yt-dlp format string mapping
    FORMAT_MAP = {
        "Best (default)": "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "Audio only": "bestaudio/best",
    }

    def __init__(
        self, url: str, save_path: str, quality: str, cookie_browser: str
    ) -> None:
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.quality = quality
        self.cookie_browser = cookie_browser  # "none", "chrome", "firefox", "edge"
        self._stream_index = 0
        self._total_streams = 1
        self._tmp_dir: str | None = None
        self._cancelled = False

    def cleanup_tmp(self) -> None:
        """Remove the temporary directory if it still exists."""
        d = self._tmp_dir
        if d and os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
        self._tmp_dir = None

    def cancel(self) -> None:
        """Request graceful cancellation of the download."""
        self._cancelled = True

    def run(self) -> None:
        tmp_dir = tempfile.mkdtemp(prefix=".downxv_", dir=self.save_path)
        self._tmp_dir = tmp_dir
        try:
            self.status_update.emit("Extracting video info...")

            format_str = self.FORMAT_MAP.get(
                self.quality, "bestvideo+bestaudio/best"
            )

            ydl_opts = {
                "format": format_str,
                "outtmpl": os.path.join(tmp_dir, "%(title).100s.%(ext)s"),
                "merge_output_format": "mp4",
                "progress_hooks": [self._progress_hook],
                "concurrent_fragment_downloads": 8,
                "retries": 5,
                "fragment_retries": 5,
                "quiet": True,
                "no_warnings": True,
                "ignoreerrors": True,
                "logger": _QuietLogger(),
            }

            if self.cookie_browser != "none":
                ydl_opts["cookiesfrombrowser"] = (self.cookie_browser,)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

                if info is None:
                    self.error.emit(
                        "Could not extract video information from this URL."
                    )
                    return

                # Handle both single videos and playlists (multi-video tweets)
                has_video = bool(info.get("formats"))
                entries = info.get("entries")
                if entries:
                    has_video = True

                if not has_video:
                    self.error.emit(
                        "No video found in this post. "
                        "It may only contain text or images."
                    )
                    return

                title = info.get("title", "video")
                video_count = 1
                if entries:
                    video_count = info.get("playlist_count", len(list(entries)))
                    self.status_update.emit(
                        f"Downloading {video_count} video(s): {title[:60]}"
                    )
                else:
                    self.status_update.emit(f"Downloading: {title[:60]}")

                # Set up combined progress tracking across streams
                streams_per_video = 2 if "+" in format_str else 1
                self._total_streams = video_count * streams_per_video
                self._stream_index = 0

                # Re-extract with download=True (entries iterator is consumed)
                ydl.download([self.url])

            # Move only final files (mp4/m4a) to the user's save directory
            moved: list[str] = []
            for f in glob.glob(os.path.join(tmp_dir, "*")):
                if f.endswith((".part", ".ytdl")):
                    continue
                dest = os.path.join(self.save_path, os.path.basename(f))
                shutil.move(f, dest)
                moved.append(dest)

            if moved:
                self.finished_ok.emit(moved[0])
            else:
                self.error.emit(
                    "No video found in this post. "
                    "It may only contain text or images."
                )
                return

        except _CancelledError:
            return
        except yt_dlp.utils.DownloadError as e:
            if self._cancelled:
                return
            self.error.emit(self._clean_error(str(e)))
        except Exception as e:
            if self._cancelled:
                return
            self.error.emit(f"Unexpected error: {e}")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            self._tmp_dir = None

    def _progress_hook(self, d: dict) -> None:
        if self._cancelled:
            raise _CancelledError()
        status = d.get("status")

        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed")  # bytes/s or None
            eta = d.get("eta")  # seconds or None

            if total and total > 0:
                stream_pct = downloaded / total
                # Each stream gets an equal share of 0–95%
                share = 95.0 / self._total_streams
                overall = int(self._stream_index * share + stream_pct * share)
                self.progress.emit(min(overall, 95))

                parts = [
                    f"{self._fmt_size(downloaded)} / {self._fmt_size(total)}"
                ]
                if speed and speed > 0:
                    parts.append(f"{self._fmt_size(speed)}/s")
                if eta is not None and eta >= 0:
                    parts.append(f"ETA {self._fmt_time(eta)}")

                self.status_update.emit("  ·  ".join(parts))
            else:
                parts = [self._fmt_size(downloaded)]
                if speed and speed > 0:
                    parts.append(f"{self._fmt_size(speed)}/s")
                self.status_update.emit("  ·  ".join(parts))

        elif status == "finished":
            self._stream_index += 1
            done_pct = int(self._stream_index * 95.0 / self._total_streams)
            self.progress.emit(min(done_pct, 95))

            if self._stream_index >= self._total_streams:
                self.status_update.emit("Merging video and audio...")
            elif self._total_streams == 2 and self._stream_index == 1:
                self.status_update.emit("Downloading audio track...")

    @staticmethod
    def _fmt_size(b: float) -> str:
        if b >= 1024 * 1024 * 1024:
            return f"{b / (1024 ** 3):.1f} GB"
        if b >= 1024 * 1024:
            return f"{b / (1024 ** 2):.1f} MB"
        if b >= 1024:
            return f"{b / 1024:.0f} KB"
        return f"{b:.0f} B"

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        seconds = int(seconds)
        if seconds < 60:
            return f"{seconds}s"
        m, s = divmod(seconds, 60)
        if m < 60:
            return f"{m}m {s}s"
        h, m = divmod(m, 60)
        return f"{h}h {m}m"

    @staticmethod
    def _clean_error(raw: str) -> str:
        msg = raw.removeprefix("ERROR: ")

        if "is not a valid URL" in msg or "Unsupported URL" in msg:
            return "Invalid URL. Please paste a valid X/Twitter post link."
        if "HTTP Error 404" in msg or "Unable to download" in msg:
            return "Post not found. It may have been deleted or the URL is wrong."
        if "HTTP Error 403" in msg:
            return "Access denied. The post may be private or age-restricted."
        if "No video could be found" in msg:
            return (
                "No video found. Try selecting a browser cookie source "
                "(Chrome/Firefox) — most X videos require authentication."
            )
        if "No video" in msg.lower():
            return "No video found in this post."
        if "urlopen error" in msg or "timed out" in msg:
            return "Network error. Please check your internet connection."
        if "Sign in" in msg or "login" in msg.lower():
            return (
                "This post requires authentication. "
                "Select Chrome or Firefox as cookie source."
            )
        if "Operation not permitted" in msg and "Cookies" in msg:
            return (
                "Cannot access browser cookies. "
                "Try Chrome or Firefox instead of Safari, "
                "or grant Full Disk Access in System Settings."
            )

        return msg
