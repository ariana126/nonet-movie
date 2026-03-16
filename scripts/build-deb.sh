#!/usr/bin/env bash
set -euo pipefail

APP_NAME="nonet-movie"
PKG_NAME="nonet-movie"
ARCH="${ARCH:-$(dpkg --print-architecture 2>/dev/null || echo amd64)}"
MAINTAINER="${MAINTAINER:-Ariana Maghsoudi <ariana.maghsoudi82@gmail.com>}"
SECTION="${SECTION:-utils}"
PRIORITY="${PRIORITY:-optional}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
WORK_DIR="$DIST_DIR/deb-work"
BUILD_DIR="$PROJECT_ROOT/build/pyinstaller-deb"
ENTRY_POINT="$PROJECT_ROOT/scripts/windows_main.py"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "dpkg-deb is required. Install with: sudo apt install dpkg-dev"
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

PKG_ROOT="$WORK_DIR/${PKG_NAME}_${VERSION}"
INSTALL_ROOT="$PKG_ROOT/opt/$APP_NAME"
BUNDLED_BIN="$INSTALL_ROOT/$APP_NAME"

echo "Building ${PKG_NAME}_${VERSION}.deb ..."
rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/DEBIAN" "$PKG_ROOT/usr/bin" "$PKG_ROOT/etc" "$INSTALL_ROOT"

if ! "$PYTHON_BIN" -m PyInstaller --version >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pip install --upgrade pip
  "$PYTHON_BIN" -m pip install pyinstaller
fi

"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel
"$PYTHON_BIN" -m pip install "$PROJECT_ROOT"

mkdir -p "$BUILD_DIR"
"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name "$APP_NAME" \
  --distpath "$INSTALL_ROOT" \
  --workpath "$BUILD_DIR" \
  "$ENTRY_POINT"

chmod 0755 "$BUNDLED_BIN"

cat > "$PKG_ROOT/usr/bin/$APP_NAME" <<'EOF'
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

# Debian-friendly defaults for user-writable app data and logs.
JSON_DB_PATH="${JSON_DB_PATH:-$HOME/.local/share/nonet-movie/storage/}"
LOG_PATH="${LOG_PATH:-$HOME/.local/share/nonet-movie/logs}"
mkdir -p "$JSON_DB_PATH" "$LOG_PATH"
export JSON_DB_PATH
export LOG_PATH

exec /opt/nonet-movie/nonet-movie "$@"
EOF
chmod 0755 "$PKG_ROOT/usr/bin/$APP_NAME"

cat > "$PKG_ROOT/etc/nonet-movie.env" <<'EOF'
# System-wide defaults for nonet-movie.
# Defaults can be overridden per user in:
#   ~/.config/nonet-movie/env
JSON_DB_PATH=~/.local/share/nonet-movie/storage/
LOG_PATH=~/.local/share/nonet-movie/logs
EOF

cat > "$PKG_ROOT/DEBIAN/conffiles" <<'EOF'
/etc/nonet-movie.env
EOF

cat > "$PKG_ROOT/DEBIAN/control" <<EOF
Package: $PKG_NAME
Version: $VERSION
Section: $SECTION
Priority: $PRIORITY
Architecture: $ARCH
Maintainer: $MAINTAINER
Description: Nonet Movie CLI application (bundled executable)
EOF

mkdir -p "$DIST_DIR"
OUTPUT_DEB="$DIST_DIR/${PKG_NAME}_${VERSION}.deb"
rm -f "$OUTPUT_DEB"
dpkg-deb --build "$PKG_ROOT" "$OUTPUT_DEB"

echo "Created: $OUTPUT_DEB"
