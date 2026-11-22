"""Default PyWebview window settings for the Finanmind shell."""

from __future__ import annotations

from dataclasses import dataclass

from finanmind.storage.runtime_environment import RuntimeEnvironment


@dataclass(frozen=True)
class WebWindowConfig:
    """Immutable settings consumed by ``WebApplication`` when creating the window."""

    title: str = "Finanmind"
    width: int = 1280
    height: int = 820
    min_width: int = 1000
    min_height: int = 620
    maximized: bool = True
    debug: bool = False

    @classmethod
    def default(cls) -> "WebWindowConfig":
        """Return the standard configuration; the title flags development runs."""
        if RuntimeEnvironment.is_production():
            return cls()
        return cls(title=f"{cls.title} (desarrollo)")
