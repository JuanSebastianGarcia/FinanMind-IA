"""Build a Windows .exe for Finanmind using PyInstaller (web UI included)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from python_interpreter_picker import PythonInterpreterPicker


class InstallerBuilder:
    """Packages Finanmind into a standalone build inside the instalador folder."""

    APP_NAME = "Finanmind"

    def __init__(self) -> None:
        self._instalador_dir = Path(__file__).resolve().parent
        self._project_root = self._instalador_dir.parent
        self._entry_script = self._project_root / "main.py"
        self._src_dir = self._project_root / "src"
        self._webui_dir = self._src_dir / "finanmind" / "webui"
        self._icon_file = self._webui_dir / "assets" / "icons" / "finanmind.ico"

    def build(self) -> Path:
        """Run PyInstaller and place the resulting bundle next to this script."""
        self._maybe_reexec_with_compatible_python()
        self._ensure_dependencies()
        self._ensure_webui_present()
        self._clean_previous_artifacts()
        self._run_pyinstaller()
        return self._publish_build()

    def _maybe_reexec_with_compatible_python(self) -> None:
        if PythonInterpreterPicker.is_current_compatible():
            return
        compatible = PythonInterpreterPicker.find_compatible_python()
        if compatible is None:
            return
        self._reexec_with(compatible)

    def _reexec_with(self, python_exe: Path) -> None:
        current = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(
            f"[installer] Current Python {current} is not supported by pywebview; "
            f"switching to: {python_exe}",
            flush=True,
        )
        result = subprocess.run([str(python_exe), str(Path(__file__).resolve())], check=False)
        sys.exit(result.returncode)

    def _ensure_dependencies(self) -> None:
        self._require_module("PyInstaller", self._install_hint())
        self._require_module("webview", self._pywebview_hint())

    def _pywebview_hint(self) -> str:
        major, minor = sys.version_info[:2]
        if (major, minor) >= (3, 14):
            return (
                f"Python {major}.{minor} is unsupported by pywebview "
                f"(pythonnet ships no wheels for it). "
                f"Install Python 3.11-3.13 and the 'py' launcher will be used automatically."
            )
        return self._install_hint()

    def _install_hint(self) -> str:
        requirements = self._project_root / "requirements.txt"
        return f'Run:  "{sys.executable}" -m pip install -r "{requirements}"'

    def _require_module(self, module_name: str, hint: str) -> None:
        try:
            __import__(module_name)
        except ImportError as exc:
            raise RuntimeError(f"Missing dependency '{module_name}'.\n  {hint}") from exc

    def _ensure_webui_present(self) -> None:
        index_html = self._webui_dir / "index.html"
        if not index_html.is_file():
            raise RuntimeError(f"Web UI assets not found at: {index_html}")

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
            *self._base_flags(),
            *self._icon_flags(),
            *self._path_flags(),
            *self._data_flags(),
            *self._collection_flags(),
            str(self._entry_script),
        ]

    def _base_flags(self) -> list[str]:
        return [
            "--noconfirm", "--clean",
            "--windowed",
            "--name", self.APP_NAME,
        ]

    def _icon_flags(self) -> list[str]:
        if not self._icon_file.is_file():
            return []
        return ["--icon", str(self._icon_file)]

    def _path_flags(self) -> list[str]:
        return ["--paths", str(self._src_dir)]

    def _data_flags(self) -> list[str]:
        spec = f"{self._webui_dir}{self._data_separator()}finanmind/webui"
        return ["--add-data", spec]

    def _collection_flags(self) -> list[str]:
        return [
            "--collect-all", "customtkinter",
            "--collect-all", "webview",
        ]

    def _data_separator(self) -> str:
        return ";" if sys.platform.startswith("win") else ":"

    def _publish_build(self) -> Path:
        built_dir = self._instalador_dir / "dist" / self.APP_NAME
        final_dir = self._instalador_dir / self.APP_NAME
        self._replace_directory(built_dir, final_dir)
        exe_path = final_dir / f"{self.APP_NAME}.exe"
        zip_path = self._create_distributable_zip(final_dir)
        self._print_success_message(exe_path, zip_path)
        return exe_path

    def _replace_directory(self, source: Path, destination: Path) -> None:
        if not source.exists():
            raise RuntimeError(f"PyInstaller did not produce: {source}")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(source), str(destination))

    def _create_distributable_zip(self, final_dir: Path) -> Path:
        archive_base = self._instalador_dir / self.APP_NAME
        zip_path = archive_base.with_suffix(".zip")
        if zip_path.exists():
            zip_path.unlink()
        shutil.make_archive(
            base_name=str(archive_base), format="zip",
            root_dir=str(self._instalador_dir), base_dir=final_dir.name,
        )
        return zip_path

    def _print_success_message(self, exe_path: Path, zip_path: Path) -> None:
        print("", flush=True)
        print(f"[installer] Build OK", flush=True)
        print(f"[installer]   Folder : {exe_path.parent}", flush=True)
        print(f"[installer]   Run    : {exe_path}", flush=True)
        print(f"[installer]   Share  : {zip_path}", flush=True)
        print("[installer] Tip: keep Finanmind.exe and _internal/ together.", flush=True)


if __name__ == "__main__":
    InstallerBuilder().build()
