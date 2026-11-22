"""Recurring payments persisted in Cloudflare D1 (production backend of ``RecurringPaymentRepository``)."""

from __future__ import annotations

import json
from typing import Any

from finanmind.models.recurring_payment import RecurringPayment
from finanmind.models.recurring_payment_month import RecurringPaymentMonth
from finanmind.storage.d1_client import D1Client
from finanmind.storage.d1_table_sync import D1Table, D1TableSync, Row


class RecurringPaymentD1Repository:
    """Same contract as ``RecurringPaymentRepository`` (``load_all`` / ``save_all``).

    ``label_id`` is a soft reference to ``budget_labels`` (NULL when the label is
    gone, read back as ``""``). ``reminder_days`` is stored as a JSON array text and
    month rows are keyed by ``(payment_id, month)``.
    """

    PAYMENTS = D1Table(
        "recurring_payments",
        ("payment_id",),
        (
            "payment_id",
            "name",
            "value_kind",
            "amount_cop",
            "frequency_months",
            "due_day",
            "start_month",
            "label_id",
            "calendar_enabled",
            "reminder_days",
            "reminder_time",
            "google_event_id",
        ),
        soft_refs={"label_id": "budget_labels.label_id"},
        order_by="due_day, lower(name), payment_id",
    )
    MONTHS = D1Table(
        "recurring_payment_months",
        ("payment_id", "month"),
        ("payment_id", "month", "paid_on", "amount_cop"),
        order_by="month, payment_id",
    )

    def __init__(self, client: D1Client) -> None:
        self._client = client
        self._payments = D1TableSync(self.PAYMENTS)
        self._months = D1TableSync(self.MONTHS)

    def load_all(self) -> tuple[list[RecurringPayment], list[RecurringPaymentMonth]]:
        """Return definitions and month rows in the order the CSV codec writes them."""
        payment_rows, month_rows = D1TableSync.read(self._client, [self._payments, self._months])
        payments = [self._payment_from_row(r) for r in payment_rows]
        months = [
            RecurringPaymentMonth(
                payment_id=r["payment_id"],
                month=r["month"],
                paid_on=r["paid_on"] or "",
                amount_cop=_optional_float(r["amount_cop"]),
            )
            for r in month_rows
        ]
        return payments, months

    def save_all(self, payments: list[RecurringPayment], months: list[RecurringPaymentMonth]) -> None:
        """Make both tables equal the given lists in one atomic batch."""
        payment_rows: list[Row] = [self._payment_row(p) for p in payments]
        month_rows: list[Row] = [
            {
                "payment_id": m.payment_id,
                "month": m.month,
                "paid_on": m.paid_on,
                "amount_cop": _optional_cop(m.amount_cop),
            }
            for m in months
        ]
        D1TableSync.write(self._client, [(self._payments, payment_rows), (self._months, month_rows)])

    @staticmethod
    def _payment_row(pay: RecurringPayment) -> Row:
        return {
            "payment_id": pay.payment_id,
            "name": pay.name,
            "value_kind": pay.value_kind,
            "amount_cop": _optional_cop(pay.amount_cop),
            "frequency_months": int(pay.frequency_months),
            "due_day": int(pay.due_day),
            "start_month": pay.start_month,
            "label_id": pay.label_id or None,
            "calendar_enabled": 1 if pay.calendar_enabled else 0,
            "reminder_days": json.dumps([int(d) for d in pay.reminder_days], separators=(",", ":")),
            "reminder_time": pay.reminder_time,
            "google_event_id": pay.google_event_id,
        }

    @staticmethod
    def _payment_from_row(r: Row) -> RecurringPayment:
        kind = r["value_kind"]
        if kind not in (RecurringPayment.KIND_FIXED, RecurringPayment.KIND_VARIABLE):
            kind = RecurringPayment.KIND_FIXED
        return RecurringPayment(
            payment_id=r["payment_id"],
            name=r["name"],
            value_kind=kind,
            amount_cop=_optional_float(r["amount_cop"]),
            frequency_months=int(r["frequency_months"]),
            due_day=int(r["due_day"]),
            start_month=r["start_month"],
            label_id=r["label_id"] or "",
            calendar_enabled=bool(r["calendar_enabled"]),
            reminder_days=_parse_days(r["reminder_days"]),
            reminder_time=r["reminder_time"] or "08:00",
            google_event_id=r["google_event_id"] or "",
        )


def _optional_cop(amount: float | None) -> int | None:
    """Whole pesos like the CSV codec; ``None`` stays NULL."""
    return None if amount is None else int(round(amount))


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _parse_days(raw: Any) -> list[int]:
    """Decode the JSON array text, ignoring anything that is not a whole number."""
    try:
        values = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return []
    if not isinstance(values, list):
        return []
    return [int(v) for v in values if isinstance(v, int) and not isinstance(v, bool)]
