"""Recurring bills: definitions, monthly paid marks and real bill values."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.models.recurring_payment import RecurringPayment
from finanmind.models.recurring_payment_month import RecurringPaymentMonth
from finanmind.repositories.recurring_payment_repository import RecurringPaymentRepository
from finanmind.services.recurring_payment_schedule import RecurringPaymentSchedule


@dataclass
class RecurringPaymentDraft:
    """Validated user input for creating or editing a bill."""

    name: str
    value_kind: str
    amount_cop: float | None
    frequency_months: int
    due_day: int
    start_month: str
    label_id: str
    calendar_enabled: bool
    reminder_days: list[int]
    reminder_time: str


@dataclass
class PaymentOccurrence:
    """One bill due in one month, with its resolved status."""

    payment: RecurringPayment
    month: str
    due_on: date
    paid_on: str
    amount_cop: float | None
    amount_is_estimate: bool

    @property
    def is_paid(self) -> bool:
        return self.paid_on != ""


class RecurringPaymentService:
    """CRUD for bills plus per-month status, persisted through the repository."""

    _ALLOWED_REMINDER_DAYS = (0, 1, 2, 3, 5, 7, 15)

    def __init__(self, repository: RecurringPaymentRepository) -> None:
        self._repository = repository
        self._payments: list[RecurringPayment] = []
        self._months: list[RecurringPaymentMonth] = []

    def load(self) -> None:
        """Reload everything from disk."""
        self._payments, self._months = self._repository.load_all()

    def persist(self) -> None:
        """Flush in-memory state."""
        self._repository.save_all(self._payments, self._months)

    def payments(self) -> list[RecurringPayment]:
        """All bill definitions ordered by due day."""
        return sorted(self._payments, key=lambda p: (p.due_day, p.name.lower()))

    def payment_by_id(self, payment_id: str) -> RecurringPayment:
        for pay in self._payments:
            if pay.payment_id == payment_id:
                return pay
        raise KeyError("Pago no encontrado")

    def add_payment(self, draft: RecurringPaymentDraft, workspace: BudgetWorkspace) -> RecurringPayment:
        """Create a new bill definition."""
        clean = self._validate(draft, workspace)
        pay = RecurringPayment(payment_id=str(uuid.uuid4()), **clean)
        self._payments.append(pay)
        self.persist()
        return pay

    def update_payment(
        self,
        payment_id: str,
        draft: RecurringPaymentDraft,
        workspace: BudgetWorkspace,
    ) -> RecurringPayment:
        """Edit a bill definition in place, keeping its monthly history."""
        pay = self.payment_by_id(payment_id)
        for key, value in self._validate(draft, workspace).items():
            setattr(pay, key, value)
        self.persist()
        return pay

    def delete_payment(self, payment_id: str) -> None:
        """Remove a bill and its monthly history."""
        self.payment_by_id(payment_id)
        self._payments = [p for p in self._payments if p.payment_id != payment_id]
        self._months = [m for m in self._months if m.payment_id != payment_id]
        self.persist()

    def set_google_event_id(self, payment_id: str, event_id: str) -> None:
        """Remember (or clear) the Google Calendar event mirroring this bill."""
        self.payment_by_id(payment_id).google_event_id = event_id
        self.persist()

    def set_paid(self, payment_id: str, month: str, paid: bool, today: date) -> None:
        """Mark or unmark a bill as paid for ``month``."""
        self._require_occurrence(payment_id, month)
        rec = self._month_record(payment_id, month, create=True)
        rec.paid_on = today.isoformat() if paid else ""
        self._drop_if_empty(rec)
        self.persist()

    def record_amount(
        self,
        payment_id: str,
        month: str,
        amount_cop: float | None,
        mark_paid: bool,
        today: date,
    ) -> None:
        """Store the real bill value for ``month`` (``None`` clears it)."""
        self._require_occurrence(payment_id, month)
        if amount_cop is not None and amount_cop <= 0:
            raise ValueError("El valor debe ser mayor que cero")
        rec = self._month_record(payment_id, month, create=True)
        rec.amount_cop = amount_cop
        if mark_paid:
            rec.paid_on = rec.paid_on or today.isoformat()
        self._drop_if_empty(rec)
        self.persist()

    def occurrences_in(self, month: str) -> list[PaymentOccurrence]:
        """Bills charged in ``month`` ordered by due date."""
        out = [self._occurrence(pay, month) for pay in self._payments if RecurringPaymentSchedule.occurs_in(pay, month)]
        return sorted(out, key=lambda o: (o.due_on, o.payment.name.lower()))

    def last_recorded_amount(self, payment_id: str, before_month: str) -> tuple[str, float] | None:
        """Most recent real value registered before ``before_month``."""
        hits = [
            m for m in self._months
            if m.payment_id == payment_id and m.amount_cop is not None and m.month < before_month
        ]
        if not hits:
            return None
        latest = max(hits, key=lambda m: m.month)
        return latest.month, float(latest.amount_cop)

    def _occurrence(self, pay: RecurringPayment, month: str) -> PaymentOccurrence:
        rec = self._month_record(pay.payment_id, month, create=False)
        real = rec.amount_cop if rec else None
        amount = real if real is not None else pay.amount_cop
        return PaymentOccurrence(
            payment=pay,
            month=month,
            due_on=RecurringPaymentSchedule.due_date(pay, month),
            paid_on=rec.paid_on if rec else "",
            amount_cop=amount,
            amount_is_estimate=pay.is_variable and real is None and amount is not None,
        )

    def _month_record(self, payment_id: str, month: str, create: bool) -> RecurringPaymentMonth | None:
        for rec in self._months:
            if rec.payment_id == payment_id and rec.month == month:
                return rec
        if not create:
            return None
        rec = RecurringPaymentMonth(payment_id=payment_id, month=month, paid_on="", amount_cop=None)
        self._months.append(rec)
        return rec

    def _drop_if_empty(self, rec: RecurringPaymentMonth) -> None:
        if rec.paid_on == "" and rec.amount_cop is None:
            self._months = [m for m in self._months if m is not rec]

    def _require_occurrence(self, payment_id: str, month: str) -> None:
        pay = self.payment_by_id(payment_id)
        if not RecurringPaymentSchedule.occurs_in(pay, month):
            raise ValueError("Este pago no se cobra en ese mes")

    def _validate(self, draft: RecurringPaymentDraft, workspace: BudgetWorkspace) -> dict:
        name = draft.name.strip()
        if name == "":
            raise ValueError("Escribe un nombre para el pago")
        kind = draft.value_kind
        if kind not in (RecurringPayment.KIND_FIXED, RecurringPayment.KIND_VARIABLE):
            raise ValueError("Tipo de valor inválido")
        amount = draft.amount_cop
        if amount is not None and amount <= 0:
            raise ValueError("El valor debe ser mayor que cero")
        if kind == RecurringPayment.KIND_FIXED and amount is None:
            raise ValueError("Un pago constante necesita su valor")
        if draft.frequency_months not in RecurringPaymentSchedule.ALLOWED_FREQUENCIES:
            raise ValueError("Frecuencia inválida")
        if not 1 <= draft.due_day <= 31:
            raise ValueError("El día de pago debe estar entre 1 y 31")
        RecurringPaymentSchedule.parse_month(draft.start_month)
        label_id = draft.label_id.strip()
        if label_id and not self._label_exists(workspace, label_id):
            raise ValueError("La etiqueta no existe en el presupuesto")
        days = sorted({d for d in draft.reminder_days if d in self._ALLOWED_REMINDER_DAYS}, reverse=True)
        return {
            "name": name,
            "value_kind": kind,
            "amount_cop": amount,
            "frequency_months": draft.frequency_months,
            "due_day": draft.due_day,
            "start_month": draft.start_month.strip(),
            "label_id": label_id,
            "calendar_enabled": bool(draft.calendar_enabled),
            "reminder_days": days,
            "reminder_time": self._clean_time(draft.reminder_time),
        }

    @classmethod
    def _label_exists(cls, workspace: BudgetWorkspace, label_id: str) -> bool:
        return any(lbl.label_id == label_id for cat in workspace.categories for lbl in cat.labels)

    @classmethod
    def _clean_time(cls, raw: str) -> str:
        token = (raw or "").strip()
        parts = token.split(":")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            hh, mm = int(parts[0]), int(parts[1])
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                return f"{hh:02d}:{mm:02d}"
        return "08:00"
