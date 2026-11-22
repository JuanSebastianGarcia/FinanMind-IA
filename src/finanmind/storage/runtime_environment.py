"""Decides whether this process runs as development (CSV) or production (Cloudflare D1)."""

from __future__ import annotations

import os
import sys


class RuntimeEnvironment:
    """Development = ``python main.py`` from source; production = the PyInstaller .exe.

    ``FINANMIND_ENV=production|development`` overrides the detection, e.g. to try the
    D1 backend from source without building the executable.
    """

    ENV_VAR = "FINANMIND_ENV"
    PRODUCTION = "production"
    DEVELOPMENT = "development"

    @classmethod
    def name(cls) -> str:
        """Return ``"production"`` or ``"development"``."""
        override = os.environ.get(cls.ENV_VAR, "").strip().lower()
        if override in (cls.PRODUCTION, cls.DEVELOPMENT):
            return override
        return cls.PRODUCTION if getattr(sys, "frozen", False) else cls.DEVELOPMENT

    @classmethod
    def is_production(cls) -> bool:
        return cls.name() == cls.PRODUCTION

    @classmethod
    def uses_cloud_storage(cls) -> bool:
        """True when domain data (budget, cards, ...) lives in Cloudflare D1 instead of CSV."""
        return cls.is_production()
