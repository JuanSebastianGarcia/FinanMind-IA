"""Turns a recurring payment into a repeating Google Calendar event body (pure)."""

from __future__ import annotations

from datetime import datetime, timedelta

from finanmind.models.recurring_payment import RecurringPayment
from finanmind.services.recurring_payment_schedule import RecurringPaymentSchedule


class GoogleCalendarEventBuilder:
    """One recurring event per bill, at the reminder time on the due day.

    The event is timed (not all-day) so "el mismo día" can notify at the chosen
    hour: each reminder is ``days * 24h`` before the event start.
    """

    EVENT_MINUTES = 30
    MAX_REMINDER_MINUTES = 40320  # Google's limit: 4 weeks
    _FREQUENCY_LABELS = {1: "Mensual", 2: "Bimestral", 3: "Trimestral", 6: "Semestral", 12: "Anual"}

    @classmethod
    def build(cls, payment: RecurringPayment, label_caption: str, time_zone: str) -> dict:
        first_due = RecurringPaymentSchedule.due_date(payment, payment.start_month)
        hh, mm = (int(x) for x in payment.reminder_time.split(":"))
        start = datetime(first_due.year, first_due.month, first_due.day, hh, mm)
        end = start + timedelta(minutes=cls.EVENT_MINUTES)
        return {
            "summary": cls._summary(payment),
            "description": cls._description(payment, label_caption),
            "start": {"dateTime": start.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": time_zone},
            "end": {"dateTime": end.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": time_zone},
            "recurrence": [cls.rrule(payment)],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": min(d * 1440, cls.MAX_REMINDER_MINUTES)}
                    for d in sorted(set(payment.reminder_days))[:5]
                ],
            },
            "extendedProperties": {"private": {"finanmind_payment_id": payment.payment_id}},
        }

    @classmethod
    def rrule(cls, payment: RecurringPayment) -> str:
        """Monthly rule every N months; days 29-31 fall back to the month's last day."""
        day = max(1, min(31, payment.due_day))
        if day <= 28:
            by_day = f"BYMONTHDAY={day}"
        else:
            by_day = f"BYMONTHDAY={','.join(str(d) for d in range(28, day + 1))};BYSETPOS=-1"
        return f"RRULE:FREQ=MONTHLY;INTERVAL={max(1, payment.frequency_months)};{by_day}"

    @classmethod
    def _summary(cls, payment: RecurringPayment) -> str:
        if payment.is_variable:
            return f"💸 Pagar {payment.name} (valor variable)"
        return f"💸 Pagar {payment.name} · {cls._cop(payment.amount_cop)}"

    @classmethod
    def _description(cls, payment: RecurringPayment, label_caption: str) -> str:
        freq = cls._FREQUENCY_LABELS.get(payment.frequency_months, f"Cada {payment.frequency_months} meses")
        lines = [f"Frecuencia: {freq}"]
        if payment.is_variable:
            estimate = f"estimado {cls._cop(payment.amount_cop)}" if payment.amount_cop else "sin estimado"
            lines.append(f"Valor: variable ({estimate})")
        else:
            lines.append(f"Valor: {cls._cop(payment.amount_cop)}")
        if label_caption:
            lines.append(f"Presupuesto: {label_caption}")
        lines.append("")
        lines.append("Creado por Finanmind. Márcalo como pagado en la app (Calendario de pagos).")
        return "\n".join(lines)

    @classmethod
    def _cop(cls, amount: float | None) -> str:
        pesos = int(round(amount or 0))
        return "$ " + f"{pesos:,}".replace(",", ".")
