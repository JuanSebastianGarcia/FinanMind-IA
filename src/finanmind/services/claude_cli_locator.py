"""Finds the Claude Code executable on this machine."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from finanmind.services.claude_cli_settings import ClaudeCliSettings


class ClaudeCliLocator:
    """Lookup order: FINANMIND_CLAUDE_CLI_PATH env, PATH, then usual install dirs.

    npm installs a ``claude.cmd`` shim; when the native ``claude.exe`` behind it
    exists we return that instead, so arguments never go through ``cmd.exe``.
    """

    @classmethod
    def locate(cls) -> str | None:
        """Return an absolute path to a runnable Claude Code binary, or None."""
        for candidate in cls._candidates():
            if candidate is not None and candidate.is_file():
                return str(cls._prefer_native(candidate))
        return None

    @classmethod
    def _candidates(cls) -> list[Path | None]:
        return [
            cls._from_env(),
            cls._from_path(),
            cls._from_appdata_npm(),
            Path.home() / ".local" / "bin" / "claude.exe",
        ]

    @classmethod
    def _from_env(cls) -> Path | None:
        raw = os.environ.get(ClaudeCliSettings.PATH_ENV_VAR, "").strip().strip('"')
        return Path(raw) if raw else None

    @classmethod
    def _from_path(cls) -> Path | None:
        found = shutil.which(ClaudeCliSettings.EXECUTABLE_NAME)
        return Path(found) if found else None

    @classmethod
    def _from_appdata_npm(cls) -> Path | None:
        appdata = os.environ.get("APPDATA", "").strip()
        return Path(appdata) / "npm" / "claude.cmd" if appdata else None

    @classmethod
    def _prefer_native(cls, path: Path) -> Path:
        if path.suffix.lower() not in (".cmd", ".bat", ""):
            return path
        native = path.parent.joinpath(*ClaudeCliSettings.NPM_NATIVE_BINARY)
        return native if native.is_file() else path
