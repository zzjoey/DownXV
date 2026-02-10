"""Main application window for DownXV."""

import os
import subprocess
import sys

from PySide6.QtCore import QEvent, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .downloader import DownloadWorker, InfoExtractWorker
from .logo import create_logo_pixmap
from .updater import UpdateChecker
from .url_validator import validate_url

_MAX_CONCURRENT = 3


class _ElidedLabel(QLabel):
    """QLabel that truncates text with ellipsis when it overflows."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._full_text = text

    def setText(self, text: str) -> None:
        self._full_text = text
        self._elide()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._elide()

    def _elide(self) -> None:
        w = self.width()
        if w <= 0:
            super().setText(self._full_text)
            return
        elided = self.fontMetrics().elidedText(
            self._full_text, Qt.TextElideMode.ElideRight, w
        )
        super().setText(elided)
        self.setToolTip(self._full_text if elided != self._full_text else "")


class _DownloadCard(QFrame):
    """Progress card for a single download task."""

    dismissed = Signal()
    open_file = Signal(str)

    def __init__(self, title: str = "Starting download...") -> None:
        super().__init__()
        self.setObjectName("card")
        self._is_done = False
        self._filepath: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(3)

        header = QHBoxLayout()
        header.setSpacing(8)
        self._title = _ElidedLabel(title)
        self._title.setObjectName("cardTitle")
        header.addWidget(self._title, 1)
        self._percent = QLabel("0%")
        self._percent.setObjectName("percentLabel")
        header.addWidget(self._percent)

        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("dismissBtn")
        self._close_btn.setFixedSize(24, 24)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self.dismissed.emit)
        header.addWidget(self._close_btn)

        layout.addLayout(header)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar)

        self._stats = _ElidedLabel("")
        self._stats.setObjectName("statsLabel")
        layout.addWidget(self._stats)

    def on_progress(self, percent: int) -> None:
        if self._is_done:
            return
        self._bar.setValue(percent)
        self._percent.setText(f"{percent}%")

    def on_status(self, message: str) -> None:
        if self._is_done:
            return
        if "·" in message:
            self._stats.setText(message)
        elif "Merging" in message or "audio track" in message:
            self._stats.setText(message)
        else:
            self._title.setText(message)

    def mark_complete(self, filepath: str) -> None:
        self._is_done = True
        self._filepath = filepath
        self._title.setText(os.path.basename(filepath))
        self._bar.setValue(100)
        self._percent.setText("100%")
        self._stats.setObjectName("successLabel")
        self._stats.setStyleSheet("")
        self._stats.setText(f"Saved to: {os.path.dirname(filepath)}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mark_error(self, message: str) -> None:
        self._is_done = True
        self._stats.setObjectName("errorLabel")
        self._stats.setStyleSheet("")
        self._stats.setText(message)

    def mousePressEvent(self, event) -> None:
        if self._is_done and self._filepath and os.path.exists(self._filepath):
            self.open_file.emit(self._filepath)
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    """Main window with URL input, download controls, and progress display."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DownXV")
        self.setMinimumSize(976, 630)
        self.resize(976, 630)

        self._default_save_path = os.path.expanduser("~/Downloads")
        self._tasks: list[dict] = []
        self._info_extractor: InfoExtractWorker | None = None
        self._titlebar_styled = False

        self._build_ui()
        self._build_menu()
        self._connect_signals()

    # ── UI Construction ──────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left panel: controls ──
        left = QWidget()
        left_col = QVBoxLayout(left)
        left_col.setContentsMargins(32, 52, 24, 28)
        left_col.setSpacing(16)

        self._build_header(left_col)
        self._build_url_card(left_col)
        self._build_options_card(left_col)

        self._download_btn = QPushButton("Download Video")
        self._download_btn.setObjectName("downloadBtn")
        self._download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        left_col.addWidget(self._download_btn)

        self._error_label = QLabel("")
        self._error_label.setObjectName("errorLabel")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        left_col.addWidget(self._error_label)

        left_col.addStretch()
        self._build_update_bar(left_col)
        root.addWidget(left, 1)

        # ── Separator ──
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        root.addWidget(sep)

        # ── Right panel: download list ──
        right = QWidget()
        right_col = QVBoxLayout(right)
        right_col.setContentsMargins(24, 52, 32, 28)
        right_col.setSpacing(12)

        right_header = QHBoxLayout()
        dl_label = QLabel("DOWNLOADS")
        dl_label.setObjectName("sectionLabel")
        right_header.addWidget(dl_label)
        right_header.addStretch()
        self._clear_all_btn = QPushButton("Clear All")
        self._clear_all_btn.setObjectName("clearAllBtn")
        self._clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_all_btn.hide()
        right_header.addWidget(self._clear_all_btn)
        right_col.addLayout(right_header)

        scroll = QScrollArea()
        scroll.setObjectName("tasksScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(8)

        self._tasks_layout = scroll_layout

        self._empty_label = QLabel("No downloads yet")
        self._empty_label.setObjectName("statusLabel")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(self._empty_label)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        right_col.addWidget(scroll, 1)
        root.addWidget(right, 1)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        app_menu = menu_bar.addMenu("DownXV")
        about_action = QAction("About DownXV", self)
        about_action.setMenuRole(QAction.MenuRole.AboutRole)
        about_action.triggered.connect(self._show_about)
        app_menu.addAction(about_action)

    def _show_about(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("About DownXV")
        dlg.setFixedSize(340, 280)
        dlg.setStyleSheet(
            "QDialog { background: #ffffff; border-radius: 16px; }"
        )

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(0)

        # Logo
        logo = QLabel()
        logo.setPixmap(create_logo_pixmap(64))
        logo.setFixedSize(64, 64)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(14)

        # Title
        title = QLabel("DownXV")
        title.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #1a1a2e;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(4)

        # Version
        ver = QLabel(f"Version {__version__}")
        ver.setStyleSheet("font-size: 12px; color: #9394a0;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)
        layout.addSpacing(16)

        # Description
        desc = QLabel("Download videos from X/Twitter with ease.")
        desc.setStyleSheet("font-size: 13px; color: #6e6e80;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(4)

        tech = QLabel("Built with PySide6 + yt-dlp")
        tech.setStyleSheet("font-size: 11px; color: #b0b0be;")
        tech.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tech)

        layout.addStretch()

        # GitHub icon button
        gh_btn = QPushButton()
        gh_btn.setIcon(QIcon(self._asset_path("icon-github.svg")))
        gh_btn.setIconSize(QSize(22, 22))
        gh_btn.setFixedSize(36, 36)
        gh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gh_btn.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: none;"
            "  border-radius: 18px;"
            "}"
            "QPushButton:hover {"
            "  background: #f0f0f4;"
            "}"
        )
        gh_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/zzjoey/DownXV")
            )
        )
        layout.addWidget(gh_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        dlg.exec()

    def _build_header(self, parent: QVBoxLayout) -> None:
        header_btn = QPushButton()
        header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none;"
            " border-radius: 10px; padding: 0px; }"
            "QPushButton:hover { background: #f0f0f4; }"
        )
        header_btn.setMinimumHeight(64)
        header_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/zzjoey/DownXV")
            )
        )

        header = QHBoxLayout(header_btn)
        header.setContentsMargins(8, 8, 8, 8)
        header.setSpacing(14)

        logo_label = QLabel()
        logo_label.setPixmap(create_logo_pixmap(48))
        logo_label.setFixedSize(48, 48)
        header.addWidget(logo_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        title = QLabel("DownXV")
        title.setObjectName("appTitle")
        text_col.addWidget(title)
        subtitle = QLabel("Download videos from X / Twitter")
        subtitle.setObjectName("appSubtitle")
        text_col.addWidget(subtitle)
        header.addLayout(text_col)

        header.addStretch()
        parent.addWidget(header_btn)

    def _build_url_card(self, parent: QVBoxLayout) -> None:
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)

        section = QLabel("VIDEO URL")
        section.setObjectName("sectionLabel")
        card_layout.addWidget(section)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText(
            "https://x.com/user/status/123456789..."
        )
        card_layout.addWidget(self._url_input)

        parent.addWidget(card)

    def _build_options_card(self, parent: QVBoxLayout) -> None:
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)

        section = QLabel("OPTIONS")
        section.setObjectName("sectionLabel")
        card_layout.addWidget(section)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        path_label = QLabel("Save to")
        path_label.setFixedWidth(55)
        path_row.addWidget(path_label)
        self._path_input = QLineEdit(self._default_save_path)
        self._path_input.setReadOnly(True)
        path_row.addWidget(self._path_input)
        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.setObjectName("browseBtn")
        path_row.addWidget(self._browse_btn)
        card_layout.addLayout(path_row)

        opts_row = QHBoxLayout()
        opts_row.setSpacing(16)

        q_group = QHBoxLayout()
        q_group.setSpacing(8)
        q_label = QLabel("Quality")
        q_group.addWidget(q_label, 0, Qt.AlignmentFlag.AlignVCenter)
        self._quality_combo = QComboBox()
        self._quality_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self._quality_combo.setMaxVisibleItems(5)
        self._quality_combo.addItems(
            ["Best (default)", "1080p", "720p", "480p", "Audio only"]
        )
        q_group.addWidget(self._quality_combo)
        opts_row.addLayout(q_group)

        c_group = QHBoxLayout()
        c_group.setSpacing(8)
        c_label = QLabel("Cookies")
        c_group.addWidget(c_label, 0, Qt.AlignmentFlag.AlignVCenter)
        self._cookie_combo = QComboBox()
        self._cookie_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self._cookie_combo.setMaxVisibleItems(4)
        self._cookie_combo.setIconSize(QSize(16, 16))
        for name, icon_file in [
            ("Chrome", "icon-chrome.svg"),
            ("Firefox", "icon-firefox.svg"),
            ("Edge", "icon-edge.svg"),
            ("None", "icon-none.svg"),
        ]:
            self._cookie_combo.addItem(
                QIcon(self._asset_path(icon_file)), name
            )
        c_group.addWidget(self._cookie_combo)
        opts_row.addLayout(c_group)

        opts_row.addStretch()
        card_layout.addLayout(opts_row)

        # Make popup container transparent so only the item view renders
        for combo in (self._quality_combo, self._cookie_combo):
            # Custom delegate to enforce proper row height (QSS ::item
            # padding/min-height do not affect actual item geometry).
            delegate = QStyledItemDelegate(combo)
            combo.setItemDelegate(delegate)
            for i in range(combo.count()):
                combo.setItemData(i, QSize(0, 36), Qt.ItemDataRole.SizeHintRole)

            container = combo.view().parentWidget()
            if container:
                container.setWindowFlags(
                    Qt.WindowType.Popup
                    | Qt.WindowType.FramelessWindowHint
                )
                container.setAttribute(
                    Qt.WidgetAttribute.WA_TranslucentBackground
                )
                container.setObjectName("comboPopup")
                container.setStyleSheet(
                    "#comboPopup { background: transparent;"
                    " border: none; }"
                )
            # Ensure popup view is wide enough for content
            hint = combo.view().sizeHintForColumn(0)
            combo.view().setMinimumWidth(hint + 24)

        parent.addWidget(card)

    # ── Update bar ─────────────────────────────────────────────

    def _build_update_bar(self, parent: QVBoxLayout) -> None:
        bar = QHBoxLayout()
        bar.setContentsMargins(4, 0, 4, 0)
        bar.setSpacing(6)

        self._update_icon = QLabel()
        self._update_icon.setObjectName("updateIcon")
        self._update_icon.setFixedWidth(16)
        bar.addWidget(self._update_icon)

        self._update_label = QLabel(f"v{__version__}")
        self._update_label.setObjectName("updateLabel")
        bar.addWidget(self._update_label)

        bar.addStretch()

        self._update_btn = QPushButton("Check for Updates")
        self._update_btn.setObjectName("updateBtn")
        self._update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_btn.clicked.connect(self._check_for_updates)
        bar.addWidget(self._update_btn)

        parent.addLayout(bar)

        self._update_url: str = ""
        self._update_checker: UpdateChecker | None = None

        # Auto-check on startup
        self._check_for_updates()

    def _check_for_updates(self) -> None:
        if self._update_checker and self._update_checker.isRunning():
            return
        self._update_icon.setText("")
        self._update_label.setText("Checking for updates...")
        self._update_btn.setEnabled(False)

        self._update_checker = UpdateChecker(__version__)
        self._update_checker.result.connect(self._on_update_result)
        self._update_checker.error.connect(self._on_update_error)
        self._update_checker.start()

    def _on_update_result(self, result) -> None:
        if result.is_newer:
            self._update_icon.setText("\u2b06")  # ⬆
            self._update_icon.setStyleSheet(
                "font-size: 14px; color: #7b39fc; background: transparent;"
            )
            self._update_label.setText(
                f"v{result.latest_version} available"
            )
            self._update_label.setStyleSheet(
                "font-size: 12px; color: #7b39fc; background: transparent;"
            )
            self._update_btn.setText("Download Update")
            self._update_btn.setProperty("updateAvailable", True)
            self._update_btn.style().unpolish(self._update_btn)
            self._update_btn.style().polish(self._update_btn)
            self._update_url = result.download_url
            try:
                self._update_btn.clicked.disconnect()
            except RuntimeError:
                pass
            self._update_btn.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl(self._update_url))
            )
        else:
            self._update_icon.setText("\u2713")  # ✓
            self._update_icon.setStyleSheet(
                "font-size: 14px; color: #18794e; background: transparent;"
            )
            self._update_label.setText(f"v{__version__} \u00b7 Up to date")
            self._update_label.setStyleSheet(
                "font-size: 12px; color: #9394a0; background: transparent;"
            )
        self._update_btn.setEnabled(True)

    def _on_update_error(self, msg: str) -> None:
        self._update_icon.setText("\u2716")  # ✖
        self._update_icon.setStyleSheet(
            "font-size: 14px; color: #e5484d; background: transparent;"
        )
        self._update_label.setText("Update check failed")
        self._update_label.setStyleSheet(
            "font-size: 12px; color: #e5484d; background: transparent;"
        )
        self._update_btn.setText("Retry")
        self._update_btn.setEnabled(True)

    # ── Signal Wiring ────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._download_btn.clicked.connect(self._on_download)
        self._browse_btn.clicked.connect(self._on_browse)
        self._clear_all_btn.clicked.connect(self._clear_all)
        self._url_input.returnPressed.connect(self._on_download)

    # ── Slots ────────────────────────────────────────────────────

    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", self._path_input.text()
        )
        if path:
            self._path_input.setText(path)

    def _on_download(self) -> None:
        raw_url = self._url_input.text().strip()

        if not raw_url:
            self._show_error("Please enter a URL.")
            return

        url = validate_url(raw_url)
        if url is None:
            self._show_error(
                "Invalid URL. Paste a link like https://x.com/user/status/..."
            )
            return

        save_path = self._path_input.text()
        if not os.path.isdir(save_path):
            self._show_error("Save directory does not exist.")
            return

        self._clear_error()

        quality = self._quality_combo.currentText()
        cookie_browser = self._cookie_combo.currentText().lower()

        # Phase 1: extract info to discover video count
        self._download_btn.setEnabled(False)
        self._download_btn.setText("Extracting video info...")

        extractor = InfoExtractWorker(url, cookie_browser)
        self._info_extractor = extractor
        extractor.info_ready.connect(
            lambda info, u=url, s=save_path, q=quality, c=cookie_browser:
                self._on_info_ready(info, u, s, q, c)
        )
        extractor.error.connect(self._on_info_error)
        extractor.finished.connect(self._on_info_extractor_done)

        self._url_input.clear()
        self._url_input.setFocus()
        extractor.start()

    def _on_info_ready(
        self, info: dict, url: str, save_path: str,
        quality: str, cookie_browser: str,
    ) -> None:
        """Phase 2: create one card + worker per video."""
        entries = info.get("entries")

        if entries:
            entries_list = [e for e in entries if e is not None]
            video_count = len(entries_list)
            parent_title = info.get("title", "video")
            workers: list[DownloadWorker] = []
            for i, entry in enumerate(entries_list, 1):
                title = entry.get("title", parent_title)
                if video_count > 1:
                    display = f"{title[:50]} ({i}/{video_count})"
                else:
                    display = title[:60]
                w = self._create_download(
                    url, save_path, quality, cookie_browser,
                    display, playlist_item=i,
                )
                workers.append(w)
            # Stagger starts so video 1 begins first
            for idx, w in enumerate(workers):
                QTimer.singleShot(idx * 200, w.start)
        else:
            title = info.get("title", "video")
            w = self._create_download(
                url, save_path, quality, cookie_browser, title[:60],
            )
            w.start()

    def _create_download(
        self, url: str, save_path: str, quality: str,
        cookie_browser: str, title: str,
        playlist_item: int | None = None,
    ) -> DownloadWorker:
        card = _DownloadCard(title)
        self._tasks_layout.insertWidget(self._tasks_layout.count() - 1, card)

        worker = DownloadWorker(
            url, save_path, quality, cookie_browser,
            playlist_item=playlist_item,
        )
        task = {"worker": worker, "card": card, "active": True}
        self._tasks.append(task)

        worker.progress.connect(card.on_progress)
        worker.status_update.connect(card.on_status)
        worker.finished_ok.connect(
            lambda path, t=task: self._on_task_finished(t, path)
        )
        worker.error.connect(
            lambda msg, t=task: self._on_task_error(t, msg)
        )
        worker.finished.connect(
            lambda t=task: self._on_task_worker_done(t)
        )
        card.dismissed.connect(lambda t=task: self._dismiss_task(t))
        card.open_file.connect(self._open_file)

        self._update_state()
        return worker

    def _on_info_error(self, message: str) -> None:
        self._show_error(message)

    def _on_info_extractor_done(self) -> None:
        self._info_extractor = None
        self._update_state()

    # ── Task callbacks ───────────────────────────────────────────

    def _on_task_finished(self, task: dict, filepath: str) -> None:
        task["card"].mark_complete(filepath)

    def _on_task_error(self, task: dict, message: str) -> None:
        task["card"].mark_error(message)

    def _on_task_worker_done(self, task: dict) -> None:
        task["active"] = False
        w = task["worker"]
        if w:
            w.deleteLater()
            task["worker"] = None
        self._update_state()

    @staticmethod
    def _disconnect_worker(worker: "DownloadWorker") -> None:
        for sig in (worker.progress, worker.status_update,
                    worker.finished_ok, worker.error, worker.finished):
            try:
                sig.disconnect()
            except RuntimeError:
                pass

    def _dismiss_task(self, task: dict) -> None:
        if task not in self._tasks:
            return
        worker = task.get("worker")
        if worker and task["active"]:
            self._disconnect_worker(worker)
            worker.cancel()
            worker.wait(3000)
            if worker.isRunning():
                # Worker is still blocked (e.g. in extract_info).
                # Deleting a running QThread crashes, so defer cleanup
                # until the thread actually finishes.
                worker.finished.connect(worker.deleteLater)
            else:
                worker.deleteLater()
            task["worker"] = None
            task["active"] = False
        self._tasks.remove(task)
        card = task["card"]
        self._tasks_layout.removeWidget(card)
        card.deleteLater()
        self._update_state()

    def _open_file(self, filepath: str) -> None:
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", filepath])
        elif sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", filepath])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(filepath)])

    def _clear_all(self) -> None:
        for task in list(self._tasks):
            if not task["active"]:
                self._tasks.remove(task)
                card = task["card"]
                self._tasks_layout.removeWidget(card)
                card.deleteLater()
        self._update_state()

    # ── Window close ─────────────────────────────────────────

    def closeEvent(self, event) -> None:
        if self._info_extractor and self._info_extractor.isRunning():
            self._info_extractor.cancel()
            self._info_extractor.wait(2000)
        for task in self._tasks:
            worker = task.get("worker")
            if worker and task["active"]:
                self._disconnect_worker(worker)
                worker.cancel()
                worker.wait(3000)
                if worker.isRunning():
                    worker.finished.connect(worker.deleteLater)
        super().closeEvent(event)

    # ── macOS title bar ────────────────────────────────────────

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._titlebar_styled:
            self._titlebar_styled = True
            self._style_macos_titlebar()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            old = event.oldState()
            cur = self.windowState()
            if (old & Qt.WindowState.WindowFullScreen) and not (
                cur & Qt.WindowState.WindowFullScreen
            ):
                self._style_macos_titlebar()

    def _style_macos_titlebar(self) -> None:
        if sys.platform != "darwin":
            return
        try:
            from ctypes import c_bool, c_uint, c_void_p, cdll, util

            objc = cdll.LoadLibrary(util.find_library("objc"))
            objc.objc_getClass.restype = c_void_p
            objc.sel_registerName.restype = c_void_p
            objc.objc_msgSend.restype = c_void_p
            objc.objc_msgSend.argtypes = [c_void_p, c_void_p]

            ns_view = int(self.winId())
            ns_window = objc.objc_msgSend(
                ns_view, objc.sel_registerName(b"window")
            )

            # titlebarAppearsTransparent = YES
            objc.objc_msgSend.argtypes = [c_void_p, c_void_p, c_bool]
            objc.objc_msgSend(
                ns_window,
                objc.sel_registerName(b"setTitlebarAppearsTransparent:"),
                True,
            )

            # titleVisibility = NSWindowTitleHidden (1)
            objc.objc_msgSend.argtypes = [c_void_p, c_void_p, c_uint]
            objc.objc_msgSend(
                ns_window,
                objc.sel_registerName(b"setTitleVisibility:"),
                1,
            )

            # Add fullSizeContentView to style mask
            objc.objc_msgSend.argtypes = [c_void_p, c_void_p]
            objc.objc_msgSend.restype = c_uint
            mask = objc.objc_msgSend(
                ns_window, objc.sel_registerName(b"styleMask")
            )
            objc.objc_msgSend.restype = c_void_p
            objc.objc_msgSend.argtypes = [c_void_p, c_void_p, c_uint]
            objc.objc_msgSend(
                ns_window,
                objc.sel_registerName(b"setStyleMask:"),
                mask | (1 << 15),  # NSFullSizeContentViewWindowMask
            )
        except Exception:
            pass

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _asset_path(filename: str) -> str:
        base = os.path.join(os.path.dirname(__file__), os.pardir, "assets")
        return os.path.normpath(os.path.join(base, filename))

    def _active_count(self) -> int:
        return sum(1 for t in self._tasks if t["active"])

    def _done_count(self) -> int:
        return sum(1 for t in self._tasks if not t["active"])

    def _update_state(self) -> None:
        active = self._active_count()
        done = self._done_count()
        total = len(self._tasks)
        extracting = (
            self._info_extractor is not None
            and self._info_extractor.isRunning()
        )
        at_limit = active >= _MAX_CONCURRENT or extracting
        self._download_btn.setEnabled(not at_limit)
        if extracting:
            self._download_btn.setText("Extracting video info...")
        elif active >= _MAX_CONCURRENT:
            self._download_btn.setText("Downloading...")
        else:
            self._download_btn.setText("Download Video")
        self._clear_all_btn.setVisible(done > 0)
        self._empty_label.setVisible(total == 0)

    def _show_error(self, message: str) -> None:
        self._error_label.setText(message)
        self._error_label.show()

    def _clear_error(self) -> None:
        self._error_label.setText("")
        self._error_label.hide()
