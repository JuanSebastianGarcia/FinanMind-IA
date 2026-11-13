"""Serializes one ``PaymentOccurrence`` into the dict used by the payments panel."""

from __future__ import annotations

from datetime import date

from finanmind.services.month_label_formatter import MonthLabelFormatter
from finanmind.services.recurring_payment_service import PaymentOccurrence, RecurringPaymentService


class PaymentsRowSerializer:
    """Builds table/calendar rows with status, label caption and reminder text."""

    NO_LABEL_COLOR = "#9ca3af"
    _FREQUENCY_LABELS = {1: "Mensual", 2: "Bimestral", 3: "Trimestral", 6: "Semestral", 12: "Anual"}

    @classmethod
    def serialize(
        cls,
        occ: PaymentOccurrence,
        labels: dict[str, dict],
        service: RecurringPaymentService,
        today: date,
    ) -> dict:
        pay = occ.payment
        label = labels.get(pay.label_id)
        return {
            "payment_id": pay.payment_id,
            "name": pay.name,
            "month": occ.month,
            "due_on": occ.due_on.isoformat(),
            "day": occ.due_on.day,
            "days_left": (occ.due_on - today).days,
            "status": cls.status(occ, today),
            "paid_on": occ.paid_on,
            "amount_cop": occ.amount_cop,
            "amount_is_estimate": occ.amount_is_estimate,
            "value_kind": pay.value_kind,
            "frequency_months": pay.frequency_months,
            "frequency_label": cls.frequency_label(pay.frequency_months),
            "label_id": pay.label_id if label else "",
            "label_caption": label["caption"] if label else "",
            "color": label["color"] if label and label["color"] else cls.NO_LABEL_COLOR,
            "reminder_caption": cls._reminder_caption(pay.calendar_enabled, pay.reminder_days, pay.reminder_time),
            "calendar_status": cls._calendar_status(pay.calendar_enabled, pay.reminder_days, pay.google_event_id),
            "definition": {
                "name": pay.name,
                "value_kind": pay.value_kind,
                "amount_cop": pay.amount_cop,
                "frequency_months": pay.frequency_months,
                "due_day": pay.due_day,
                "start_month": pay.start_month,
                "label_id": pay.label_id if label else "",
                "label_caption": label["caption"] if label else "",
                "calendar_enabled": pay.calendar_enabled,
                "reminder_days": list(pay.reminder_days),
                "reminder_time": pay.reminder_time,
            },
            "last_recorded": cls._last_recorded(service, pay.payment_id, occ.month),
        }

    @classmethod
    def status(cls, occ: PaymentOccurrence, today: date) -> str:
        if occ.is_paid:
            return "paid"
        return "late" if occ.due_on < today else "pending"

    @classmethod
    def frequency_label(cls, months: int) -> str:
        return cls._FREQUENCY_LABELS.get(months, f"Cada {months} meses")

    @classmethod
    def _reminder_caption(cls, enabled: bool, days: list[int], time_hhmm: str) -> str:
        if not enabled or not days:
            return "Sin aviso"
        text = " y ".join(cls._day_phrase(d) for d in sorted(days, reverse=True))
        return f"{text[:1].upper()}{text[1:]} · {time_hhmm}"

    @classmethod
    def _calendar_status(cls, enabled: bool, days: list[int], event_id: str) -> str:
        """``off`` (no reminder), ``synced`` (event exists) or ``pending`` (not in Google yet)."""
        if not enabled or not days:
            return "off"
        return "synced" if event_id else "pending"

    @classmethod
    def _day_phrase(cls, days: int) -> str:
        if days == 0:
            return "el mismo día"
        if days == 7:
            return "1 semana antes"
        return "1 día antes" if days == 1 else f"{days} días antes"

    @classmethod
    def _last_recorded(cls, service: RecurringPaymentService, payment_id: str, month: str) -> dict | None:
        hit = service.last_recorded_amount(payment_id, month)
        if hit is None:
            return None
        ym, amount = hit
        return {"month_title": MonthLabelFormatter.spanish_month_year(ym), "amount_cop": amount}
