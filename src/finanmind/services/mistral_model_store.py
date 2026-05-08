"""Resolves Mistral model id from env, file, or built-in default."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.services.mistral_api_settings import MistralApiSettings


class MistralModelStore:
    """Lookup order: MISTRAL_MODEL env, then mistral_model.txt, then default."""

    ENV_VAR = "MISTRAL_MODEL"
    FILENAME = "mistral_model.txt"

    @classmethod
    def resolve_model(cls) -> str:
        env_value = os.environ.get(cls.ENV_VAR, "").strip()
        if env_value:
            return env_value
        persisted = cls._read_persisted_model()
        if persisted:
            return persisted
        return MistralApiSettings.DEFAULT_MODEL_ID

    @classmethod
    def persist_model(cls, raw_model: str) -> None:
        path = cls._model_path_or_raise()
        cleaned = raw_model.strip()
        if not cleaned:
            cls._delete_if_present(path)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cleaned, encoding="utf-8")

    @classmethod
    def env_var_in_use(cls) -> bool:
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
