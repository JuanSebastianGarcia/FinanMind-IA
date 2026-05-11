"""Locates the bundled HTML/CSS/JS front-end assets at runtime."""

from __future__ import annotations

import sys
from pathlib import Path


class FrontendAssetsLocator:
    """Resolves the absolute path to ``index.html`` in dev and frozen builds."""

    _PACKAGE_RELATIVE = Path("webui") / "index.html"

    @classmethod
    def find_index_path(cls) -> str:
        """Return the absolute path string of ``index.html`` for PyWebview."""
        path = cls._resolve_index_path()
        if not path.is_file():
            raise FileNotFoundError(f"Front-end entry not found: {path}")
        return str(path)

    @classmethod
    def _resolve_index_path(cls) -> Path:
        frozen = cls._frozen_index_path()
        if frozen is not None and frozen.is_file():
            return frozen
        return cls._package_index_path()

    @classmethod
    def _package_index_path(cls) -> Path:
        package_dir = Path(__file__).resolve().parent.parent.parent
        return package_dir / cls._PACKAGE_RELATIVE

    @classmethod
    def _frozen_index_path(cls) -> Path | None:
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir is None:
            return None
        return Path(bundle_dir) / "finanmind" / cls._PACKAGE_RELATIVE
