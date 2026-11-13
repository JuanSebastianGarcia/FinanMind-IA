"""CSV codec for recurring payment definitions and their monthly status rows."""

from __future__ import annotations

import csv
import io

from finanmind.models.recurring_payment import RecurringPayment
from finanmind.models.recurring_payment_month import RecurringPaymentMonth


class RecurringPaymentCsvCodec:
    """Single-table CSV mixing ``payment`` definition rows and ``month`` status rows."""

    HEADER = [
        "record_type",
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
        "month",
        "paid_on",
    ]
    ROW_PAYMENT = "payment"
    ROW_MONTH = "month"

    @classmethod
    def to_csv_text(
        cls,
        payments: list[RecurringPayment],
        months: list[RecurringPaymentMonth],
    ) -> str:
        """Serialize definitions first, then month rows."""
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(cls.HEADER)
        for pay in sorted(payments, key=lambda p: (p.due_day, p.name.lower(), p.payment_id)):
            writer.writerow(cls._payment_row(pay))
        for rec in sorted(months, key=lambda m: (m.month, m.payment_id)):
            writer.writerow(cls._month_row(rec))
        return buffer.getvalue()

    @classmethod
    def _payment_row(cls, pay: RecurringPayment) -> list[str]:
        return [
            cls.ROW_PAYMENT,
            pay.payment_id,
            pay.name,
            pay.value_kind,
            cls._amount_cell(pay.amount_cop),
            str(pay.frequency_months),
            str(pay.due_day),
            pay.start_month,
            pay.label_id,
            "1" if pay.calendar_enabled else "0",
            ";".join(str(d) for d in pay.reminder_days),
            pay.reminder_time,
            pay.google_event_id,
            "",
            "",
        ]

    @classmethod
    def _month_row(cls, rec: RecurringPaymentMonth) -> list[str]:
        row = [""] * len(cls.HEADER)
        row[0] = cls.ROW_MONTH
        row[1] = rec.payment_id
        row[4] = cls._amount_cell(rec.amount_cop)
        row[13] = rec.month
        row[14] = rec.paid_on
        return row

    @classmethod
    def from_csv_text(
        cls,
        text: str,
    ) -> tuple[list[RecurringPayment], list[RecurringPaymentMonth]]:
        """Parse CSV text into definitions and month rows."""
        rows = list(csv.reader(io.StringIO(text)))
        if rows and rows[0] == cls.HEADER:
            rows = rows[1:]
        payments: list[RecurringPayment] = []
        months: list[RecurringPaymentMonth] = []
        for row in rows:
            kind = cls._cell(row, 0)
            if kind == cls.ROW_PAYMENT:
                payments.append(cls._payment_from_row(row))
            elif kind == cls.ROW_MONTH:
                months.append(cls._month_from_row(row))
        return payments, months

    @classmethod
    def _payment_from_row(cls, row: list[str]) -> RecurringPayment:
        kind = cls._cell(row, 3)
        if kind not in (RecurringPayment.KIND_FIXED, RecurringPayment.KIND_VARIABLE):
            kind = RecurringPayment.KIND_FIXED
        return RecurringPayment(
            payment_id=cls._cell(row, 1),
            name=cls._cell(row, 2),
            value_kind=kind,
            amount_cop=cls._parse_amount(cls._cell(row, 4)),
            frequency_months=cls._parse_int(cls._cell(row, 5), 1),
            due_day=cls._parse_int(cls._cell(row, 6), 1),
            start_month=cls._cell(row, 7),
            label_id=cls._cell(row, 8),
            calendar_enabled=cls._cell(row, 9) == "1",
            reminder_days=cls._parse_days(cls._cell(row, 10)),
            reminder_time=cls._cell(row, 11) or "08:00",
            google_event_id=cls._cell(row, 12),
        )

    @classmethod
    def _month_from_row(cls, row: list[str]) -> RecurringPaymentMonth:
        return RecurringPaymentMonth(
            payment_id=cls._cell(row, 1),
            month=cls._cell(row, 13),
            paid_on=cls._cell(row, 14),
            amount_cop=cls._parse_amount(cls._cell(row, 4)),
        )

    @classmethod
    def _amount_cell(cls, amount: float | None) -> str:
        if amount is None:
            return ""
        return str(int(round(amount)))

    @classmethod
    def _parse_amount(cls, raw: str) -> float | None:
        if raw == "":
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    @classmethod
    def _parse_int(cls, raw: str, default: int) -> int:
        try:
            return int(raw)
        except ValueError:
            return default

    @classmethod
    def _parse_days(cls, raw: str) -> list[int]:
        out: list[int] = []
        for token in raw.split(";"):
            token = token.strip()
            if token.isdigit():
                out.append(int(token))
        return out

    @classmethod
    def _cell(cls, row: list[str], idx: int) -> str:
        if idx >= len(row):
            return ""
        return row[idx].strip()
