"""Resolves the cycle dropdown choices and the active range for one card."""

from __future__ import annotations

from datetime import date

from finanmind.models.credit_card import CreditCard
from finanmind.services.credit_card_billing_cycle import CreditCardBillingCycle
from finanmind.services.credit_card_service import CreditCardService


class CardsCyclesResolver:
    """Owns the cycle-key list (rolling + observed) plus active range coercion."""

    _SPAN_MONTHS = 6

    @classmethod
    def list_cycle_keys(cls, service: CreditCardService, card: CreditCard) -> list[str]:
        """Return ``yyyy-mm`` keys merging the rolling window with observed months."""
        anchor = date.today()
        rolling = CreditCardBillingCycle.cycle_keys_around(card.cut_day, anchor, span=cls._SPAN_MONTHS)
        observed = service.known_expense_months(card.card_id)
        merged = list(dict.fromkeys(rolling + observed))
        merged.sort(reverse=True)
        return merged or [cls.current_cycle_key()]

    @classmethod
    def current_cycle_key(cls) -> str:
        """Return today's ``yyyy-mm`` token."""
        today = date.today()
        return f"{today.year:04d}-{today.month:02d}"

    @classmethod
    def coerce_active(cls, cycle_keys: list[str], preferred: str) -> str:
        """Pick the preferred cycle when valid, otherwise the most recent one."""
        token = (preferred or "").strip()
        if token in cycle_keys:
            return token
        return cycle_keys[0]

    @classmethod
    def range_for(cls, card: CreditCard, cycle_key: str) -> tuple[str, str]:
        """Return ``(start_iso, end_iso)`` for ``cycle_key`` (yyyy-mm)."""
        year, month = cls._parse_year_month(cycle_key)
        return CreditCardBillingCycle.cycle_for_month(card.cut_day, year, month)

    @classmethod
    def _parse_year_month(cls, key: str) -> tuple[int, int]:
        try:
            year_str, month_str = (key or "").split("-")
            return int(year_str), int(month_str)
        except (ValueError, TypeError):
            today = date.today()
            return today.year, today.month
