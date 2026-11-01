"""YouTube Lite: Desktop App with HTML5 Feed and Embedded Native MPV Player matching the exact visual layout."""
import gc
import http.server
import json
import locale
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import urllib.request

# Chromium flags optimized for memory savings and background feed
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-features=WebGPU,Vulkan "
    "--disable-webgpu "
    "--ignore-gpu-blocklist "
    "--enable-gpu-rasterization "
    "--autoplay-policy=no-user-gesture-required "
    "--renderer-process-limit=2 "
    "--js-flags=--max-old-space-size=128 "
    "--disk-cache-size=33554432 "
    "--media-cache-size=33554432 "
    "--disable-logging "
    "--disable-speech-api"
)

from PySide6.QtCore import Qt, QUrl, QStandardPaths, QTimer, QObject, Signal, QByteArray, QSize
from PySide6.QtGui import QPixmap, QImage, QCursor, QIcon, QPainter, QShortcut, QKeySequence
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QComboBox, QFrame, QStackedWidget, QMessageBox,
    QScrollArea, QMenu,
)

APP_NAME = "YouTube Lite"
_DLL_HANDLES = []

HEROICONS = {
    "back": '<path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18"/>',
    "play": '<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-1.079 1.16-1.756 2.097-1.227l11.249 6.347c.96.542.96 1.912 0 2.454L7.347 19.574c-.937.529-2.097-.148-2.097-1.227V5.653Z"/>',
    "pause": '<path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25v13.5m-7.5-13.5v13.5"/>',
    "bookmark": '<path stroke-linecap="round" stroke-linejoin="round" d="M17.25 21 12 17.25 6.75 21V5.25A2.25 2.25 0 0 1 9 3h6a2.25 2.25 0 0 1 2.25 2.25V21Z"/>',
    "bookmark-filled": '<path fill="currentColor" stroke-linecap="round" stroke-linejoin="round" d="M17.25 21 12 17.25 6.75 21V5.25A2.25 2.25 0 0 1 9 3h6a2.25 2.25 0 0 1 2.25 2.25V21Z"/>',
    "download": '<path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M7.5 12 12 16.5m0 0 4.5-4.5M12 16.5V3"/>',
    "fullscreen": '<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9V5.25c0-.828.672-1.5 1.5-1.5H9m6 0h3.75c.828 0 1.5.672 1.5 1.5V9m0 6v3.75c0 .828-.672 1.5-1.5 1.5H15m-6 0H5.25a1.5 1.5 0 0 1-1.5-1.5V15"/>',
    "film": '<path stroke-linecap="round" stroke-linejoin="round" d="M6 3v18M18 3v18M3 9h3m-3 6h3m12-6h3m-3 6h3M5.25 3h13.5A2.25 2.25 0 0 1 21 5.25v13.5A2.25 2.25 0 0 1 18.75 21H5.25A2.25 2.25 0 0 1 3 18.75V5.25A2.25 2.25 0 0 1 5.25 3Z"/>',
    "chat": '<path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12c0 4.556 4.365 8.25 9.75 8.25.759 0 1.498-.073 2.207-.211 1.294.869 2.866 1.415 4.555 1.455a9.73 9.73 0 0 1-.996-3.164c2.12-1.51 3.484-3.81 3.484-6.33 0-4.556-4.365-8.25-9.75-8.25S2.25 7.444 2.25 12Z"/>',
    "live": '<path stroke-linecap="round" stroke-linejoin="round" d="M8.288 15.712a5.25 5.25 0 0 1 0-7.424m7.424 0a5.25 5.25 0 0 1 0 7.424M5.636 18.364a9 9 0 0 1 0-12.728m12.728 0a9 9 0 0 1 0 12.728M12 12h.008v.008H12V12Z"/>',
    "clock": '<path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2m5-2a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>',
    "like": '<path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21H4.875A1.875 1.875 0 0 1 3 19.125v-5.25C3 12.839 3.84 12 4.875 12H7.5m0 9V12m0 9h9.375c.95 0 1.76-.686 1.916-1.623l.875-5.25A1.94 1.94 0 0 0 17.75 12H14.25l.46-3.684a2.25 2.25 0 0 0-2.232-2.529L7.5 12"/>',
    "loading": '<path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2m5-2a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>',
}


def heroicon(name, color="#f0f2f7", size=18):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" color="{color}" stroke-width="1.5">{HEROICONS[name]}</svg>'
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter)
    painter.end()
    return QIcon(pixmap)


def icon_label(name, color="#8b93a7", size=14):
    label = QLabel()
    label.setFixedSize(size, size)
    label.setPixmap(heroicon(name, color, size).pixmap(QSize(size, size)))
    label.setStyleSheet("background: transparent;")
    return label


def icon_text_row(name, text, color="#8b93a7"):
    row = QHBoxLayout()
    row.setSpacing(4)
    row.addWidget(icon_label(name, color))
    row.addWidget(text)
    row.addStretch()
    return row


def resource_root():
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def setup_native_path():
    """Make libmpv and yt-dlp discoverable in source and packaged modes."""
    executable_root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    paths = [executable_root / "tools", executable_root, resource_root() / "tools", resource_root()]
    os.environ["PATH"] = os.pathsep.join(str(p) for p in paths) + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        for p in paths:
            if p.is_dir():
                _DLL_HANDLES.append(os.add_dll_directory(str(p)))


