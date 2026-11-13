"""Builds the Monday-first month grid shown in the payments calendar."""

from __future__ import annotations

from datetime import date, timedelta

from finanmind.services.recurring_payment_schedule import RecurringPaymentSchedule


class PaymentsCalendarBuilder:
    """Returns 7-day weeks covering the month, with the month's bills on each day."""

    @classmethod
    def build(cls, month: str, rows: list[dict], today: date) -> list[list[dict]]:
        year, mon = RecurringPaymentSchedule.parse_month(month)
        first = date(year, mon, 1)
        start = first - timedelta(days=first.weekday())
        next_first = date(year + (mon == 12), mon % 12 + 1, 1)
        by_day: dict[int, list[dict]] = {}
        for row in rows:
            by_day.setdefault(row["day"], []).append(cls._chip(row))
        weeks: list[list[dict]] = []
        cursor = start
        while cursor < next_first or len(weeks) == 0:
            week = []
            for _ in range(7):
                in_month = cursor.month == mon and cursor.year == year
                week.append({
                    "iso": cursor.isoformat(),
                    "day": cursor.day,
                    "in_month": in_month,
                    "is_today": cursor == today,
                    "items": by_day.get(cursor.day, []) if in_month else [],
                })
                cursor += timedelta(days=1)
            weeks.append(week)
        return weeks

    @classmethod
    def _chip(cls, row: dict) -> dict:
        return {
            "payment_id": row["payment_id"],
            "name": row["name"],
            "status": row["status"],
            "color": row["color"],
        }
