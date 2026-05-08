"""Which external LLM vendor powers budget review."""

from __future__ import annotations

from enum import Enum


class BudgetAiProvider(str, Enum):
    """Concrete providers Finanmind can route budget reviews to."""

    OPENAI = "openai"
    MISTRAL = "mistral"

    @classmethod
    def parse(cls, raw: str) -> BudgetAiProvider:
        """Interpret persisted or env strings; defaults to OPENAI."""
        token = (raw or "").strip().lower()
        for member in cls:
            if member.value == token:
                return member
        return cls.OPENAI
