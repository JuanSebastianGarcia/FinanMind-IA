"""Recurring bill (rent, utilities, insurance) scheduled on a fixed day."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RecurringPayment:
    """Bill definition: when it repeats, its usual value and how to be reminded.

    ``amount_cop`` is the fixed value, or the optional estimate for variable bills
    (``None`` when no estimate was given). ``start_month`` (``yyyy-mm``) anchors the
    cycle for bills repeating every ``frequency_months`` months.
    """

    payment_id: str
    name: str
    value_kind: str
    amount_cop: float | None
    frequency_months: int
    due_day: int
    start_month: str
    label_id: str
    calendar_enabled: bool
    reminder_days: list[int] = field(default_factory=list)
    reminder_time: str = "08:00"
    google_event_id: str = ""

    KIND_FIXED = "fixed"
    KIND_VARIABLE = "variable"

    @property
    def is_variable(self) -> bool:
        """True when the bill value changes every period."""
        return self.value_kind == self.KIND_VARIABLE
