"""Errors raised when a chat-completion HTTP call fails or returns junk."""

from __future__ import annotations


class LlmChatCompletionError(Exception):
    """Raised when the upstream LLM API fails after retries or returns unusable JSON."""

    def __init__(self, message: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.http_status = http_status

    @property
    def is_auth_error(self) -> bool:
        """True for 401/403 (invalid or forbidden key)."""
        return self.http_status in (401, 403)
