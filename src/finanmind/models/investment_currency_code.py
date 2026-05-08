"""Supported currencies for stored investment amounts."""

from __future__ import annotations


class InvestmentCurrencyCode:
    """Normalizes user or CSV input to COP or USD."""

    COP = "COP"
    USD = "USD"

    @classmethod
    def normalize(cls, raw: str) -> str:
        """Return ``COP`` or ``USD``; raises ``ValueError`` when unknown."""
        token = raw.strip().upper()
        if token in (cls.COP, cls.USD):
            return token
        raise ValueError("Moneda inválida. Use COP o USD.")

    @classmethod
    def from_storage_cell(cls, raw: str) -> str:
        """Map legacy empty CSV cells to COP."""
        token = raw.strip().upper()
        if token == "":
            return cls.COP
        if token in (cls.COP, cls.USD):
            return token
        return cls.COP
