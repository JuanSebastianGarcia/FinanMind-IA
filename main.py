"""Run Finanmind from the repository root without an editable install."""

from __future__ import annotations

import sys
from pathlib import Path


class ProjectRootLauncher:
    """Prepends ``src`` on ``sys.path`` and delegates to ``Application.run``."""

    @classmethod
    def run(cls) -> None:
        repo_root = Path(__file__).resolve().parent
        src_dir = repo_root / "src"
        sys.path.insert(0, str(src_dir))
        from finanmind.main import Application

        Application.run()


if __name__ == "__main__":
    ProjectRootLauncher.run()
