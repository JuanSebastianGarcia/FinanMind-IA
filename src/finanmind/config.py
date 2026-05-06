"""Application-wide runtime configuration values."""

from pathlib import Path


class AppConfig:
    """Mutable shell configuration shared across services during a session."""

    USER_DATA_ROOT: Path | None = None
