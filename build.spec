# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for DownXV macOS app."""

import re

from PyInstaller.utils.hooks import collect_data_files

_version = re.search(
    r'__version__\s*=\s*"([^"]+)"',
    open("src/__init__.py").read(),
).group(1)

a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("assets/logo.png", "assets"),
        ("assets/icon-chrome.svg", "assets"),
        ("assets/icon-firefox.svg", "assets"),
        ("assets/icon-edge.svg", "assets"),
        ("assets/icon-none.svg", "assets"),
        ("assets/icon-github.svg", "assets"),
        ("assets/chevron-down.svg", "assets"),
        *collect_data_files("certifi"),
    ],
    hiddenimports=[
        "src",
        "src.app",
        "src.main_window",
        "src.downloader",
        "src.url_validator",
        "src.styles",
        "src.logo",
        "src.updater",
        "certifi",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DownXV",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DownXV",
)

app = BUNDLE(
    coll,
    name="DownXV.app",
    icon="assets/icon.icns",
    bundle_identifier="com.joey.downxv",
    info_plist={
        "CFBundleName": "DownXV",
        "CFBundleDisplayName": "DownXV",
        "CFBundleShortVersionString": _version,
        "CFBundleVersion": _version,
        "NSHighResolutionCapable": True,
    },
)
