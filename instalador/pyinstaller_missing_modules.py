"""Reads PyInstaller's warn file to find modules the app imports but the bundle lacks."""

from __future__ import annotations

import re
from pathlib import Path


class PyInstallerMissingModules:
    """Parses the ``warn-<name>.txt`` list of modules PyInstaller could not find."""

    _LINE_PATTERN = re.compile(r"^missing module named (\S+) - imported by (.+)$")
    _IMPORTER_PATTERN = re.compile(r"([\w.]+) \(([^)]*)\)")

    def __init__(self, warn_file: Path) -> None:
        self._warn_file = warn_file

    def required_by(self, package: str) -> list[str]:
        """Return ``module (imported by importer)`` for non-optional imports made by ``package``."""
        if not self._warn_file.is_file():
            return []
        lines = self._warn_file.read_text(encoding="utf-8", errors="replace").splitlines()
        return [entry for line in lines for entry in self._entries_for_line(line, package)]

    def _entries_for_line(self, line: str, package: str) -> list[str]:
        match = self._LINE_PATTERN.match(line)
        if match is None:
            return []
        module = match.group(1).strip("'")
        return [
            f"{module} (imported by {importer})"
            for importer, kinds in self._IMPORTER_PATTERN.findall(match.group(2))
            if self._belongs_to(importer, package) and "optional" not in kinds
        ]

    @staticmethod
    def _belongs_to(importer: str, package: str) -> bool:
        return importer == package or importer.startswith(f"{package}.")
