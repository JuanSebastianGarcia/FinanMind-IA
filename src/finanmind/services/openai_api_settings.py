"""OpenAI Chat Completions endpoint plus default snapshot model id."""

from __future__ import annotations


class OpenAiApiSettings:
    """Minimal OpenAI constants; timeouts live in ``LlmTransportSettings``."""

    ENDPOINT_URL = "https://api.openai.com/v1/chat/completions"
    DEFAULT_MODEL_ID = "gpt-5.4-mini"
