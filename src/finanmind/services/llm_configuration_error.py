"""Raised when API keys or provider settings are missing for a review."""

from __future__ import annotations


class LlmConfigurationError(ValueError):
    """User-visible misconfiguration before any HTTP call."""
