"""Resolves the OpenAI API key from env var or the workspace user-data folder."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.config import AppConfig


class OpenAiApiKeyStore:
    """Reads/writes the API key without ever placing it inside the repo."""

    ENV_VAR = "OPENAI_API_KEY"
    FILENAME = "openai_api_key.txt"

    @classmethod
    def resolve_key(cls) -> str | None:
        """Return env-var value when present, otherwise the persisted file."""
        env_value = os.environ.get(cls.ENV_VAR, "").strip()
        if env_value:
            return env_value
        return cls._read_persisted_key()

    @classmethod
    def persist_key(cls, raw_key: str) -> None:
        """Save the key in the user-data folder; raises when not configured."""
        path = cls._key_path_or_raise()
        cleaned = raw_key.strip()
        if not cleaned:
            raise ValueError("La API key no puede estar vacía.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cleaned, encoding="utf-8")

    @classmethod
    def clear_key(cls) -> None:
        """Remove the persisted key file when present."""
        try:
            path = cls._key_path_or_raise()
        except RuntimeError:
            return
        if path.is_file():
            path.unlink()

    @classmethod
    def env_var_in_use(cls) -> bool:
        """True when the env var supplies the key (so saving is skipped)."""
        return os.environ.get(cls.ENV_VAR, "").strip() != ""

    @classmethod
    def _read_persisted_key(cls) -> str | None:
        try:
            path = cls._key_path_or_raise()
        except RuntimeError:
            return None
        if not path.is_file():
            return None
        token = path.read_text(encoding="utf-8").strip()
        return token or None

    @classmethod
    def _key_path_or_raise(cls) -> Path:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace folder not configured yet.")
        return Path(root) / cls.FILENAME
