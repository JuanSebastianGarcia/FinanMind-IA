"""Turns one parsed NU statement row into the data needed to register it in the app."""

from __future__ import annotations

import calendar
import re
from datetime import date

_INSTALLMENTS_PATTERN = re.compile(r"^\s*(\d+)\s*de\s*(\d+)\s*$", re.IGNORECASE)
_MONEY_CLEAN_PATTERN = re.compile(r"[^\d,.\-]")


class NuExpenseRowInterpreter:
    """Parses the raw text fields of a :class:`NuStatementPdfParser` row."""

    @classmethod
    def parse_money(cls, text: str) -> float:
        """Parse a Colombian-formatted amount like ``"$1.546.044,99"`` into a float."""
        cleaned = _MONEY_CLEAN_PATTERN.sub("", text or "")
        cleaned = cleaned.replace(".", "").replace(",", ".")
        if not cleaned or cleaned in ("-", "."):
            return 0.0
        return float(cleaned)

    @classmethod
    def parse_installments(cls, text: str) -> tuple[int, int] | None:
        """Parse ``"3 de 12"`` into ``(current_installment, total_installments)``."""
        match = _INSTALLMENTS_PATTERN.match(text or "")
        if not match:
            return None
        return int(match.group(1)), int(match.group(2))

    @classmethod
    def is_expense_row(cls, row: dict) -> bool:
        """False for non-purchase rows (e.g. "Gracias por tu pago") that carry no installments."""
        return cls.parse_installments(row.get("installments", "")) is not None

    @classmethod
    def origin_date(cls, occurred_on: str, current_installment: int) -> str:
        """Shift ``occurred_on`` back by ``current_installment - 1`` months.

        A statement only shows the installment being billed *this* month; the actual
        purchase (installment 1) happened that many months earlier, on the same day
        of the month (clamped to the shorter month when needed, e.g. no Feb 30).
        """
        year, month, day = (int(part) for part in occurred_on.split("-"))
        total_months = (year * 12 + (month - 1)) - (current_installment - 1)
        origin_year, origin_month = divmod(total_months, 12)
        origin_month += 1
        last_day = calendar.monthrange(origin_year, origin_month)[1]
        origin_day = min(day, last_day)
        return date(origin_year, origin_month, origin_day).isoformat()

    @classmethod
    def normalize_description(cls, description: str) -> str:
        return " ".join((description or "").strip().lower().split())
