"""Builds the month list shown in the Distribución month dropdown."""

from __future__ import annotations

from datetime import date

from finanmind.services.monthly_distribution_service import MonthlyDistributionService


class DistributionMonthsResolver:
    """Resolves the visible months and picks the active one for the panel."""

    @classmethod
    def list_months(cls, ledger: MonthlyDistributionService) -> list[str]:
        """Return the union of known months plus the current month, newest first."""
        tokens = ledger.known_month_prefixes()
        current = cls.current_month_key()
        merged = list(dict.fromkeys(tokens))
        if current not in merged:
            merged.insert(0, current)
        return merged if merged else [current]

    @classmethod
    def current_month_key(cls) -> str:
        """Return today's date as ``YYYY-MM``."""
        return date.today().strftime("%Y-%m")

    @classmethod
    def coerce_active(cls, months: list[str], preferred: str) -> str:
        """Choose the preferred month when valid, otherwise fall back to the first."""
        token = (preferred or "").strip()
        if token in months:
            return token
        return months[0]
