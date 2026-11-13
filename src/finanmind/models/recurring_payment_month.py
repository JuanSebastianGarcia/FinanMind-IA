"""Per-month status of a recurring payment (paid mark and actual bill value)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RecurringPaymentMonth:
    """What happened with one bill in one ``yyyy-mm`` period.

    ``paid_on`` is an ISO day when the bill was marked as paid, empty otherwise.
    ``amount_cop`` is the real bill value registered for that month, if any.
    """

    payment_id: str
    month: str
    paid_on: str
    amount_cop: float | None

    @property
    def is_paid(self) -> bool:
        """True when the bill was marked as paid for this month."""
        return self.paid_on != ""
