#!/usr/bin/env bash
set -euo pipefail

APP_NAME="nonet-movie"
PKG_ID="${PKG_ID:-com.ariana.nonet-movie}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
WORK_DIR="$DIST_DIR/macos-pkg-work"
BUILD_DIR="$PROJECT_ROOT/build/pyinstaller-macos-pkg"
ENTRY_POINT="$PROJECT_ROOT/scripts/windows_main.py"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v pkgbuild >/dev/null 2>&1; then
  echo "pkgbuild is required. Run this script on macOS with Xcode CLT installed."
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

PKG_STAGE="$WORK_DIR/${APP_NAME}-${VERSION}"
PAYLOAD_ROOT="$PKG_STAGE/payload"
INSTALL_ROOT="$PAYLOAD_ROOT/opt/$APP_NAME"
BUNDLED_BIN="$INSTALL_ROOT/$APP_NAME"
BIN_PATH="$PAYLOAD_ROOT/usr/local/bin/$APP_NAME"
ETC_ENV_PATH="$PAYLOAD_ROOT/etc/nonet-movie.env"
OUTPUT_PKG="$DIST_DIR/${APP_NAME}-${VERSION}.pkg"

echo "Building ${APP_NAME}-${VERSION}.pkg ..."
rm -rf "$PKG_STAGE" "$BUILD_DIR"
mkdir -p "$INSTALL_ROOT" "$(dirname "$BIN_PATH")" "$(dirname "$ETC_ENV_PATH")" "$DIST_DIR" "$BUILD_DIR"

"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --console \
  --name "$APP_NAME" \
  --distpath "$INSTALL_ROOT" \
  --workpath "$BUILD_DIR" \
  "$ENTRY_POINT"

chmod 0755 "$BUNDLED_BIN"

cat > "$BIN_PATH" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Load optional environment files in priority order:
# 1) per-user override
# 2) system-wide package config
USER_ENV_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/nonet-movie/env"
SYSTEM_ENV_FILE="/etc/nonet-movie.env"

if [ -f "$SYSTEM_ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$SYSTEM_ENV_FILE"
  set +a
fi

if [ -f "$USER_ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$USER_ENV_FILE"
  set +a
fi

JSON_DB_PATH="${JSON_DB_PATH:-$HOME/.local/share/nonet-movie/storage/}"
LOG_PATH="${LOG_PATH:-$HOME/.local/share/nonet-movie/logs}"
mkdir -p "$JSON_DB_PATH" "$LOG_PATH"
export JSON_DB_PATH
export LOG_PATH

exec /opt/nonet-movie/nonet-movie "$@"
EOF
chmod 0755 "$BIN_PATH"

cat > "$ETC_ENV_PATH" <<'EOF'
# System-wide defaults for nonet-movie.
# Defaults can be overridden per user in:
#   ~/.config/nonet-movie/env
JSON_DB_PATH=~/.local/share/nonet-movie/storage/
LOG_PATH=~/.local/share/nonet-movie/logs
EOF
chmod 0644 "$ETC_ENV_PATH"

rm -f "$OUTPUT_PKG"
pkgbuild \
  --root "$PAYLOAD_ROOT" \
  --identifier "$PKG_ID" \
  --version "$VERSION" \
  --install-location "/" \
  "$OUTPUT_PKG"

echo "Created: $OUTPUT_PKG"
