#!/usr/bin/env bash
set -euo pipefail

APP_NAME="nonet-movie"
APP_DISPLAY_NAME="Nonet Movie"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
WORK_DIR="$DIST_DIR/macos-dmg-work"
BUILD_DIR="$PROJECT_ROOT/build/macos-dmg"
PYI_WORK_DIR="$PROJECT_ROOT/build/pyinstaller-macos-dmg"
ENTRY_POINT="$PROJECT_ROOT/scripts/windows_main.py"
ICON_SOURCE="$PROJECT_ROOT/assets/nonet-movie.svg"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v hdiutil >/dev/null 2>&1; then
  echo "hdiutil is required. Run this script on macOS."
  exit 1
fi

if ! command -v iconutil >/dev/null 2>&1; then
  echo "iconutil is required to build macOS app icons."
  exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    echo "python3 is required but was not found."
    exit 1
  fi
fi

if [ ! -f "$ICON_SOURCE" ]; then
  echo "Missing shared icon file: $ICON_SOURCE"
  exit 1
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

STAGE_ROOT="$WORK_DIR/${APP_NAME}-${VERSION}"
APP_BUNDLE="$STAGE_ROOT/${APP_DISPLAY_NAME}.app"
APP_CONTENTS_DIR="$APP_BUNDLE/Contents"
APP_MACOS_DIR="$APP_CONTENTS_DIR/MacOS"
APP_RESOURCES_DIR="$APP_CONTENTS_DIR/Resources"
APP_EXECUTABLE="$APP_MACOS_DIR/$APP_NAME"
APP_LAUNCHER="$APP_MACOS_DIR/nonet-movie-launcher"
APP_INFO_PLIST="$APP_CONTENTS_DIR/Info.plist"
ICONSET_DIR="$BUILD_DIR/nonet-movie.iconset"
ICON_BASE_PNG="$BUILD_DIR/nonet-movie-1024.png"
APP_ICON_ICNS="$APP_RESOURCES_DIR/nonet-movie.icns"
DMG_ROOT="$STAGE_ROOT/dmg-root"
OUTPUT_DMG="$DIST_DIR/${APP_NAME}-${VERSION}.dmg"

echo "Building ${APP_NAME}-${VERSION}.dmg ..."
rm -rf "$STAGE_ROOT" "$BUILD_DIR" "$PYI_WORK_DIR"
mkdir -p "$APP_MACOS_DIR" "$APP_RESOURCES_DIR" "$BUILD_DIR" "$PYI_WORK_DIR" "$DMG_ROOT" "$DIST_DIR"

if command -v magick >/dev/null 2>&1; then
  magick "$ICON_SOURCE" -background none -resize 1024x1024 "$ICON_BASE_PNG"
else
  sips -s format png "$ICON_SOURCE" --out "$ICON_BASE_PNG" >/dev/null
fi

mkdir -p "$ICONSET_DIR"
sips -z 16 16 "$ICON_BASE_PNG" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null
sips -z 32 32 "$ICON_BASE_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
sips -z 32 32 "$ICON_BASE_PNG" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null
sips -z 64 64 "$ICON_BASE_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
sips -z 128 128 "$ICON_BASE_PNG" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null
sips -z 256 256 "$ICON_BASE_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
sips -z 256 256 "$ICON_BASE_PNG" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null
sips -z 512 512 "$ICON_BASE_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
sips -z 512 512 "$ICON_BASE_PNG" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null
cp "$ICON_BASE_PNG" "$ICONSET_DIR/icon_512x512@2x.png"
iconutil -c icns "$ICONSET_DIR" -o "$APP_ICON_ICNS"

"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --console \
  --name "$APP_NAME" \
  --distpath "$APP_MACOS_DIR" \
  --workpath "$PYI_WORK_DIR" \
  "$ENTRY_POINT"
chmod 0755 "$APP_EXECUTABLE"

cat > "$APP_LAUNCHER" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_BIN="$SCRIPT_DIR/nonet-movie"

APP_BIN="$APP_BIN" /usr/bin/osascript <<'APPLESCRIPT' >/dev/null 2>&1
set appCommand to system attribute "APP_BIN"
set wrappedCommand to "bash -lc " & quoted form of ("\"" & appCommand & "\"")
tell application "Terminal"
  activate
  if not (exists window 1) then reopen
  do script wrappedCommand in window 1
end tell
APPLESCRIPT
EOF
chmod 0755 "$APP_LAUNCHER"

cat > "$APP_INFO_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>${APP_DISPLAY_NAME}</string>
  <key>CFBundleDisplayName</key>
  <string>${APP_DISPLAY_NAME}</string>
  <key>CFBundleIdentifier</key>
  <string>com.ariana.nonet-movie.app</string>
  <key>CFBundleVersion</key>
  <string>${VERSION}</string>
  <key>CFBundleShortVersionString</key>
  <string>${VERSION}</string>
  <key>CFBundleExecutable</key>
  <string>nonet-movie-launcher</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleIconFile</key>
  <string>nonet-movie.icns</string>
  <key>LSMinimumSystemVersion</key>
  <string>10.13</string>
</dict>
</plist>
EOF
chmod 0644 "$APP_INFO_PLIST"

cp -R "$APP_BUNDLE" "$DMG_ROOT/"
ln -s /Applications "$DMG_ROOT/Applications"

rm -f "$OUTPUT_DMG"
hdiutil create \
  -volname "${APP_DISPLAY_NAME}" \
  -srcfolder "$DMG_ROOT" \
  -ov \
  -format UDZO \
  "$OUTPUT_DMG" >/dev/null

echo "Created: $OUTPUT_DMG"
