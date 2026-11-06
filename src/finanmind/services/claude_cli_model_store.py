"""Resolves the optional model alias passed to the Claude Code CLI."""

from __future__ import annotations

import os
import re
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.services.claude_cli_settings import ClaudeCliSettings


class ClaudeCliModelStore:
    """Lookup order: CLAUDE_CLI_MODEL env, then claude_cli_model.txt, then ''.

    An empty value means "use whatever model Claude Code has as default".
    """

    ENV_VAR = "CLAUDE_CLI_MODEL"
    FILENAME = "claude_cli_model.txt"

    @classmethod
    def resolve_model(cls) -> str:
        env_value = os.environ.get(cls.ENV_VAR, "").strip()
        if env_value:
            return env_value
        return cls._read_persisted_model() or ""

    @classmethod
    def persist_model(cls, raw_model: str) -> None:
        cleaned = (raw_model or "").strip()
        cls.validate(cleaned)
        path = cls._model_path_or_raise()
        if not cleaned:
            cls._delete_if_present(path)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cleaned, encoding="utf-8")

    @classmethod
    def validate(cls, model: str) -> None:
        """Reject anything that is not a plain model alias or id."""
        if not re.match(ClaudeCliSettings.MODEL_PATTERN, model):
            raise ValueError(
                "El modelo solo puede contener letras, números, '.', '-', '_' o corchetes "
                "(ej. 'sonnet', 'opus')."
            )

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
