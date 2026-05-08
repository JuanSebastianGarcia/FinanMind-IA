"""Billing cycle math: derive (start, end) ISO range for a card and target month."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta


class CreditCardBillingCycle:
    """Resolve cycle ranges for a credit card with a fixed cut day."""

    @classmethod
    def cycle_for_month(cls, cut_day: int, year: int, month: int) -> tuple[str, str]:
        """Return (start_iso, end_iso) for the cycle that closes within ``year-month``."""
        end = cls._clamp_to_month(year, month, cut_day)
        start = cls._previous_cycle_start(end, cut_day)
        return start.isoformat(), end.isoformat()

    @classmethod
    def _clamp_to_month(cls, year: int, month: int, day: int) -> date:
        last_day = monthrange(year, month)[1]
        chosen = min(max(day, 1), last_day)
        return date(year, month, chosen)

    @classmethod
    def _previous_cycle_start(cls, end: date, cut_day: int) -> date:
        prev_y, prev_m = cls._step_back_one_month(end.year, end.month)
        prev_end = cls._clamp_to_month(prev_y, prev_m, cut_day)
        return prev_end + timedelta(days=1)

    @classmethod
    def _step_back_one_month(cls, year: int, month: int) -> tuple[int, int]:
        if month == 1:
            return year - 1, 12
        return year, month - 1

    @classmethod
    def cycle_keys_around(cls, cut_day: int, anchor: date, span: int) -> list[str]:
        """Return ``yyyy-mm`` cycle labels covering ``span`` months back and forward."""
        out: list[str] = []
        for delta in range(-span, span + 1):
            y, m = cls._shift_months(anchor.year, anchor.month, delta)
            out.append(f"{y:04d}-{m:02d}")
        out.sort(reverse=True)
        return out

    @classmethod
    def _shift_months(cls, year: int, month: int, delta: int) -> tuple[int, int]:
        idx = (year * 12 + (month - 1)) + delta
        return idx // 12, (idx % 12) + 1

    @classmethod
    def is_inside(cls, day_iso: str, start_iso: str, end_iso: str) -> bool:
        """True when ``day_iso`` falls within the inclusive cycle range."""
        return start_iso <= day_iso <= end_iso