def find_ytdlp_binary():
    """Locate yt-dlp binary in tools or system PATH."""
    executable_root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    candidates = [
        executable_root / "tools" / "yt-dlp.exe",
        executable_root / "yt-dlp.exe",
        resource_root() / "tools" / "yt-dlp.exe",
        resource_root() / "yt-dlp.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    found = shutil.which("yt-dlp")
    return found or "yt-dlp"


def find_ffmpeg_binary():
    """Locate ffmpeg binary in tools, execution root, or system PATH."""
    executable_root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    candidates = [
        executable_root / "tools" / "ffmpeg.exe",
        executable_root / "ffmpeg.exe",
        resource_root() / "tools" / "ffmpeg.exe",
        resource_root() / "ffmpeg.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    found = shutil.which("ffmpeg")
    return found or "ffmpeg"


def find_ffmpeg_dir():
    """Locate directory containing ffmpeg binary for yt-dlp --ffmpeg-location."""
    bin_path = find_ffmpeg_binary()
    if bin_path and Path(bin_path).is_file():
        return str(Path(bin_path).parent)
    return "tools"


def display_time(seconds):
    try:
        seconds = max(0, int(float(seconds or 0)))
        return f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}" if seconds >= 3600 else f"{seconds // 60:02d}:{seconds % 60:02d}"
    except (TypeError, ValueError, OverflowError):
        return "00:00"


APP_DATA_DIR = None
BOOKMARKS_FILE = None
HISTORY_FILE = None


def init_app_data_dir():
    """Initialize data directory paths. Safe fallback if called before QApplication."""
    global APP_DATA_DIR, BOOKMARKS_FILE, HISTORY_FILE
    if QApplication.instance():
        loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        APP_DATA_DIR = Path(loc) if loc else (Path.home() / ".youtube_lite")
    else:
        APP_DATA_DIR = Path.home() / ".youtube_lite"
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    BOOKMARKS_FILE = APP_DATA_DIR / "bookmarked_channels.json"
    HISTORY_FILE = APP_DATA_DIR / "history_items.json"


def load_bookmarks():
    if BOOKMARKS_FILE is None:
        init_app_data_dir()
    if BOOKMARKS_FILE and BOOKMARKS_FILE.exists():
        try:
            return json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return [
        {"name": "Bro Code", "url": "https://www.youtube.com/@BroCodez"},
        {"name": "Programming with Mosh", "url": "https://www.youtube.com/@programmingwithmosh"},
        {"name": "Fireship", "url": "https://www.youtube.com/@Fireship"},
    ]


def save_bookmarks(items):
    if BOOKMARKS_FILE is None:
        init_app_data_dir()
    try:
        if BOOKMARKS_FILE:
            BOOKMARKS_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def load_history():
    if HISTORY_FILE is None:
        init_app_data_dir()
    if HISTORY_FILE and HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_history(items):
    if HISTORY_FILE is None:
        init_app_data_dir()
    try:
        if HISTORY_FILE:
            HISTORY_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def fetch_youtube_feed(target: str, is_channel: bool = False, count: int = 18):
    ytdlp_bin = find_ytdlp_binary()
    if is_channel:
        channel_target = target
        if not channel_target.startswith("http"):
            if channel_target.startswith("@"):
                channel_target = f"https://www.youtube.com/{channel_target}/videos"
            else:
                channel_target = f"https://www.youtube.com/@{channel_target}/videos"
        cmd = [
            ytdlp_bin,
            "--dump-json",
            "--flat-playlist",
            "--playlist-end", str(count),
            "--no-warnings",
            channel_target,
        ]
    else:
        cmd = [
            ytdlp_bin,
            "--dump-json",
            "--flat-playlist",
            "--playlist-end", str(count),
            "--no-warnings",
            f"ytsearch{count}:{target}",
        ]

    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags,
        )

        results = []
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                vid_id = data.get("id") or ""
                title = data.get("title") or "Tanpa Judul"
                url = data.get("url") or (f"https://www.youtube.com/watch?v={vid_id}" if vid_id else "")
                channel = data.get("channel") or data.get("uploader") or "YouTube"
                channel_url = data.get("channel_url") or data.get("uploader_url") or ""
                if not channel_url and data.get("uploader_id"):
                    channel_url = f"https://www.youtube.com/{data['uploader_id']}"

                dur_str = data.get("duration_string")
                if not dur_str and data.get("duration"):
                    dur_str = display_time(data.get("duration"))
                if not dur_str:
                    dur_str = "--:--"

                thumb_url = ""
                thumbnails = data.get("thumbnails")
                if thumbnails and isinstance(thumbnails, list):
                    thumb_url = thumbnails[-1].get("url", "")
                if not thumb_url and data.get("thumbnail"):
                    thumb_url = data.get("thumbnail")
                if not thumb_url and vid_id:
                    thumb_url = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

                is_live_status = bool(
                    data.get("is_live")
                    or data.get("live_status") == "is_live"
                    or dur_str == "--:--"
                )
                if vid_id:
                    results.append({
                        "id": vid_id,
                        "title": title,
                        "url": url,
                        "channel": channel,
                        "channel_url": channel_url,
                        "duration": dur_str,
                        "thumbnail": thumb_url,
                        "is_live": is_live_status,
                    })
            except json.JSONDecodeError:
                continue

        proc.wait()
        return results
    except Exception as exc:
        print("Error running yt-dlp:", exc)
        return []


def fetch_video_comments(video_id: str, count: int = 25):
    ytdlp_bin = find_ytdlp_binary()
    cmd = [
        ytdlp_bin,
        "--dump-json",
        "--write-comments",
        "--playlist-end", "1",
        "--extractor-args", f"youtube:comment_sort=top;max_comments={count}",
        "--no-warnings",
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags,
        )
        stdout, _ = proc.communicate(timeout=20)
        if stdout:
            data = json.loads(stdout)
            raw_comments = data.get("comments") or []
            results = []
            for c in raw_comments[:count]:
                results.append({
                    "id": c.get("id"),
                    "author": c.get("author") or "Pengguna",
                    "text": c.get("text") or "",
                    "like_count": c.get("like_count") or 0,
                    "time_text": c.get("_time_text") or "",
                })
            return results
    except Exception as exc:
        print("Error fetching comments:", exc)
    return []


class BridgeSignals(QObject):
    play_requested = Signal(dict)
    related_videos_loaded = Signal(list)
    thumbnail_loaded = Signal(str, bytes)
    comments_loaded = Signal(list)


signals = BridgeSignals()


class CommentCard(QFrame):
    def __init__(self, comment_data, parent=None):
        super().__init__(parent)
        self.setObjectName("commentCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        author_lbl = QLabel(comment_data.get("author", "Pengguna"))
        author_lbl.setObjectName("commentAuthor")
        top_row.addWidget(author_lbl)

        time_lbl = QLabel(comment_data.get("time_text", ""))
        time_lbl.setObjectName("commentTime")
        top_row.addWidget(time_lbl)
        top_row.addStretch()
        layout.addLayout(top_row)

        text_lbl = QLabel(comment_data.get("text", ""))
        text_lbl.setObjectName("commentText")
        text_lbl.setWordWrap(True)
        layout.addWidget(text_lbl)

        likes = comment_data.get("like_count") or 0
        if likes > 0:
            like_lbl = QLabel(f"{likes:,}")
            like_lbl.setObjectName("commentLikes")
            layout.addLayout(icon_text_row("like", like_lbl, "#ffb800"))


class RelatedVideoCard(QFrame):
    def __init__(self, video_data, on_click_callback, parent=None):
        super().__init__(parent)
        self.video_data = video_data
        self.on_click_callback = on_click_callback
        self.setObjectName("relatedCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(10)

        # Thumbnail box (100x56)
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(100, 56)
        self.thumb_label.setObjectName("relatedThumb")
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setPixmap(heroicon("play", "#6b7280", 22).pixmap(QSize(22, 22)))
        layout.addWidget(self.thumb_label)

        # Details
        details = QVBoxLayout()
        details.setSpacing(2)
        details.setContentsMargins(0, 0, 0, 0)

        title_text = video_data.get("title", "Video")
        title_lbl = QLabel(title_text)
        title_lbl.setObjectName("relatedTitle")
        title_lbl.setWordWrap(True)
        title_lbl.setToolTip(title_text)
        title_lbl.setMaximumHeight(36)

        ch_lbl = QLabel(video_data.get("channel", "YouTube"))
        ch_lbl.setObjectName("relatedChannel")

        dur_lbl = QLabel(f"{video_data.get('duration', '--:--')}")
        dur_lbl.setObjectName("relatedDuration")

        details.addWidget(title_lbl)
        details.addWidget(ch_lbl)
        details.addLayout(icon_text_row("clock", dur_lbl, "#ffb800"))
        details.addStretch()

        layout.addLayout(details, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_click_callback(self.video_data)
        super().mousePressEvent(event)

    def set_thumbnail_pixmap(self, pixmap):
        self.thumb_label.setPixmap(pixmap)


def format_eta(eta_val):
    if not eta_val or str(eta_val).strip().upper() in ["NA", "NONE", "--"]:
        return "--:--"
    try:
        secs = int(float(eta_val))
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
    except Exception:
        return str(eta_val)


class DownloadTask:
    def __init__(self, task_id, url, title, thumbnail="", format_type="mp4", resolution="720"):
        self.id = task_id
        self.url = url
        self.title = title or "Video YouTube"
        self.thumbnail = thumbnail
        self.format_type = (format_type or "mp4").lower()
        self.resolution = str(resolution or "720")
        self.status = "queued"  # queued, downloading, paused, completed, cancelled, error
        self.progress = 0.0  # 0.0 - 100.0
        self.speed = "--"
        self.downloaded_bytes_str = "0 B"
        self.total_bytes_str = "--"
        self.eta = "--:--"
        self.error_msg = ""
        self.file_path = ""
        self.process = None
        self._thread = None
        self._stop_requested = False
        self.download_dir = Path.home() / "Downloads"

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "thumbnail": self.thumbnail,
            "format_type": self.format_type,
            "resolution": self.resolution,
            "status": self.status,
            "progress": round(self.progress, 1),
            "speed": self.speed,
            "downloaded": self.downloaded_bytes_str,
            "total": self.total_bytes_str,
            "eta": self.eta,
            "error": self.error_msg,
            "file_path": self.file_path,
        }

    def start(self):
        if self.status == "downloading":
            return
        self.status = "downloading"
        self._stop_requested = False
        self.error_msg = ""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self):
        if self.status == "downloading":
            self.status = "paused"
            self._stop_requested = True
            self.speed = "--"
            if self.process:
                try:
                    self.process.terminate()
                except Exception:
                    pass

    def resume(self):
        if self.status in ["paused", "error"]:
            self.start()

    def cancel(self):
        self.status = "cancelled"
        self._stop_requested = True
        self.speed = "--"
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
        def _cleanup():
            time.sleep(0.5)
            try:
                clean_name = re.sub(r'[\\/*?:"<>|]', "", self.title)[:15]
                for p in self.download_dir.glob(f"*{clean_name}*.part"):
                    try:
                        p.unlink(missing_ok=True)
                    except Exception:
                        pass
            except Exception:
                pass
        threading.Thread(target=_cleanup, daemon=True).start()

    def _run(self):
        try:
            self.download_dir.mkdir(parents=True, exist_ok=True)
            ytdlp_bin = find_ytdlp_binary()
            ffmpeg_dir = find_ffmpeg_dir()
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

            cmd = [
                ytdlp_bin,
                "--ffmpeg-location", ffmpeg_dir,
                "--no-warnings",
                "--no-playlist",
                "--newline",
                "--progress-template", "download:PG:%(progress._percent_str)s|%(progress._speed_str)s|%(progress._downloaded_bytes_str)s|%(progress._total_bytes_str,progress._total_bytes_estimate_str)s|%(progress.eta)s",
            ]

            if self.format_type == "mp3":
                out_tmpl = str(self.download_dir / "%(title)s.%(ext)s")
                cmd.extend([
                    "-x",
                    "--audio-format", "mp3",
                    "--audio-quality", "0",
                    "-o", out_tmpl,
                    self.url,
                ])
            else:
                res = self.resolution if self.resolution in ["1080", "720", "480", "360"] else "720"
                out_tmpl = str(self.download_dir / f"%(title)s [{res}p].%(ext)s")
                cmd.extend([
                    "-f", f"bestvideo[height<={res}]+bestaudio/best[height<={res}]/best",
                    "--merge-output-format", "mp4",
                    "-o", out_tmpl,
                    self.url,
                ])

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
                creationflags=creation_flags
            )

            re_progress = re.compile(r"\[download\]\s+([\d\.]+)%\s+of\s+~?([^\s]+)\s+at\s+([^\s]+)\s+ETA\s+([^\s]+)")
            re_dest = re.compile(r"\[(?:download|Merger|ExtractAudio)\]\s+Destination:\s+(.+)")
            re_already = re.compile(r"\[download\]\s+(.+)\s+has already been downloaded")

            for line in self.process.stdout:
                if self._stop_requested:
                    break
                line = line.strip()
                if not line:
                    continue

                if line.startswith("PG:"):
                    payload = line[3:]
                    parts = payload.split("|")
                    if len(parts) >= 5:
                        p_str = parts[0].replace("%", "").strip()
                        try:
                            self.progress = max(self.progress, float(p_str))
                        except ValueError:
                            pass
                        speed_val = parts[1].strip()
                        if speed_val and speed_val != "NA":
                            self.speed = speed_val
                        dl_val = parts[2].strip()
                        if dl_val and dl_val != "NA":
                            self.downloaded_bytes_str = dl_val
                        tot_val = parts[3].strip()
                        if tot_val and tot_val != "NA":
                            self.total_bytes_str = tot_val
                        eta_val = parts[4].strip()
                        if eta_val:
                            self.eta = format_eta(eta_val)

                elif "[download]" in line:
                    m = re_progress.search(line)
                    if m:
                        try:
                            self.progress = max(self.progress, float(m.group(1)))
                        except ValueError:
                            pass
                        self.total_bytes_str = m.group(2)
                        self.speed = m.group(3)
                        self.eta = m.group(4)
                    m_al = re_already.search(line)
                    if m_al:
                        self.progress = 100.0
                        self.file_path = m_al.group(1).strip()
                elif "Destination:" in line:
                    m_d = re_dest.search(line)
                    if m_d:
                        self.file_path = m_d.group(1).strip()

            self.process.wait()
            return_code = self.process.returncode

            if self._stop_requested:
                return

            if return_code == 0:
                self.progress = 100.0
                self.status = "completed"
                self.speed = "--"
                self.eta = "00:00"
                if not self.file_path or not os.path.exists(self.file_path):
                    clean_name = re.sub(r'[\\/*?:"<>|]', "", self.title)[:15]
                    for p in self.download_dir.glob(f"*{clean_name}*"):
                        if not p.name.endswith(".part"):
                            self.file_path = str(p)
                            break
            else:
                if self.status not in ["cancelled", "paused"]:
                    self.status = "error"
                    self.error_msg = f"Selesai dengan kode error {return_code}"
                    self.speed = "--"

        except Exception as exc:
            if not self._stop_requested:
                self.status = "error"
                self.error_msg = str(exc)
                self.speed = "--"
        finally:
            self.process = None


class DownloadManager:
    def __init__(self):
        self.tasks = {}
        self.lock = threading.Lock()

    def add_task(self, url, title, thumbnail="", format_type="mp4", resolution="720"):
        with self.lock:
            for task in self.tasks.values():
                if task.url == url and task.format_type == format_type and task.resolution == str(resolution) and task.status in ["downloading", "queued"]:
                    return task
            task_id = str(uuid.uuid4())[:8]
            task = DownloadTask(task_id, url, title, thumbnail, format_type, resolution)
            self.tasks[task_id] = task
            task.start()
            return task

    def get_task(self, task_id):
        with self.lock:
            return self.tasks.get(task_id)

    def pause_task(self, task_id):
        task = self.get_task(task_id)
        if task:
            task.pause()
            return True
        return False

    def resume_task(self, task_id):
        task = self.get_task(task_id)
        if task:
            task.resume()
            return True
        return False

    def cancel_task(self, task_id):
        task = self.get_task(task_id)
        if task:
            task.cancel()
            return True
        return False

    def clear_completed(self):
        with self.lock:
            to_del = [tid for tid, t in self.tasks.items() if t.status in ["completed", "cancelled", "error"]]
            for tid in to_del:
                del self.tasks[tid]

    def get_all_tasks(self):
        with self.lock:
            order = {"downloading": 0, "queued": 1, "paused": 2, "error": 3, "completed": 4, "cancelled": 5}
            task_list = list(self.tasks.values())
            task_list.sort(key=lambda t: (order.get(t.status, 99), t.id))
            return [t.to_dict() for t in task_list]


download_manager = DownloadManager()


def open_downloads_folder():
    download_dir = Path.home() / "Downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        os.startfile(download_dir)
    else:
        subprocess.Popen(["xdg-open", str(download_dir)])


def open_downloaded_file(task_id):
    task = download_manager.get_task(task_id)
    if task and task.file_path and os.path.exists(task.file_path):
        if sys.platform == "win32":
            os.startfile(task.file_path)
        else:
            subprocess.Popen(["xdg-open", str(task.file_path)])
        return True
    return False


class AppRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        web_dir = resource_root() / "web"
        super().__init__(*args, directory=str(web_dir), **kwargs)

    def log_message(self, format, *args):
        pass

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def send_json(self, status_code, data):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)

        if path == "/api/feed":
            q = query_params.get("q", ["trending indonesia"])[0]
            is_ch = query_params.get("channel", ["false"])[0].lower() == "true"
            count = int(query_params.get("count", ["18"])[0])
            items = fetch_youtube_feed(q, is_channel=is_ch, count=count)
            self.send_json(200, items)
            return

        elif path == "/api/bookmarks":
            bms = load_bookmarks()
            self.send_json(200, bms)
            return

        elif path == "/api/history":
            hist = load_history()
            self.send_json(200, hist)
            return

        elif path == "/api/downloads":
            tasks = download_manager.get_all_tasks()
            self.send_json(200, tasks)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            data = {}

        if parsed.path == "/api/play":
            signals.play_requested.emit(data)
            self.send_json(200, {"success": True})
            return

        elif parsed.path == "/api/bookmarks":
            name = data.get("name", "").strip()
            url = data.get("url", "").strip()
            if name:
                bms = load_bookmarks()
                bms = [b for b in bms if b.get("name", "").lower() != name.lower()]
                bms.insert(0, {"name": name, "url": url or f"https://www.youtube.com/@{name}"})
                save_bookmarks(bms)
            self.send_json(200, {"success": True})
            return

        elif parsed.path == "/api/history":
            if data and data.get("id"):
                hist = load_history()
                hist = [h for h in hist if h.get("id") != data.get("id")]
                hist.insert(0, data)
                hist = hist[:60]
                save_history(hist)
            self.send_json(200, {"success": True})
            return

        elif parsed.path == "/api/download":
            url = data.get("url", "").strip()
            title = data.get("title", "Video").strip()
            thumbnail = data.get("thumbnail", "").strip()
            format_type = data.get("format_type", "mp4").strip().lower()
            resolution = str(data.get("resolution", "720")).strip()
            if url:
                task = download_manager.add_task(url, title, thumbnail, format_type, resolution)
                self.send_json(200, {"success": True, "message": "Download dimulai", "task": task.to_dict()})
            else:
                self.send_json(400, {"success": False, "error": "URL video tidak ditemukan"})
            return

        elif parsed.path == "/api/downloads/pause":
            task_id = data.get("id", "")
            ok = download_manager.pause_task(task_id)
            self.send_json(200, {"success": ok})
            return

        elif parsed.path == "/api/downloads/resume":
            task_id = data.get("id", "")
            ok = download_manager.resume_task(task_id)
            self.send_json(200, {"success": ok})
            return

        elif parsed.path == "/api/downloads/cancel":
            task_id = data.get("id", "")
            ok = download_manager.cancel_task(task_id)
            self.send_json(200, {"success": ok})
            return

        elif parsed.path == "/api/downloads/open-folder":
            open_downloads_folder()
            self.send_json(200, {"success": True})
            return

        elif parsed.path == "/api/downloads/open-file":
            task_id = data.get("id", "")
            ok = open_downloaded_file(task_id)
            self.send_json(200, {"success": ok})
            return

        elif parsed.path == "/api/downloads/clear":
            download_manager.clear_completed()
            self.send_json(200, {"success": True})
            return

        self.send_response(404)
        self.end_headers()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)

        if parsed.path == "/api/bookmarks":
            name = query_params.get("name", [""])[0].strip()
            if name:
                bms = load_bookmarks()
                bms = [b for b in bms if b.get("name", "").lower() != name.lower()]
                save_bookmarks(bms)
            self.send_json(200, {"success": True})
            return

        elif parsed.path == "/api/history":
            save_history([])
            self.send_json(200, {"success": True})
            return

        self.send_response(404)
        self.end_headers()


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class VideoWidget(QWidget):
    """Native widget for MPV video rendering."""
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setObjectName("videoWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.setStyleSheet("background: #000000;")

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.window.pip_active:
                self.window.restore_from_pip()
            else:
                self.window.toggle_fullscreen()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class PiPWindow(QWidget):
    def __init__(self, owner):
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.owner = owner
        self.setWindowTitle("Picture-in-Picture")
        self.resize(400, 260)
        self.setMinimumSize(240, 160)
        self.pause_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self.pause_shortcut.activated.connect(owner.toggle_pause)
        self.back_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.back_shortcut.activated.connect(owner.restore_from_pip)
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(0, 0, 0, 0)
        self.layout_box.setSpacing(0)
        controls = QHBoxLayout()
        self.play_btn = QPushButton("Putar / Jeda")
        self.play_btn.clicked.connect(owner.toggle_pause)
        controls.addWidget(self.play_btn)
        back_btn = QPushButton("Kembali ke Pemutar")
        back_btn.clicked.connect(owner.restore_from_pip)
        controls.addWidget(back_btn)
        self.layout_box.addLayout(controls)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.owner.toggle_pause()
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self.owner.restore_from_pip()
            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.owner.pip_active:
            event.ignore()
            self.owner.restore_from_pip()
        else:
            event.accept()


class YouTubeLiteWindow(QMainWindow):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.player = None
        self.pip_active = False
        self.pip_window = None
        self.mpv_wid = None
        self.current_video_data = None
        self.user_seeking = False
        self.thumb_cache = {}
        self.pending_cards = {}
        self.fetching_thumbs = set()
        self.thumb_pool = ThreadPoolExecutor(max_workers=4)

        self.setWindowTitle(APP_NAME)
        logo_path = resource_root() / "logo.webp"
        if logo_path.is_file():
            self.setWindowIcon(QIcon(str(logo_path)))
        self.resize(1300, 820)
        self.setMinimumSize(920, 600)

        # Central Stacked Widget
        self.stacked = QStackedWidget(self)
        self.setCentralWidget(self.stacked)

        # ==========================================================
        # PAGE 0: Modern HTML5 Web UI (Beranda, Cards, Search, Bookmarks)
        # ==========================================================
        self.web_view = QWebEngineView(self)
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.web_view.load(QUrl(f"http://127.0.0.1:{self.port}/"))
        self.stacked.addWidget(self.web_view)

        # ==========================================================
        # PAGE 1: Native MPV Player Page (Video + Sidebar Rekomendasi)
        # ==========================================================
        self.player_page = QWidget()
        player_layout = QVBoxLayout(self.player_page)
        player_layout.setContentsMargins(20, 12, 20, 16)
        player_layout.setSpacing(10)

        # Top Bar: Back to Home
        top_bar = QHBoxLayout()
        self.back_btn = QPushButton("Kembali ke Beranda")
        self.back_btn.setIcon(heroicon("back"))
        self.back_btn.setObjectName("backBtn")
        self.back_btn.clicked.connect(self.return_to_home)
        top_bar.addWidget(self.back_btn)
        top_bar.addStretch()
        player_layout.addLayout(top_bar)

        # Main Split Content: Left (Video & Meta) | Right (Sidebar Video Lainnya)
        main_content_hlayout = QHBoxLayout()
        main_content_hlayout.setSpacing(16)

        # --- LEFT COLUMN: Video Container + Meta Card ---
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        # 1. TOP VIDEO CONTAINER (16:9 Aspect with MPV)
        self.video_container = QFrame()
        self.video_container.setObjectName("videoContainer")
        vc_layout = QVBoxLayout(self.video_container)
        vc_layout.setContentsMargins(0, 0, 0, 0)
        vc_layout.setSpacing(0)

        self.video_widget = VideoWidget(self)
        vc_layout.addWidget(self.video_widget, 1)

        # Seek Bar & Playback Controls bar right underneath video
        self.controls_bar = QFrame()
        self.controls_bar.setObjectName("controlsBar")
        cb_layout = QHBoxLayout(self.controls_bar)
        cb_layout.setContentsMargins(14, 8, 14, 8)
        cb_layout.setSpacing(10)

        # Dynamic Play/Pause Button
        self.play_btn = QPushButton()
        self.play_btn.setIcon(heroicon("play"))
        self.play_btn.setObjectName("playBtn")
        self.play_btn.setToolTip("Putar / Jeda (Spasi)")
        self.play_btn.setFixedWidth(44)
        self.play_btn.clicked.connect(self.toggle_pause)
        cb_layout.addWidget(self.play_btn)

        self.current_time_lbl = QLabel("00:00")
        self.current_time_lbl.setStyleSheet("color: #8b93a7; font-size: 11px;")
        cb_layout.addWidget(self.current_time_lbl)

        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderPressed.connect(self.on_seek_pressed)
        self.seek_slider.sliderReleased.connect(self.on_seek_released)
        cb_layout.addWidget(self.seek_slider, 1)

        self.total_time_lbl = QLabel("00:00")
        self.total_time_lbl.setStyleSheet("color: #8b93a7; font-size: 11px;")
        cb_layout.addWidget(self.total_time_lbl)

        # Resolution Selector Dropdown
        res_lbl = QLabel("Kualitas:")
        res_lbl.setStyleSheet("color: #8b93a7; font-size: 11px;")
        cb_layout.addWidget(res_lbl)
        self.res_combo = QComboBox()
        self.res_combo.setObjectName("resCombo")
        self.res_combo.addItems(["Auto", "1080p", "720p (HD)", "480p", "360p (Hemat)"])
        self.res_combo.setCurrentText("720p (HD)")
        self.res_combo.currentIndexChanged.connect(self.on_resolution_changed)
        cb_layout.addWidget(self.res_combo)

        # Volume
        cb_layout.addWidget(QLabel("Vol:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setFixedWidth(70)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.set_volume)
        cb_layout.addWidget(self.volume_slider)

        vc_layout.addWidget(self.controls_bar)
        left_col.addWidget(self.video_container, 1)

        # 2. BOTTOM META CARD (Video title, channel avatar, bookmark & fullscreen)
        self.meta_card = QFrame()
        self.meta_card.setObjectName("metaCard")
        mc_layout = QVBoxLayout(self.meta_card)
        mc_layout.setContentsMargins(18, 14, 18, 14)
        mc_layout.setSpacing(10)

        # Title
        self.player_title_lbl = QLabel("Judul Video")
        self.player_title_lbl.setObjectName("metaTitle")
        self.player_title_lbl.setWordWrap(True)
        mc_layout.addWidget(self.player_title_lbl)

        # Channel Row
        ch_row = QHBoxLayout()
        ch_row.setSpacing(12)

        self.channel_avatar = QLabel("D")
        self.channel_avatar.setObjectName("channelAvatar")
        self.channel_avatar.setFixedSize(40, 40)
        self.channel_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ch_row.addWidget(self.channel_avatar)

        ch_info_col = QVBoxLayout()
        ch_info_col.setSpacing(2)
        self.player_channel_lbl = QLabel("DENNY CAKNAN")
        self.player_channel_lbl.setObjectName("metaChannel")
        ch_info_col.addWidget(self.player_channel_lbl)

        self.player_duration_lbl = QLabel("Durasi: 00:00")
        self.player_duration_lbl.setObjectName("metaDuration")
        ch_info_col.addLayout(icon_text_row("clock", self.player_duration_lbl))
        ch_row.addLayout(ch_info_col, 1)
        mc_layout.addLayout(ch_row)

        # Pill Buttons: [Simpan Channel] [Layar Penuh]
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.player_bookmark_btn = QPushButton("Simpan Channel")
        self.player_bookmark_btn.setIcon(heroicon("bookmark", "#ffb800"))
        self.player_bookmark_btn.setObjectName("btnBookmarkPill")
        self.player_bookmark_btn.clicked.connect(self.toggle_player_bookmark)
        btn_row.addWidget(self.player_bookmark_btn)

        self.download_btn = QPushButton("Download")
        self.download_btn.setIcon(heroicon("download"))
        self.download_btn.setObjectName("btnSecondaryPill")
        self.download_btn.clicked.connect(self.download_current_video)
        btn_row.addWidget(self.download_btn)

        self.fullscreen_btn = QPushButton("Layar Penuh")
        self.fullscreen_btn.setIcon(heroicon("fullscreen"))
        self.fullscreen_btn.setObjectName("btnSecondaryPill")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        btn_row.addWidget(self.fullscreen_btn)

        self.pip_btn = QPushButton("Picture-in-Picture")
        self.pip_btn.setObjectName("btnSecondaryPill")
        self.pip_btn.clicked.connect(self.enter_pip)
        btn_row.addWidget(self.pip_btn)

        btn_row.addStretch()
        mc_layout.addLayout(btn_row)

        left_col.addWidget(self.meta_card)
        main_content_hlayout.addLayout(left_col, stretch=7)

        # --- RIGHT COLUMN: Sidebar Video Terkait & Komentar / Live Chat ---
        self.related_sidebar = QFrame()
        self.related_sidebar.setObjectName("relatedSidebar")
        self.related_sidebar.setFixedWidth(360)
        rs_layout = QVBoxLayout(self.related_sidebar)
        rs_layout.setContentsMargins(12, 12, 12, 12)
        rs_layout.setSpacing(10)

        # Tab Navigation Header
        tab_header = QHBoxLayout()
        tab_header.setSpacing(8)

        self.tab_related_btn = QPushButton("Terkait")
        self.tab_related_btn.setIcon(heroicon("film"))
        self.tab_related_btn.setObjectName("tabActive")
        self.tab_related_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tab_related_btn.clicked.connect(lambda: self.switch_sidebar_tab(0))
        tab_header.addWidget(self.tab_related_btn, 1)

        self.tab_chat_btn = QPushButton("Komentar")
        self.tab_chat_btn.setIcon(heroicon("chat"))
        self.tab_chat_btn.setObjectName("tabInactive")
        self.tab_chat_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tab_chat_btn.clicked.connect(lambda: self.switch_sidebar_tab(1))
        tab_header.addWidget(self.tab_chat_btn, 1)

        rs_layout.addLayout(tab_header)

        # Stacked Container for Sidebar Content
        self.sidebar_stack = QStackedWidget()

        # Page 0: Related Videos
        self.related_scroll = QScrollArea()
        self.related_scroll.setObjectName("relatedScroll")
        self.related_scroll.setWidgetResizable(True)
        self.related_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.related_container = QWidget()
        self.related_list_layout = QVBoxLayout(self.related_container)
        self.related_list_layout.setContentsMargins(0, 0, 0, 0)
        self.related_list_layout.setSpacing(8)
        self.related_scroll.setWidget(self.related_container)
        self.sidebar_stack.addWidget(self.related_scroll)

        # Page 1: Live Chat / Regular Comments
        self.comments_page = QWidget()
        self.cp_layout = QVBoxLayout(self.comments_page)
        self.cp_layout.setContentsMargins(0, 0, 0, 0)
        self.cp_layout.setSpacing(8)

        # Live Chat WebEngineView (Lazy-loaded to save RAM)
        self.live_chat_view = None

        # Regular Comments Scroll Area
        self.comments_scroll = QScrollArea()
        self.comments_scroll.setObjectName("commentsScroll")
        self.comments_scroll.setWidgetResizable(True)
        self.comments_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.comments_container = QWidget()
        self.comments_list_layout = QVBoxLayout(self.comments_container)
        self.comments_list_layout.setContentsMargins(0, 0, 0, 0)
        self.comments_list_layout.setSpacing(8)
        self.comments_scroll.setWidget(self.comments_container)
        self.cp_layout.addWidget(self.comments_scroll, 1)

        self.sidebar_stack.addWidget(self.comments_page)
        rs_layout.addWidget(self.sidebar_stack, 1)

        main_content_hlayout.addWidget(self.related_sidebar, stretch=3)

        player_layout.addLayout(main_content_hlayout, 1)

        self.stacked.addWidget(self.player_page)

        # Sleek Stylesheet
        self.setStyleSheet("""
            QWidget { background: #0c0d12; color: #f0f2f7; font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 13px; }
            
            QFrame#videoContainer { background: #000000; border: 1px solid #272c3d; border-radius: 14px; }
            QFrame#controlsBar { background: #11141c; border-top: 1px solid #212634; border-bottom-left-radius: 14px; border-bottom-right-radius: 14px; }
            
            QFrame#metaCard { background: #14161f; border: 1px solid #272c3d; border-radius: 14px; }
            QLabel#metaTitle { font-size: 15px; font-weight: 700; color: #ffffff; }
            QLabel#channelAvatar { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff3b5c, stop:1 #ff6b8b); color: #ffffff; font-size: 17px; font-weight: 700; border-radius: 20px; }
            QLabel#metaChannel { font-size: 13px; font-weight: 600; color: #ffffff; }
            QLabel#metaDuration { font-size: 12px; color: #8b93a7; }

            /* Right Sidebar Video & Komentar */
            QFrame#relatedSidebar { background: #14161f; border: 1px solid #272c3d; border-radius: 14px; }
            
            /* Tab Buttons */
            QPushButton#tabActive {
                background: #ff3b5c;
                color: #ffffff;
                font-weight: 700;
                font-size: 12px;
                border-radius: 8px;
                padding: 7px 12px;
                border: none;
            }
            QPushButton#tabInactive {
                background: #1e2230;
                color: #8b93a7;
                font-weight: 600;
                font-size: 12px;
                border-radius: 8px;
                padding: 7px 12px;
                border: 1px solid #282f42;
            }
            QPushButton#tabInactive:hover {
                background: #272e42;
                color: #ffffff;
            }

            QScrollArea#relatedScroll, QScrollArea#commentsScroll { background: transparent; border: none; }
            QScrollArea#relatedScroll > QWidget > QWidget, QScrollArea#commentsScroll > QWidget > QWidget { background: transparent; }
            
            QFrame#relatedCard { background: #191c28; border: 1px solid #232838; border-radius: 8px; }
            QFrame#relatedCard:hover { background: #252b3e; border: 1px solid #ff3b5c; }
            QLabel#relatedThumb { background: #08090d; border-radius: 6px; color: #6b7280; font-size: 14px; }
            QLabel#relatedTitle { font-size: 12px; font-weight: 600; color: #ffffff; }
            QLabel#relatedChannel { font-size: 11px; color: #8b93a7; }
            QLabel#relatedDuration { font-size: 11px; font-weight: 600; color: #ffb800; }

            /* Comments Cards */
            QFrame#commentCard { background: #191c28; border: 1px solid #232838; border-radius: 8px; }
            QLabel#commentAuthor { color: #f0f2f7; font-weight: 600; font-size: 12px; }
            QLabel#commentTime { color: #8b93a7; font-size: 11px; }
            QLabel#commentText { color: #d8dbe2; font-size: 12px; }
            QLabel#commentLikes { color: #ffb800; font-size: 11px; font-weight: 600; }

            /* Resolution Dropdown */
            QComboBox#resCombo {
                background: #202432;
                border: 1px solid #343c52;
                color: #f0f2f7;
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
            }
            QComboBox#resCombo QAbstractItemView {
                background: #191c28;
                border: 1px solid #343c52;
                color: #ffffff;
                selection-background-color: #ff3b5c;
                outline: none;
            }

            /* Buttons */
            QPushButton#playBtn {
                background: #ff3b5c;
                border: none;
                color: #ffffff;
                font-size: 15px;
                font-weight: bold;
                border-radius: 6px;
                padding: 5px 8px;
            }
            QPushButton#playBtn:hover { background: #ff5574; }

            QPushButton#btnBookmarkPill {
                background: rgba(255, 184, 0, 0.12);
                border: 1px solid rgba(255, 184, 0, 0.4);
                color: #ffb800;
                font-weight: 600;
                padding: 8px 18px;
                border-radius: 20px;
            }
            QPushButton#btnBookmarkPill:hover { background: rgba(255, 184, 0, 0.22); }
            
            QPushButton#btnSecondaryPill, QPushButton#backBtn {
                background: #202534;
                border: 1px solid #272c3d;
                color: #f0f2f7;
                font-weight: 600;
                padding: 8px 18px;
                border-radius: 20px;
            }
            QPushButton#btnSecondaryPill:hover, QPushButton#backBtn:hover { background: #2b3246; }

            QSlider::groove:horizontal { height: 5px; background: #2b3145; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #ff0033; border-radius: 2px; }
            QSlider::handle:horizontal { background: #ffffff; width: 14px; margin: -5px 0; border-radius: 7px; }
            
            QPushButton { background: #202432; border: 1px solid #343c52; padding: 6px 12px; border-radius: 6px; font-weight: 600; }
            QPushButton:hover { background: #2d3448; }
        """)

        signals.play_requested.connect(self.play_video)
        signals.related_videos_loaded.connect(self.populate_related_videos)
        signals.thumbnail_loaded.connect(self.on_thumbnail_loaded)
        signals.comments_loaded.connect(self.populate_comments)

        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(500)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start()

    def init_mpv(self):
        if self.player is None:
            try:
                setup_native_path()
                import mpv
                prev_locale = locale.getlocale(locale.LC_NUMERIC)
                locale.setlocale(locale.LC_NUMERIC, "C")
                self.mpv_wid = int(self.video_widget.winId())
                self.player = mpv.MPV(
                    wid=str(self.mpv_wid),
                    vo="gpu",
                    hwdec="auto-safe",
                    ytdl=True,
                    osc=False,
                    input_default_bindings=False,
                    config=False,
                    volume=self.volume_slider.value(),
                    keep_open="yes",
                    loglevel="error",
                    video_sync="audio",
                    hr_seek="yes",
                    demuxer_lavf_o="live_start_index=-1",
                    demuxer_max_bytes=32 * 1024 * 1024,
                    demuxer_max_back_bytes=16 * 1024 * 1024,
                )
            except Exception as exc:
                self.mpv_wid = None
                QMessageBox.critical(
                    self,
                    "Kesalahan MPV",
                    f"Tidak dapat memulai MPV player:\n{exc}\n\nPastikan libmpv-2.dll tersedia di folder tools.",
                )
            finally:
                if 'prev_locale' in locals():
                    try:
                        locale.setlocale(locale.LC_NUMERIC, prev_locale)
                    except Exception:
                        pass

    def is_live_video(self, video_data):
        if not video_data:
            return False
        if video_data.get("is_live"):
            return True
        dur = str(video_data.get("duration", "")).strip().lower()
        if dur in ["--:--", "live", "", "none"]:
            return True
        return False

    def get_selected_format(self, is_live: bool = False):
        text = self.res_combo.currentText()
        if is_live:
            # YouTube Live: prioritizing muxed stream formats (e.g. format 91-96 via android client)
            # guarantees 100% video-audio lock in the same bitstream container with zero drift.
            if "1080p" in text:
                return "best[height<=1080]/bestvideo[height<=1080]+bestaudio/best"
            elif "720p" in text:
                return "best[height<=720]/bestvideo[height<=720]+bestaudio/best"
            elif "480p" in text:
                return "best[height<=480]/bestvideo[height<=480]+bestaudio/best"
            elif "360p" in text:
                return "best[height<=360]/bestvideo[height<=360]+bestaudio/best"
            else:
                return "best/bestvideo+bestaudio"
        else:
            if "1080p" in text:
                return "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
            elif "720p" in text:
                return "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
            elif "480p" in text:
                return "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
            elif "360p" in text:
                return "bestvideo[height<=360]+bestaudio/best[height<=360]/best"
            else: # Auto
                return "bestvideo+bestaudio/best"

    def on_resolution_changed(self, idx):
        if not self.player or not self.current_video_data:
            return
        is_live = self.is_live_video(self.current_video_data)
        fmt = self.get_selected_format(is_live=is_live)
        try:
            self.player["ytdl-format"] = fmt
            url = self.current_video_data.get("url") or f"https://www.youtube.com/watch?v={self.current_video_data.get('id')}"
            if is_live:
                self.player.command("loadfile", url, "replace")
            else:
                pos = float(getattr(self.player, "time_pos", 0) or 0)
                self.player.command("loadfile", url, "replace", f"start={pos}")
        except Exception:
            pass

    def request_thumbnail(self, url):
        if not url:
            return
        if url in self.thumb_cache:
            cards = self.pending_cards.pop(url, [])
            for c in cards:
                c.set_thumbnail_pixmap(self.thumb_cache[url])
            return
        if url in self.fetching_thumbs:
            return
        self.fetching_thumbs.add(url)
        def _fetch():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = resp.read()
                    signals.thumbnail_loaded.emit(url, data)
            except Exception:
                pass
            finally:
                self.fetching_thumbs.discard(url)
        self.thumb_pool.submit(_fetch)

    def on_thumbnail_loaded(self, url, data):
        pix = QPixmap()
        if pix.loadFromData(data):
            scaled = pix.scaled(100, 56, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            # Evict oldest thumbnail if cache exceeds 60 items to save RAM
            if len(self.thumb_cache) >= 60:
                try:
                    oldest = next(iter(self.thumb_cache))
                    del self.thumb_cache[oldest]
                except Exception:
                    pass
            self.thumb_cache[url] = scaled
            cards = self.pending_cards.pop(url, [])
            for c in cards:
                c.set_thumbnail_pixmap(scaled)

    def populate_related_videos(self, videos):
        while self.related_list_layout.count() > 0:
            item = self.related_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not videos:
            empty_lbl = QLabel("Tidak ada video terkait.")
            empty_lbl.setStyleSheet("color: #6b7280; padding: 20px; font-size: 12px;")
            self.related_list_layout.addWidget(empty_lbl)
            self.related_list_layout.addStretch()
            return

        cur_id = self.current_video_data.get("id") if self.current_video_data else ""
        for v in videos:
            if cur_id and v.get("id") == cur_id:
                continue
            card = RelatedVideoCard(v, self.play_video)
            self.related_list_layout.addWidget(card)

            thumb_url = v.get("thumbnail")
            if thumb_url:
                if thumb_url in self.thumb_cache:
                    card.set_thumbnail_pixmap(self.thumb_cache[thumb_url])
                else:
                    self.pending_cards.setdefault(thumb_url, []).append(card)
                    self.request_thumbnail(thumb_url)

        self.related_list_layout.addStretch()

    def switch_sidebar_tab(self, idx):
        self.sidebar_stack.setCurrentIndex(idx)
        if idx == 0:
            self.tab_related_btn.setObjectName("tabActive")
            self.tab_chat_btn.setObjectName("tabInactive")
        else:
            self.tab_related_btn.setObjectName("tabInactive")
            self.tab_chat_btn.setObjectName("tabActive")
        self.tab_related_btn.style().unpolish(self.tab_related_btn)
        self.tab_related_btn.style().polish(self.tab_related_btn)
        self.tab_chat_btn.style().unpolish(self.tab_chat_btn)
        self.tab_chat_btn.style().polish(self.tab_chat_btn)

    def show_comments_loading(self):
        while self.comments_list_layout.count() > 0:
            item = self.comments_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        loading_lbl = QLabel("Memuat komentar...")
        loading_lbl.setStyleSheet("color: #8b93a7; padding: 24px; font-size: 13px; font-weight: 500;")
        loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_row = QWidget()
        loading_row.setLayout(icon_text_row("loading", loading_lbl))
        self.comments_list_layout.addWidget(loading_row)
        self.comments_list_layout.addStretch()

    def populate_comments(self, comments):
        while self.comments_list_layout.count() > 0:
            item = self.comments_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not comments:
            empty_lbl = QLabel("Komentar dinonaktifkan atau belum ada.")
            empty_lbl.setStyleSheet("color: #6b7280; padding: 24px; font-size: 12px;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.comments_list_layout.addWidget(empty_lbl)
            self.comments_list_layout.addStretch()
            return

        header_lbl = QLabel(f"{len(comments)} Komentar Terpopuler")
        header_lbl.setStyleSheet("color: #f0f2f7; font-weight: 700; font-size: 13px; padding: 4px 6px;")
        header_row = QWidget()
        header_row.setLayout(icon_text_row("chat", header_lbl, "#f0f2f7"))
        self.comments_list_layout.addWidget(header_row)

        for c in comments:
            card = CommentCard(c)
            self.comments_list_layout.addWidget(card)

        self.comments_list_layout.addStretch()

    def play_video(self, video_data):
        if self.pip_active:
            self.restore_from_pip()
        self.current_video_data = video_data
        url = video_data.get("url") or f"https://www.youtube.com/watch?v={video_data.get('id')}"
        vid_id = video_data.get("id") or ""

        # 1. Update metadata UI
        title = video_data.get("title", "Memutar Video")
        channel = video_data.get("channel", "YouTube")
        duration = video_data.get("duration", "--:--")
        initial = (channel[:1] or "Y").upper()

        self.player_title_lbl.setText(title)
        self.player_channel_lbl.setText(channel)
        self.player_duration_lbl.setText(f"Durasi: {duration}")
        self.channel_avatar.setText(initial)
        self.update_bookmark_btn_state()

        # Update play icon to Pause (active playback)
        self.play_btn.setIcon(heroicon("pause"))
        self.play_btn.setToolTip("Jeda (Spasi)")

        # 2. Switch to Player page
        self.stacked.setCurrentIndex(1)

        # 3. Initialize MPV after widget is mapped
        self.init_mpv()
        if not self.player:
            return

        # 4. Play video with chosen resolution format and sync options
        is_live = self.is_live_video(video_data)
        try:
            self.configure_playback(is_live)
            self.player.play(url)
        except Exception as exc:
            QMessageBox.warning(self, "Gagal Memutar", str(exc))

        # 5. Configure Sidebar Tabs: Live Chat vs Regular Comments
        if is_live:
            self.tab_chat_btn.setText("Live Chat")
            self.tab_chat_btn.setIcon(heroicon("live", "#ff3b5c"))
            self.comments_scroll.hide()
            if self.live_chat_view is None:
                self.live_chat_view = QWebEngineView()
                self.live_chat_view.setObjectName("liveChatView")
                self.live_chat_view.setStyleSheet("background: #0f1117; border-radius: 8px;")
                self.cp_layout.insertWidget(0, self.live_chat_view, 1)
            self.live_chat_view.show()
            if vid_id:
                chat_url = f"https://www.youtube.com/live_chat?v={vid_id}&embed_domain=127.0.0.1&dark_theme=1"
                self.live_chat_view.setUrl(QUrl(chat_url))
        else:
            self.tab_chat_btn.setText("Komentar")
            self.tab_chat_btn.setIcon(heroicon("chat"))
            if self.live_chat_view is not None:
                self.live_chat_view.hide()
                self.live_chat_view.setUrl(QUrl("about:blank"))
            self.comments_scroll.show()
            self.show_comments_loading()
            if vid_id:
                def _fetch_comments_bg():
                    cmts = fetch_video_comments(vid_id, count=25)
                    signals.comments_loaded.emit(cmts)
                threading.Thread(target=_fetch_comments_bg, daemon=True).start()

        # 6. Fetch related videos asynchronously for the sidebar
        def _fetch_related_bg():
            q = channel if (channel and channel != "YouTube") else " ".join(title.split()[:4])
            results = fetch_youtube_feed(q, is_channel=False, count=12)
            signals.related_videos_loaded.emit(results)
        threading.Thread(target=_fetch_related_bg, daemon=True).start()

    def configure_playback(self, is_live):
        self.player["ytdl-raw-options"] = {"extractor-args": "youtube:player_client=android"} if is_live else {}
        self.player["ytdl-format"] = self.get_selected_format(is_live=is_live)

    def playback_snapshot(self):
        if not self.player or not self.current_video_data:
            return None
        def read_property(name, default):
            try:
                value = getattr(self.player, name)
                return default if value is None else value
            except Exception:
                return default
        data = self.current_video_data
        return {
            "url": data.get("url") or f"https://www.youtube.com/watch?v={data.get('id')}",
            "position": read_property("time_pos", 0),
            "pause": bool(read_property("pause", False)),
            "volume": read_property("volume", self.volume_slider.value()),
            "live": self.is_live_video(data),
        }

    def enter_pip(self):
        if not self.player or self.pip_active:
            return
        if self.isFullScreen():
            self.toggle_fullscreen()
        if self.pip_window is None:
            self.pip_window = PiPWindow(self)
        snapshot = self.playback_snapshot()
        self.video_container.layout().removeWidget(self.video_widget)
        self.pip_window.layout_box.insertWidget(0, self.video_widget, 1)
        self.pip_active = True
        self.pip_window.show()
        self.video_widget.show()
        self.check_video_handle(snapshot)
        self.stacked.setCurrentIndex(0)
        self.update_progress()

    def restore_from_pip(self):
        if not self.pip_active:
            return
        snapshot = self.playback_snapshot()
        self.stacked.setCurrentIndex(1)
        self.pip_window.layout_box.removeWidget(self.video_widget)
        self.video_container.layout().insertWidget(0, self.video_widget, 1)
        self.video_widget.show()
        self.pip_active = False
        self.pip_window.hide()
        self.check_video_handle(snapshot)
        self.showNormal() if self.isMinimized() else self.show()
        self.raise_()
        self.activateWindow()

    def check_video_handle(self, snapshot):
        if not self.player or int(self.video_widget.winId()) == self.mpv_wid:
            return
        try:
            self.player.terminate()
        except Exception as exc:
            QMessageBox.critical(self, "Kesalahan MPV", f"MPV lama tidak dapat ditutup; pemutar tidak dibuat ulang: {exc}")
            return
        self.player = None
        self.mpv_wid = None
        self.init_mpv()
        if not self.player or not snapshot:
            return
        try:
            self.configure_playback(snapshot["live"])
            self.player.volume = snapshot["volume"]
            self.player.pause = snapshot["pause"]
            if not snapshot["live"] and float(snapshot["position"]) > 0:
                self.player.command("loadfile", snapshot["url"], "replace", -1, f"start={snapshot['position']}")
            else:
                self.player.play(snapshot["url"])
        except Exception as exc:
            QMessageBox.critical(self, "Kesalahan MPV", f"Pemutar dibuat ulang, tetapi video tidak dapat dipulihkan: {exc}")

    def return_to_home(self):
        if not self.pip_active:
            self.stop_playback()
        self.stacked.setCurrentIndex(0)
        gc.collect()

    def toggle_pause(self):
        if self.player:
            try:
                new_pause = not bool(getattr(self.player, "pause", False))
                self.player.pause = new_pause
                self.play_btn.setIcon(heroicon("play" if new_pause else "pause"))
                self.play_btn.setToolTip("Putar (Spasi)" if new_pause else "Jeda (Spasi)")
                if self.pip_window:
                    self.pip_window.play_btn.setText("Putar" if new_pause else "Jeda")
            except Exception:
                pass

    def stop_playback(self):
        if getattr(self, "live_chat_view", None) is not None:
            self.live_chat_view.setUrl(QUrl("about:blank"))
        if self.player:
            try:
                self.player.stop()
            except Exception:
                pass
        self.play_btn.setIcon(heroicon("play"))
        self.play_btn.setToolTip("Putar (Spasi)")
        self.current_time_lbl.setText("00:00")
        self.seek_slider.setValue(0)
        gc.collect()

    def set_volume(self, val):
        if self.player:
            try:
                self.player.volume = val
            except Exception:
                pass

    def on_seek_pressed(self):
        self.user_seeking = True

    def on_seek_released(self):
        if self.player:
            try:
                duration = float(self.player.duration or 0)
                if duration > 0:
                    self.player.time_pos = duration * self.seek_slider.value() / 1000
            except Exception:
                pass
        self.user_seeking = False

    def update_progress(self):
        if self.player and (self.stacked.currentIndex() == 1 or self.pip_active):
            try:
                is_paused = bool(getattr(self.player, "pause", False))
                if self.pip_window:
                    self.pip_window.play_btn.setText("Putar" if is_paused else "Jeda")
                self.play_btn.setIcon(heroicon("play" if is_paused else "pause"))
                self.play_btn.setToolTip("Putar (Spasi)" if is_paused else "Jeda (Spasi)")

                duration = float(self.player.duration or 0)
                pos = float(self.player.time_pos or 0)
                self.current_time_lbl.setText(display_time(pos))
                self.total_time_lbl.setText(display_time(duration))
                if duration > 0 and not self.user_seeking:
                    self.seek_slider.setValue(max(0, min(1000, int(pos / duration * 1000))))
            except Exception:
                pass

    def toggle_player_bookmark(self):
        if not self.current_video_data:
            return
        ch_name = self.current_video_data.get("channel", "")
        ch_url = self.current_video_data.get("channel_url", "")
        if not ch_name or ch_name == "YouTube":
            return

        bms = load_bookmarks()
        exists = any(b.get("name", "").lower() == ch_name.lower() for b in bms)
        if exists:
            bms = [b for b in bms if b.get("name", "").lower() != ch_name.lower()]
        else:
            bms.insert(0, {"name": ch_name, "url": ch_url or f"https://www.youtube.com/@{ch_name.replace(' ', '')}"})

        save_bookmarks(bms)
        self.update_bookmark_btn_state()

    def update_bookmark_btn_state(self):
        if not self.current_video_data:
            return
        ch_name = self.current_video_data.get("channel", "")
        bms = load_bookmarks()
        exists = any(b.get("name", "").lower() == ch_name.lower() for b in bms)
        if exists:
            self.player_bookmark_btn.setText("Channel Disimpan")
            self.player_bookmark_btn.setIcon(heroicon("bookmark-filled", "#0c0d12"))
            self.player_bookmark_btn.setStyleSheet("""
                background: #ffb800; color: #0c0d12; font-weight: bold; border-radius: 20px; padding: 8px 18px; border: none;
            """)
        else:
            self.player_bookmark_btn.setText("Simpan Channel")
            self.player_bookmark_btn.setIcon(heroicon("bookmark", "#ffb800"))
            self.player_bookmark_btn.setStyleSheet("""
                background: rgba(255, 184, 0, 0.12); border: 1px solid rgba(255, 184, 0, 0.4); color: #ffb800; font-weight: 600; padding: 8px 18px; border-radius: 20px;
            """)

    def download_current_video(self):
        if not self.current_video_data:
            return
        url = self.current_video_data.get("url") or f"https://www.youtube.com/watch?v={self.current_video_data.get('id')}"
        title = self.current_video_data.get("title", "video")
        thumbnail = self.current_video_data.get("thumbnail", "")

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #181b26;
                color: #f0f2f7;
                border: 1px solid #2b3248;
                border-radius: 8px;
                padding: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #2b3248;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #2b3248;
                margin: 4px 6px;
            }
        """)

        act_1080 = menu.addAction("MP4 Video - 1080p (Full HD)")
        act_720 = menu.addAction("MP4 Video - 720p (HD)")
        act_480 = menu.addAction("MP4 Video - 480p (SD)")
        act_360 = menu.addAction("MP4 Video - 360p (Hemat)")
        menu.addSeparator()
        act_mp3 = menu.addAction("MP3 Audio Musik (Kualitas Terbaik)")

        btn_pos = self.download_btn.mapToGlobal(self.download_btn.rect().bottomLeft())
        chosen = menu.exec(btn_pos)
        if not chosen:
            return

        if chosen == act_1080:
            fmt, res, desc = "mp4", "1080", "Video MP4 1080p"
        elif chosen == act_720:
            fmt, res, desc = "mp4", "720", "Video MP4 720p"
        elif chosen == act_480:
            fmt, res, desc = "mp4", "480", "Video MP4 480p"
        elif chosen == act_360:
            fmt, res, desc = "mp4", "360", "Video MP4 360p"
        elif chosen == act_mp3:
            fmt, res, desc = "mp3", "auto", "Audio MP3"
        else:
            return

        try:
            task = download_manager.add_task(url, title, thumbnail, fmt, res)
            download_dir = Path.home() / "Downloads"
            QMessageBox.information(
                self,
                "Download Dimulai",
                f"Mengunduh [{desc}]:\n{title}\n\nFile tersimpan di:\n{download_dir}\n\nAnda dapat memantau progres unduhan di halaman Pengelola Unduhan.",
            )
        except Exception as exc:
            QMessageBox.warning(self, "Gagal Download", f"Error: {exc}")

    def toggle_fullscreen(self):
        if self.pip_active:
            return
        if self.isFullScreen():
            self.meta_card.show()
            self.related_sidebar.show()
            self.controls_bar.show()
            self.back_btn.show()
            self.fullscreen_btn.setText("Layar Penuh")
            self.showNormal()
        else:
            self.meta_card.hide()
            self.related_sidebar.hide()
            self.controls_bar.hide()
            self.back_btn.hide()
            self.fullscreen_btn.setText("Keluar Penuh")
            self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_F11, Qt.Key.Key_F):
            self.toggle_fullscreen()
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.toggle_fullscreen()
                event.accept()
            elif self.stacked.currentIndex() == 1:
                self.return_to_home()
                event.accept()
            else:
                super().keyPressEvent(event)
        elif event.key() == Qt.Key.Key_Space:
            if self.stacked.currentIndex() == 1:
                self.toggle_pause()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.progress_timer.stop()
        if self.pip_window:
            self.pip_active = False
            self.pip_window.hide()
        if self.player:
            try:
                self.player.terminate()
            except Exception:
                pass
            self.player = None
        if self.pip_window:
            self.pip_window.close()
            self.pip_window.deleteLater()
        self.thumb_pool.shutdown(wait=False)
        for handle in _DLL_HANDLES:
            try:
                handle.close()
            except Exception:
                pass
        _DLL_HANDLES.clear()
        event.accept()


def start_server(port):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), AppRequestHandler)
    server.serve_forever()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("YouTubeLiteLocal")

    init_app_data_dir()

    port = get_free_port()

    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()

    window = YouTubeLiteWindow(port)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
