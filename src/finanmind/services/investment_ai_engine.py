"""Which execution engine powers the AI investment review."""

from __future__ import annotations

from enum import Enum


class InvestmentAiEngine(str, Enum):
    """HTTP API (OpenAI/Mistral via 'Configurar IA') or the local Claude Code CLI."""

    API = "api"
    CLAUDE_CLI = "claude_cli"

    @classmethod
    def parse(cls, raw: str) -> InvestmentAiEngine:
        """Interpret persisted, env or JS strings; defaults to API."""
        token = (raw or "").strip().lower()
        for member in cls:
            if member.value == token:
                return member
        return cls.API
