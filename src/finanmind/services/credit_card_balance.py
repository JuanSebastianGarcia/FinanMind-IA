"""Balance and per-category aggregates for a credit card."""

from __future__ import annotations

from finanmind.models.credit_card_expense import CreditCardExpense
from finanmind.models.credit_card_payment import CreditCardPayment


class CreditCardBalance:
    """Pure math helpers; receives lists already filtered by card_id when needed."""

    @classmethod
    def total_charged(cls, expenses: list[CreditCardExpense]) -> float:
        """Sum every charge regardless of date."""
        return sum(e.amount_cop for e in expenses)

    @classmethod
    def total_paid(cls, payments: list[CreditCardPayment]) -> float:
        """Sum every payment regardless of date."""
        return sum(p.amount_cop for p in payments)

    @classmethod
    def outstanding(
        cls,
        expenses: list[CreditCardExpense],
        payments: list[CreditCardPayment],
    ) -> float:
        """Charges minus payments."""
        return cls.total_charged(expenses) - cls.total_paid(payments)

    @classmethod
    def available_credit(
        cls,
        limit_cop: float,
        expenses: list[CreditCardExpense],
        payments: list[CreditCardPayment],
    ) -> float:
        """Remaining usable credit; floored at zero so the UI never goes negative visually."""
        used = cls.outstanding(expenses, payments)
        return max(limit_cop - used, 0.0)

    @classmethod
    def usage_ratio(
        cls,
        limit_cop: float,
        expenses: list[CreditCardExpense],
        payments: list[CreditCardPayment],
    ) -> float:
        """Used credit as a fraction of the limit; clamped to [0, 1]."""
        if limit_cop <= 0:
            return 0.0
        used = cls.outstanding(expenses, payments)
        ratio = used / limit_cop
        return cls._clamp_unit(ratio)

    @classmethod
    def _clamp_unit(cls, value: float) -> float:
        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return value

    @classmethod
    def per_category_totals(
        cls,
        expenses: list[CreditCardExpense],
    ) -> dict[str, float]:
        """Map ``category_id -> sum`` for the supplied expenses."""
        totals: dict[str, float] = {}
        for ex in expenses:
            totals[ex.category_id] = totals.get(ex.category_id, 0.0) + ex.amount_cop
        return totals
