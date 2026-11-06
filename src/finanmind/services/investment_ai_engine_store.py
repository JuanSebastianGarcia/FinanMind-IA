"""Persists which engine (API key vs Claude Code CLI) runs investment reviews."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.services.investment_ai_engine import InvestmentAiEngine


class InvestmentAiEngineStore:
    """Lookup order: FINANMIND_INVESTMENT_AI_ENGINE env, then text file, then API."""

    ENV_VAR = "FINANMIND_INVESTMENT_AI_ENGINE"
    FILENAME = "investment_ai_engine.txt"

    @classmethod
    def resolve(cls) -> InvestmentAiEngine:
        env = os.environ.get(cls.ENV_VAR, "").strip()
        if env:
            return InvestmentAiEngine.parse(env)
        persisted = cls._read_file()
        if persisted:
            return InvestmentAiEngine.parse(persisted)
        return InvestmentAiEngine.API

    @classmethod
    def persist(cls, engine: InvestmentAiEngine) -> None:
        path = cls._path_or_raise()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(engine.value, encoding="utf-8")

    @classmethod
    def env_var_in_use(cls) -> bool:
        return os.environ.get(cls.ENV_VAR, "").strip() != ""

    @classmethod
    def _read_file(cls) -> str | None:
        try:
            path = cls._path_or_raise()
        except RuntimeError:
            return None
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8").strip()

    @classmethod
    def _path_or_raise(cls) -> Path:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace folder not configured yet.")
        return Path(root) / cls.FILENAME
