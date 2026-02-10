#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

APP_NAME="DownXV"
VERSION=$(grep -o '__version__\s*=\s*"[^"]*"' src/__init__.py | cut -d'"' -f2)
DMG_NAME="${APP_NAME}-${VERSION}.dmg"

echo "==> Building ${APP_NAME}.app ..."
source .venv/bin/activate
pyinstaller build.spec --noconfirm

echo "==> Packaging ${DMG_NAME} ..."
rm -f "dist/${DMG_NAME}"

create-dmg \
    --volname "$APP_NAME" \
    --volicon "assets/icon.icns" \
    --window-pos 200 120 \
    --window-size 660 400 \
    --icon-size 128 \
    --icon "$APP_NAME.app" 160 185 \
    --app-drop-link 500 185 \
    --hide-extension "$APP_NAME.app" \
    --no-internet-enable \
    "dist/${DMG_NAME}" \
    "dist/${APP_NAME}.app"

echo ""
echo "Done: dist/${DMG_NAME}"
