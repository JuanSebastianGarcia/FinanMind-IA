"""Resolves the Mistral API key from env or workspace file."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.config import AppConfig


class MistralApiKeyStore:
    """Mirrors OpenAI key persistence for Mistral-compatible calls."""

    ENV_VAR = "MISTRAL_API_KEY"
    FILENAME = "mistral_api_key.txt"

    @classmethod
    def resolve_key(cls) -> str | None:
        env_value = os.environ.get(cls.ENV_VAR, "").strip()
        if env_value:
            return env_value
        return cls._read_persisted_key()

    @classmethod
    def persist_key(cls, raw_key: str) -> None:
        path = cls._key_path_or_raise()
        cleaned = raw_key.strip()
        if not cleaned:
            raise ValueError("La API key de Mistral no puede estar vacía.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cleaned, encoding="utf-8")

    @classmethod
    def env_var_in_use(cls) -> bool:
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
