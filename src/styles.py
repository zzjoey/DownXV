"""QSS stylesheet for DownXV — premium light theme."""

import os

_ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets"
)


def _asset(name: str) -> str:
    return os.path.normpath(os.path.join(_ASSETS_DIR, name)).replace("\\", "/")


STYLESHEET = """
/* ── Global ── */
* {
    font-family: ".AppleSystemUIFont", "SF Pro Text", "Helvetica Neue",
                 "Segoe UI", sans-serif;
}

QMainWindow {
    background-color: #f5f5f7;
}

/* ── Cards ── */
QFrame#card {
    background-color: #ffffff;
    border: 1px solid #e8e8ec;
    border-radius: 12px;
}

/* ── Scroll area ── */
QScrollArea#tasksScroll {
    background: transparent;
    border: none;
}

QScrollArea#tasksScroll > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #d0d0d8;
    border-radius: 3px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #b0b0be;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
    height: 0px;
}

/* ── Separator ── */
QFrame#separator {
    background-color: #e8e8ec;
    border: none;
}

/* ── Labels ── */
QLabel {
    font-size: 13px;
    color: #6e6e80;
    background: transparent;
}

QLabel#appTitle {
    font-size: 26px;
    font-weight: 700;
    color: #1a1a2e;
    background: transparent;
}

QLabel#appSubtitle {
    font-size: 13px;
    color: #9394a0;
    background: transparent;
}

QLabel#sectionLabel {
    font-size: 11px;
    font-weight: 600;
    color: #7b39fc;
    text-transform: uppercase;
    letter-spacing: 1px;
    background: transparent;
}

QLabel#cardTitle {
    font-size: 13px;
    font-weight: 600;
    color: #1a1a2e;
    background: transparent;
}

QLabel#percentLabel {
    font-size: 16px;
    font-weight: 700;
    color: #1a1a2e;
    background: transparent;
}

QLabel#statsLabel {
    font-size: 11px;
    color: #9394a0;
    background: transparent;
}

QLabel#statusLabel {
    font-size: 12px;
    color: #9394a0;
    background: transparent;
}

QLabel#errorLabel {
    font-size: 12px;
    color: #e5484d;
    background: transparent;
}

QLabel#successLabel {
    font-size: 12px;
    color: #18794e;
    background: transparent;
}

/* ── Input fields ── */
QLineEdit {
    padding: 10px 14px;
    border: 1px solid #e0e0e6;
    border-radius: 10px;
    background-color: #f8f8fa;
    font-size: 14px;
    color: #1a1a2e;
    selection-background-color: #d4bfff;
    selection-color: #1a1a2e;
}

QLineEdit:focus {
    border-color: #7b39fc;
    background-color: #ffffff;
}

QLineEdit:read-only {
    background-color: #f0f0f4;
    color: #6e6e80;
}

QLineEdit::placeholder {
    color: #b0b0be;
}

/* ── Download button ── */
QPushButton#downloadBtn {
    background-color: #7b39fc;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    padding: 14px;
    font-size: 15px;
    font-weight: 700;
}

QPushButton#downloadBtn:hover {
    background-color: #6a2ce0;
}

QPushButton#downloadBtn:pressed {
    background-color: #5a22c0;
}

QPushButton#downloadBtn:disabled {
    background-color: #e8e8ec;
    color: #b0b0be;
}

/* ── Browse button ── */
QPushButton#browseBtn {
    padding: 10px 18px;
    border: 1px solid #e0e0e6;
    border-radius: 10px;
    background-color: #ffffff;
    font-size: 13px;
    color: #6e6e80;
}

QPushButton#browseBtn:hover {
    background-color: #f0f0f4;
    border-color: #7b39fc;
    color: #1a1a2e;
}

/* ── Dismiss button (card close) ── */
QPushButton#dismissBtn {
    background: transparent;
    border: none;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
    color: #b0b0be;
}

QPushButton#dismissBtn:hover {
    background-color: #ebebf0;
    color: #6e6e80;
}

/* ── Clear All button ── */
QPushButton#clearAllBtn {
    background: transparent;
    border: none;
    font-size: 12px;
    font-weight: 600;
    color: #9394a0;
    padding: 4px 8px;
}

QPushButton#clearAllBtn:hover {
    color: #e5484d;
}

/* ── Progress bar ── */
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #ebebf0;
    text-align: center;
    max-height: 8px;
    min-height: 8px;
}

QProgressBar::chunk {
    border-radius: 4px;
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b39fc, stop:1 #a78bfa
    );
}

/* ── Combo boxes ── */
QComboBox {
    combobox-popup: 0;
    padding: 8px 28px 8px 12px;
    border: 1px solid #e0e0e6;
    border-radius: 10px;
    background-color: #f8f8fa;
    font-size: 13px;
    color: #1a1a2e;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #c4b5fd;
    background-color: #ffffff;
}

QComboBox:on {
    border-color: #7b39fc;
    background-color: #ffffff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    background: transparent;
}

QComboBox::down-arrow {
    image: url(%%CHEVRON_DOWN%%);
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    border: 1px solid #e0e0e6;
    background-color: #ffffff;
    color: #1a1a2e;
    padding: 4px;
    outline: none;
    selection-background-color: transparent;
    selection-color: #7b39fc;
}

QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    border-radius: 6px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #f5f3ff;
    color: #1a1a2e;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #f0ebff;
    color: #7b39fc;
}
/* ── Update bar ── */
QLabel#updateIcon {
    font-size: 14px;
    background: transparent;
}

QLabel#updateLabel {
    font-size: 12px;
    color: #9394a0;
    background: transparent;
}

QPushButton#updateBtn {
    background: transparent;
    border: 1px solid #e0e0e6;
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 600;
    color: #6e6e80;
}

QPushButton#updateBtn:hover {
    border-color: #7b39fc;
    color: #7b39fc;
    background-color: #f5f3ff;
}

QPushButton#updateBtn[updateAvailable="true"] {
    border-color: #7b39fc;
    color: #ffffff;
    background-color: #7b39fc;
}

QPushButton#updateBtn[updateAvailable="true"]:hover {
    background-color: #6a2ce0;
}
""".replace("%%CHEVRON_DOWN%%", _asset("chevron-down.svg"))
