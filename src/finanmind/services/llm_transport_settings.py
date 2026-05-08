"""Shared HTTP limits for OpenAI-compatible chat completion calls."""

from __future__ import annotations


class LlmTransportSettings:
    """Timeout, retry policy, and sampling shared by OpenAI and Mistral."""

    REQUEST_TIMEOUT_SECONDS = 60.0
    MAX_RETRIES = 3
    RETRY_BACKOFF_SECONDS = 2.0
    TEMPERATURE = 0.4
