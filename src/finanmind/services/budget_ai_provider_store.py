"""Persists which LLM vendor the user prefers for budget reviews."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.services.budget_ai_provider import BudgetAiProvider


class BudgetAiProviderStore:
    """Lookup order: FINANMIND_AI_PROVIDER env, then text file, then OpenAI."""

    ENV_VAR = "FINANMIND_AI_PROVIDER"
    FILENAME = "budget_ai_provider.txt"

    @classmethod
    def resolve(cls) -> BudgetAiProvider:
        env = os.environ.get(cls.ENV_VAR, "").strip()
        if env:
            return BudgetAiProvider.parse(env)
        persisted = cls._read_file()
        if persisted:
            return BudgetAiProvider.parse(persisted)
        return BudgetAiProvider.OPENAI

    @classmethod
    def persist(cls, provider: BudgetAiProvider) -> None:
        path = cls._path_or_raise()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(provider.value, encoding="utf-8")

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
