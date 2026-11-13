"""Pure calendar arithmetic for recurring payments (no I/O)."""

from __future__ import annotations

import calendar
from datetime import date

from finanmind.models.recurring_payment import RecurringPayment


class RecurringPaymentSchedule:
    """Answers when a bill is due: which months it applies to and on which day."""

    ALLOWED_FREQUENCIES = (1, 2, 3, 6, 12)

    @classmethod
    def month_key(cls, day: date) -> str:
        """Return ``yyyy-mm`` for a date."""
        return day.strftime("%Y-%m")

    @classmethod
    def parse_month(cls, ym: str) -> tuple[int, int]:
        """Split ``yyyy-mm`` into ``(year, month)``; raises ``ValueError`` when malformed."""
        token = (ym or "").strip()
        if len(token) != 7 or token[4] != "-":
            raise ValueError("Usa el mes en formato AAAA-MM")
        year, month = int(token[:4]), int(token[5:7])
        if not 1 <= month <= 12:
            raise ValueError("Mes inválido")
        return year, month

    @classmethod
    def shift_month(cls, ym: str, delta: int) -> str:
        """Move ``yyyy-mm`` by ``delta`` months."""
        year, month = cls.parse_month(ym)
        index = year * 12 + (month - 1) + delta
        return f"{index // 12:04d}-{index % 12 + 1:02d}"

    @classmethod
    def months_between(cls, start: str, end: str) -> int:
        """Whole months from ``start`` to ``end`` (negative when ``end`` is earlier)."""
        sy, sm = cls.parse_month(start)
        ey, em = cls.parse_month(end)
        return (ey * 12 + em) - (sy * 12 + sm)

    @classmethod
    def occurs_in(cls, payment: RecurringPayment, ym: str) -> bool:
        """True when the bill is charged in month ``ym``."""
        try:
            gap = cls.months_between(payment.start_month, ym)
        except ValueError:
            return False
        freq = max(1, payment.frequency_months)
        return gap >= 0 and gap % freq == 0

    @classmethod
    def due_date(cls, payment: RecurringPayment, ym: str) -> date:
        """Due date inside ``ym``, clamping day 31 to the month's last day."""
        year, month = cls.parse_month(ym)
        last = calendar.monthrange(year, month)[1]
        return date(year, month, min(max(1, payment.due_day), last))

    @classmethod
    def charged_months(cls, payment: RecurringPayment, start: str, count: int) -> list[str]:
        """Months from ``start`` (inclusive, ``count`` months ahead) where the bill applies."""
        out = []
        for offset in range(count):
            ym = cls.shift_month(start, offset)
            if cls.occurs_in(payment, ym):
                out.append(ym)
        return out
