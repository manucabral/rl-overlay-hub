"""Build script for RL Overlay Hub."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.constants import APP_NAME, APP_VERSION

COMPANY_NAME = os.getenv("COMPANY_NAME", "RL Overlay Hub")
OUTPUT_DIR = "dist_build"
OUTPUT_FILENAME = "RLOverlayHub"
TARGET_FILE = "run.py"


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def build() -> None:
    project_root = _project_root()
    icon_path = project_root / "assets" / "logo.ico"

    if not icon_path.exists():
        raise FileNotFoundError(f"Icon not found: {icon_path}")

    nuitka_args = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--windows-console-mode=disable",
        f"--output-dir={OUTPUT_DIR}",
        f"--output-filename={OUTPUT_FILENAME}",
        f"--windows-icon-from-ico={icon_path}",
        f"--windows-product-name={APP_NAME}",
        "--windows-file-description=Rocket League Overlay Hub",
        f"--windows-company-name={COMPANY_NAME}",
        f"--windows-file-version={APP_VERSION}.0",
        f"--windows-product-version={APP_VERSION}.0",
        f"--include-data-dir={project_root / 'ui' / 'panel'}=ui/panel",
        f"--include-data-dir={project_root / 'public'}=public",
        f"--include-data-dir={project_root / 'assets'}=assets",
        "--disable-plugin=pywebview",
        "--include-module=webview.platforms.winforms",
        "--include-module=webview.platforms.win32",
        "--include-module=webview.platforms.edgechromium",
        "--include-module=webview.platforms.mshtml",
        "--nofollow-import-to=unittest",
        "--nofollow-import-to=unittest.mock",
        "--nofollow-import-to=doctest",
        "--nofollow-import-to=pytest",
        "--nofollow-import-to=test",
        "--nofollow-import-to=webview.platforms.cocoa",
        "--nofollow-import-to=webview.platforms.gtk",
        "--nofollow-import-to=webview.platforms.qt",
        "--nofollow-import-to=webview.platforms.android",
        "--nofollow-import-to=webview.platforms.linux",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=_tkinter",
        "--nofollow-import-to=PyQt5",
        "--nofollow-import-to=PyQt6",
        "--nofollow-import-to=PySide2",
        "--nofollow-import-to=PySide6",
        "--nofollow-import-to=nuitka",
        "--nofollow-import-to=gi",
        "--nofollow-import-to=pydoc",
        "--nofollow-import-to=distutils",
        "--nofollow-import-to=setuptools",
        "--remove-output",
        "--python-flag=no_docstrings",
        "--python-flag=no_asserts",
        "--msvc=latest",
        TARGET_FILE,
    ]

    print(f"Building {APP_NAME} v{APP_VERSION} with Nuitka...")
    print(" ".join(map(str, nuitka_args)))

    try:
        subprocess.run(nuitka_args, check=True, cwd=project_root)
    except subprocess.CalledProcessError as exc:
        print(f"Build failed with exit code {exc.returncode}")
        sys.exit(exc.returncode)

    print("Build completed successfully.")
    print(f"Output: {project_root / OUTPUT_DIR}")


if __name__ == "__main__":
    build()
