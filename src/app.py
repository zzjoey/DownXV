"""Application entry point for DownXV."""

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .logo import create_app_icon
from .main_window import MainWindow
from .styles import STYLESHEET


def _set_macos_dock_name(name: str) -> None:
    """Set the application name displayed in the macOS Dock."""
    if sys.platform != "darwin":
        return
    try:
        from ctypes import c_char_p, c_void_p, cdll, util

        objc = cdll.LoadLibrary(util.find_library("objc"))
        cf = cdll.LoadLibrary(util.find_library("CoreFoundation"))

        objc.objc_getClass.restype = c_void_p
        objc.sel_registerName.restype = c_void_p
        objc.objc_msgSend.restype = c_void_p
        objc.objc_msgSend.argtypes = [c_void_p, c_void_p]

        cf.__CFStringMakeConstantString.restype = c_void_p
        cf.__CFStringMakeConstantString.argtypes = [c_char_p]

        bundle = objc.objc_msgSend(
            objc.objc_getClass(b"NSBundle"),
            objc.sel_registerName(b"mainBundle"),
        )
        info = objc.objc_msgSend(
            bundle, objc.sel_registerName(b"infoDictionary")
        )

        objc.objc_msgSend.argtypes = [
            c_void_p, c_void_p, c_void_p, c_void_p,
        ]
        objc.objc_msgSend(
            info,
            objc.sel_registerName(b"setObject:forKey:"),
            cf.__CFStringMakeConstantString(name.encode("utf-8")),
            cf.__CFStringMakeConstantString(b"CFBundleName"),
        )
    except Exception:
        pass


def main() -> int:
    _set_macos_dock_name("DownXV")
    app = QApplication(sys.argv)
    app.setApplicationName("DownXV")
    app.setWindowIcon(create_app_icon())

    font = QFont(".AppleSystemUIFont")
    font.setPointSize(13)
    app.setFont(font)

    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    return app.exec()
