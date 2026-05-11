"""Build a single-file Windows .exe for Finanmind using PyInstaller."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


class InstallerBuilder:
    """Packages Finanmind into a standalone .exe inside the instalador folder."""

    APP_NAME = "Finanmind"

    def __init__(self) -> None:
        self._instalador_dir = Path(__file__).resolve().parent
        self._project_root = self._instalador_dir.parent
        self._entry_script = self._project_root / "main.py"
        self._src_dir = self._project_root / "src"

    def build(self) -> Path:
        """Run PyInstaller and place the resulting .exe next to this script."""
        self._ensure_pyinstaller()
        self._clean_previous_artifacts()
        self._run_pyinstaller()
        return self._publish_exe()

    def _ensure_pyinstaller(self) -> None:
        try:
            import PyInstaller  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "PyInstaller is missing. Install it with: pip install pyinstaller"
            ) from exc

    def _clean_previous_artifacts(self) -> None:
        for folder_name in ("build", "dist"):
            folder = self._instalador_dir / folder_name
            if folder.exists():
                shutil.rmtree(folder)
        spec_file = self._instalador_dir / f"{self.APP_NAME}.spec"
        if spec_file.exists():
            spec_file.unlink()

    def _run_pyinstaller(self) -> None:
        subprocess.run(
            self._build_command(), check=True, cwd=self._instalador_dir
        )

    def _build_command(self) -> list[str]:
        return [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean",
            "--onefile", "--windowed",
            "--name", self.APP_NAME,
            "--paths", str(self._src_dir),
            "--collect-all", "customtkinter",
            str(self._entry_script),
        ]

    def _publish_exe(self) -> Path:
        built_exe = self._instalador_dir / "dist" / f"{self.APP_NAME}.exe"
        final_exe = self._instalador_dir / f"{self.APP_NAME}.exe"
        if final_exe.exists():
            final_exe.unlink()
        shutil.move(str(built_exe), str(final_exe))
        return final_exe


if __name__ == "__main__":
    InstallerBuilder().build()
