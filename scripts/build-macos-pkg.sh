#!/usr/bin/env bash
set -euo pipefail

APP_NAME="nonet-movie"
PKG_ID="${PKG_ID:-com.ariana.nonet-movie}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
WORK_DIR="$DIST_DIR/macos-pkg-work"

if ! command -v pkgbuild >/dev/null 2>&1; then
  echo "pkgbuild is required. Run this script on macOS with Xcode CLT installed."
  exit 1
fi

VERSION="${VERSION:-$(python3 - <<'PY'
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

PKG_STAGE="$WORK_DIR/${APP_NAME}-${VERSION}"
PAYLOAD_ROOT="$PKG_STAGE/payload"
INSTALL_ROOT="$PAYLOAD_ROOT/opt/$APP_NAME"
VENV_PATH="$INSTALL_ROOT/venv"
BIN_PATH="$PAYLOAD_ROOT/usr/local/bin/$APP_NAME"
ETC_ENV_PATH="$PAYLOAD_ROOT/etc/nonet-movie.env"
OUTPUT_PKG="$DIST_DIR/${APP_NAME}-${VERSION}.pkg"

echo "Building ${APP_NAME}-${VERSION}.pkg ..."
rm -rf "$PKG_STAGE"
mkdir -p "$INSTALL_ROOT" "$(dirname "$BIN_PATH")" "$(dirname "$ETC_ENV_PATH")" "$DIST_DIR"

python3 -m venv "$VENV_PATH"
"$VENV_PATH/bin/pip" install --upgrade pip setuptools wheel
"$VENV_PATH/bin/pip" install "$PROJECT_ROOT"

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

exec /opt/nonet-movie/venv/bin/python -c "
from pydm import ServiceContainer
from nonet_movie.infrastructure.boot import boot
from nonet_movie.infrastructure.console.app import ConsoleApplication

boot()
ServiceContainer.get_instance().get_service(ConsoleApplication).run()
" "$@"
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
