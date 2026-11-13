"""Turns the payment dialog's JS payload into a ``RecurringPaymentDraft``."""

from __future__ import annotations

from finanmind.services.recurring_payment_service import RecurringPaymentDraft


class PaymentsDraftParser:
    """Coerces loosely-typed JSON values coming from the browser."""

    @classmethod
    def parse(cls, data: dict) -> RecurringPaymentDraft:
        if not isinstance(data, dict):
            raise ValueError("Datos del pago inválidos")
        return RecurringPaymentDraft(
            name=str(data.get("name") or ""),
            value_kind=str(data.get("value_kind") or ""),
            amount_cop=cls._amount(data.get("amount_cop")),
            frequency_months=cls._int(data.get("frequency_months"), "Frecuencia inválida"),
            due_day=cls._int(data.get("due_day"), "Día de pago inválido"),
            start_month=str(data.get("start_month") or ""),
            label_id=str(data.get("label_id") or ""),
            calendar_enabled=bool(data.get("calendar_enabled")),
            reminder_days=[cls._int(d, "Aviso inválido") for d in (data.get("reminder_days") or [])],
            reminder_time=str(data.get("reminder_time") or "08:00"),
        )

    @classmethod
    def amount(cls, raw) -> float | None:
        """Public helper for single-amount commands."""
        return cls._amount(raw)

    @classmethod
    def _amount(cls, raw) -> float | None:
        if raw is None or raw == "":
            return None
        try:
            return float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("Valor inválido") from exc

    @classmethod
    def _int(cls, raw, message: str) -> int:
        try:
            return int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(message) from exc
