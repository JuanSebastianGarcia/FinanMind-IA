"""Serializes the investment review engine choice and Claude Code CLI state."""

from __future__ import annotations

from finanmind.services.claude_cli_locator import ClaudeCliLocator
from finanmind.services.claude_cli_model_store import ClaudeCliModelStore
from finanmind.services.investment_ai_engine_store import InvestmentAiEngineStore


class InvestmentReviewEngineBuilder:
    """Returns the active engine plus whether the CLI was found and its model."""

    @classmethod
    def build(cls) -> dict:
        """Return ``{engine, engine_env_locked, claude_cli: {...}}`` for the dialog."""
        return {
            "engine": InvestmentAiEngineStore.resolve().value,
            "engine_env_locked": InvestmentAiEngineStore.env_var_in_use(),
            "claude_cli": cls._claude_cli_block(),
        }

    @classmethod
    def _claude_cli_block(cls) -> dict:
        path = ClaudeCliLocator.locate()
        return {
            "detected": path is not None,
            "path": path or "",
            "model_id": ClaudeCliModelStore.resolve_model(),
            "model_env_locked": ClaudeCliModelStore.env_var_in_use(),
        }
