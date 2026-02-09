"""Load DownXV logo from assets/logo.png."""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

_LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png"
)


def create_logo_pixmap(size: int = 128) -> QPixmap:
    """Load the PNG logo as a QPixmap scaled to the given size."""
    pixmap = QPixmap(_LOGO_PATH)
    return pixmap.scaled(
        size, size, Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def create_app_icon() -> QIcon:
    """Create a multi-resolution QIcon from the PNG logo."""
    icon = QIcon()
    for s in (16, 32, 64, 128, 256):
        icon.addPixmap(create_logo_pixmap(s))
    return icon
