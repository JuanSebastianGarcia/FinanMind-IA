"""Run Finanmind from the repository root without an editable install."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class ProjectRootLauncher:
    """Prepends ``src`` on ``sys.path`` and delegates to ``Application.run``.

    pywebview has no wheels for Python 3.14+, so when started with an unsupported
    interpreter the launcher re-runs itself with a compatible one (3.13/3.12/3.11)
    found through the Windows ``py`` launcher, like the installer builder does.
    """

    @classmethod
    def run(cls) -> None:
        repo_root = Path(__file__).resolve().parent
        cls._maybe_reexec_with_compatible_python(repo_root)
        sys.path.insert(0, str(repo_root / "src"))
        from finanmind.main import Application

        Application.run()

    @classmethod
    def _maybe_reexec_with_compatible_python(cls, repo_root: Path) -> None:
        if getattr(sys, "frozen", False):
            return
        sys.path.insert(0, str(repo_root / "instalador"))
        from python_interpreter_picker import PythonInterpreterPicker

        if PythonInterpreterPicker.is_current_compatible():
            return
        current = f"{sys.version_info.major}.{sys.version_info.minor}"
        compatible = PythonInterpreterPicker.find_compatible_python()
        if compatible is None:
            sys.exit(
                f"Finanmind necesita Python 3.11, 3.12 o 3.13 (pywebview no soporta Python {current}). "
                "Instala una de esas versiones y vuelve a ejecutar main.py.",
            )
        print(f"[finanmind] Python {current} no es compatible; usando {compatible}", flush=True)
        result = subprocess.run([str(compatible), str(Path(__file__).resolve()), *sys.argv[1:]], check=False)
        sys.exit(result.returncode)


if __name__ == "__main__":
    ProjectRootLauncher.run()
