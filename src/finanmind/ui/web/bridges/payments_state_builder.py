"""Composes the full Calendario de pagos snapshot returned to the front-end."""

from __future__ import annotations

from datetime import date, timedelta

from finanmind.budget.book_service import BudgetBookService
from finanmind.services.month_label_formatter import MonthLabelFormatter
from finanmind.services.recurring_payment_schedule import RecurringPaymentSchedule
from finanmind.services.recurring_payment_service import RecurringPaymentService
from finanmind.ui.web.bridges.distribution_label_options_builder import DistributionLabelOptionsBuilder
from finanmind.ui.web.bridges.payments_calendar_builder import PaymentsCalendarBuilder
from finanmind.ui.web.bridges.payments_row_serializer import PaymentsRowSerializer
from finanmind.ui.web.bridges.payments_summary_builder import PaymentsSummaryBuilder


class PaymentsStateBuilder:
    """Month rows, calendar grid, upcoming list and KPIs in one dict."""

    UPCOMING_DAYS = 15

    @classmethod
    def build(
        cls,
        book: BudgetBookService,
        service: RecurringPaymentService,
        preferred_month: str,
        today: date,
    ) -> dict:
        current = RecurringPaymentSchedule.month_key(today)
        month = cls._coerce_month(preferred_month, current)
        labels = cls._label_index(book)
        rows = cls._rows(service, labels, month, today)
        upcoming = cls._upcoming(service, labels, today)
        return {
            "month": month,
            "month_title": MonthLabelFormatter.spanish_month_year(month),
            "current_month": current,
            "prev_month": RecurringPaymentSchedule.shift_month(month, -1),
            "next_month": RecurringPaymentSchedule.shift_month(month, 1),
            "today": today.isoformat(),
            "has_payments": len(service.payments()) > 0,
            "rows": rows,
            "weeks": PaymentsCalendarBuilder.build(month, rows, today),
            "upcoming": upcoming,
            "summary": PaymentsSummaryBuilder.build(rows, upcoming),
        }

    @classmethod
    def _coerce_month(cls, preferred: str, fallback: str) -> str:
        try:
            RecurringPaymentSchedule.parse_month(preferred)
            return preferred.strip()
        except (ValueError, TypeError):
            return fallback

    @classmethod
    def _label_index(cls, book: BudgetBookService) -> dict[str, dict]:
        return {opt["label_id"]: opt for opt in DistributionLabelOptionsBuilder.build(book.peek())}

    @classmethod
    def _rows(cls, service, labels, month: str, today: date) -> list[dict]:
        return [
            PaymentsRowSerializer.serialize(occ, labels, service, today)
            for occ in service.occurrences_in(month)
        ]

    @classmethod
    def _upcoming(cls, service, labels, today: date) -> list[dict]:
        """Unpaid bills of the current month already overdue, plus the next 15 days."""
        horizon = today + timedelta(days=cls.UPCOMING_DAYS)
        current = RecurringPaymentSchedule.month_key(today)
        months = [current, RecurringPaymentSchedule.shift_month(current, 1)]
        out = []
        for ym in months:
            for occ in service.occurrences_in(ym):
                if occ.is_paid or occ.due_on > horizon:
                    continue
                if occ.due_on < today and ym != current:
                    continue
                out.append(PaymentsRowSerializer.serialize(occ, labels, service, today))
        return sorted(out, key=lambda r: (r["due_on"], r["name"].lower()))
