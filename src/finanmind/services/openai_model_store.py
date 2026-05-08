"""Resolves the OpenAI model id from env var, user-data file, or default."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.services.openai_api_settings import OpenAiApiSettings


class OpenAiModelStore:
    """Lookup order: OPENAI_MODEL env var, then file, then built-in default."""

    ENV_VAR = "OPENAI_MODEL"
    FILENAME = "openai_model.txt"

    @classmethod
    def resolve_model(cls) -> str:
        """Return the active model id (never empty)."""
        env_value = os.environ.get(cls.ENV_VAR, "").strip()
        if env_value:
            return env_value
        persisted = cls._read_persisted_model()
        if persisted:
            return persisted
        return OpenAiApiSettings.DEFAULT_MODEL_ID

    @classmethod
    def persist_model(cls, raw_model: str) -> None:
        """Save the chosen model id alongside other workspace files."""
        path = cls._model_path_or_raise()
        cleaned = raw_model.strip()
        if not cleaned:
            cls._delete_if_present(path)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cleaned, encoding="utf-8")

    @classmethod
    def env_var_in_use(cls) -> bool:
        """True when the env var supplies the value (so saving is skipped)."""
        return os.environ.get(cls.ENV_VAR, "").strip() != ""

    @classmethod
    def _read_persisted_model(cls) -> str | None:
        try:
            path = cls._model_path_or_raise()
        except RuntimeError:
            return None
        if not path.is_file():
            return None
        token = path.read_text(encoding="utf-8").strip()
        return token or None

    @classmethod
    def _delete_if_present(cls, path: Path) -> None:
        if path.is_file():
            path.unlink()

    @classmethod
    def _model_path_or_raise(cls) -> Path:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace folder not configured yet.")
        return Path(root) / cls.FILENAME
