import os
import shutil
import subprocess
import sys
from pathlib import Path

from pydm import ServiceContainer

from nonet_movie.infrastructure.boot import boot
from nonet_movie.infrastructure.console.app import ConsoleApplication


def _ensure_windows_desktop_shortcut() -> None:
    if os.name != "nt":
        return

    # Only create a launcher for packaged executable builds.
    if not getattr(sys, "frozen", False):
        return

    desktop_dir = Path.home() / "Desktop"
    shortcut_path = desktop_dir / "Nonet Movie.lnk"
    if shortcut_path.exists():
        return

    executable_path = Path(sys.executable).resolve()
    if not executable_path.exists():
        return

    powershell_bin = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell_bin:
        return

    def _ps_quote(text: str) -> str:
        return "'" + text.replace("'", "''") + "'"

    quoted_shortcut = _ps_quote(str(shortcut_path))
    quoted_target = _ps_quote(str(executable_path))
    shortcut_script = (
        "$wsh = New-Object -ComObject WScript.Shell;"
        f"$shortcut = $wsh.CreateShortcut({quoted_shortcut});"
        f"$shortcut.TargetPath = {quoted_target};"
        f"$shortcut.WorkingDirectory = [System.IO.Path]::GetDirectoryName({quoted_target});"
        f"$shortcut.IconLocation = {quoted_target} + ',0';"
        "$shortcut.Save();"
    )

    subprocess.run(
        [
            powershell_bin,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            shortcut_script,
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    _ensure_windows_desktop_shortcut()
    boot()
    ServiceContainer.get_instance().get_service(ConsoleApplication).run()


if __name__ == "__main__":
    main()
