"""Serialises ``yyyy-mm`` keys into key/label dropdown options."""

from __future__ import annotations

from finanmind.services.month_label_formatter import MonthLabelFormatter


class DashboardMonthOptionsBuilder:
    """Pairs each month key with its Spanish caption for the picker."""

    @classmethod
    def build(cls, keys: list[str]) -> list[dict]:
        """Return one ``{key, label}`` dict per month, preserving order."""
        return [cls._option_for(key) for key in keys or []]

    @classmethod
    def _option_for(cls, key: str) -> dict:
        return {"key": key, "label": MonthLabelFormatter.spanish_month_year(key)}
