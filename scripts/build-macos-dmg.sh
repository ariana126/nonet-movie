#!/usr/bin/env bash
set -euo pipefail

APP_NAME="nonet-movie"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build/pyinstaller-macos"
ENTRY_POINT="$PROJECT_ROOT/scripts/windows_main.py"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ ! -x "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    echo "python3 is required but was not found."
    exit 1
  fi
fi

VERSION="${VERSION:-$("$PYTHON_BIN" - <<'PY'
import pathlib

project_file = pathlib.Path("pyproject.toml")
text = project_file.read_text(encoding="utf-8")
for line in text.splitlines():
    if line.startswith("version ="):
        print(line.split("=", 1)[1].strip().strip('"'))
        break
else:
    raise SystemExit("Unable to parse version from pyproject.toml")
PY
)}"

if ! "$PYTHON_BIN" -m PyInstaller --version >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pip install --upgrade pip
  "$PYTHON_BIN" -m pip install pyinstaller
fi

"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel
"$PYTHON_BIN" -m pip install "$PROJECT_ROOT"

mkdir -p "$DIST_DIR" "$BUILD_DIR"
rm -rf "$DIST_DIR/$APP_NAME.app" "$DIST_DIR/$APP_NAME-$VERSION.app"

echo "Building ${APP_NAME}.app ..."
"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --console \
  --name "$APP_NAME" \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  "$ENTRY_POINT"

APP_BUNDLE="$DIST_DIR/$APP_NAME.app"
VERSIONED_APP_BUNDLE="$DIST_DIR/$APP_NAME-$VERSION.app"
DMG_STAGING_DIR="$DIST_DIR/dmg-staging"
DMG_OUTPUT="$DIST_DIR/$APP_NAME-$VERSION-macos.dmg"

cp -R "$APP_BUNDLE" "$VERSIONED_APP_BUNDLE"
rm -rf "$DMG_STAGING_DIR"
mkdir -p "$DMG_STAGING_DIR"
cp -R "$VERSIONED_APP_BUNDLE" "$DMG_STAGING_DIR/"
ln -s /Applications "$DMG_STAGING_DIR/Applications"

rm -f "$DMG_OUTPUT"
hdiutil create \
  -volname "${APP_NAME}-${VERSION}" \
  -srcfolder "$DMG_STAGING_DIR" \
  -ov \
  -format UDZO \
  "$DMG_OUTPUT"

echo "Created: $APP_BUNDLE"
echo "Created: $VERSIONED_APP_BUNDLE"
echo "Created: $DMG_OUTPUT"
