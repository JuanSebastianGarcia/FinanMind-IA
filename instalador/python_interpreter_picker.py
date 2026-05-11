"""Locates a Python interpreter compatible with pywebview/pythonnet wheels."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class PythonInterpreterPicker:
    """Probes the Windows ``py`` launcher for the best available CPython."""

    PREFERRED_VERSIONS = ("3.13", "3.12", "3.11")

    @classmethod
    def is_current_compatible(cls) -> bool:
        """True when the running interpreter is one of the supported versions."""
        return cls._current_version_token() in cls.PREFERRED_VERSIONS

    @classmethod
    def find_compatible_python(cls) -> Path | None:
        """Return the path to a working compatible interpreter, newest first."""
        for version in cls.PREFERRED_VERSIONS:
            resolved = cls._resolve_via_launcher(version)
            if resolved is not None:
                return resolved
        return None

    @classmethod
    def _resolve_via_launcher(cls, version: str) -> Path | None:
        result = cls._run_launcher_probe(version)
        if result is None or result.returncode != 0:
            return None
        candidate = Path(result.stdout.strip())
        return candidate if candidate.is_file() else None

    @classmethod
    def _run_launcher_probe(cls, version: str) -> subprocess.CompletedProcess | None:
        try:
            return subprocess.run(
                ["py", f"-{version}", "-c", "import sys; print(sys.executable)"],
                capture_output=True, text=True, timeout=10, check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    @classmethod
    def _current_version_token(cls) -> str:
        major, minor = sys.version_info[:2]
        return f"{major}.{minor}"
