"""Mistral La Plateforme chat completion defaults."""

from __future__ import annotations


class MistralApiSettings:
    """Base URL plus a sensible default for the Experiment/free-style tier."""

    ENDPOINT_URL = "https://api.mistral.ai/v1/chat/completions"
    DEFAULT_MODEL_ID = "mistral-small-latest"
