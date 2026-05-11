"""Resolves the USD→COP exchange rate used to unify the investments view."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.config import AppConfig


class UsdCopRateStore:
    """Lookup order: USD_COP_RATE env var, then file, then built-in default."""

    ENV_VAR = "USD_COP_RATE"
    FILENAME = "usd_cop_rate.txt"
    DEFAULT_RATE = 4000.0

    @classmethod
    def resolve_rate(cls) -> float:
        """Return the active rate; never returns a non-positive value."""
        env_value = cls._parse_positive(os.environ.get(cls.ENV_VAR, ""))
        if env_value is not None:
            return env_value
        persisted = cls._read_persisted_rate()
        if persisted is not None:
            return persisted
        return cls.DEFAULT_RATE

    @classmethod
    def persist_rate(cls, raw_rate: float) -> None:
        """Save the chosen rate alongside other workspace files."""
        if raw_rate <= 0:
            raise ValueError("La tasa USD→COP debe ser mayor que cero.")
        path = cls._rate_path_or_raise()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{raw_rate:.4f}", encoding="utf-8")

    @classmethod
    def env_var_in_use(cls) -> bool:
        """True when the env var supplies a valid value (so saving is skipped)."""
        return cls._parse_positive(os.environ.get(cls.ENV_VAR, "")) is not None

    @classmethod
    def _read_persisted_rate(cls) -> float | None:
        try:
            path = cls._rate_path_or_raise()
        except RuntimeError:
            return None
        if not path.is_file():
            return None
        return cls._parse_positive(path.read_text(encoding="utf-8"))

    @classmethod
    def _parse_positive(cls, raw: str) -> float | None:
        token = raw.strip().replace(",", ".")
        if token == "":
            return None
        try:
            value = float(token)
        except ValueError:
            return None
        return value if value > 0 else None

    @classmethod
    def _rate_path_or_raise(cls) -> Path:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace folder not configured yet.")
        return Path(root) / cls.FILENAME
