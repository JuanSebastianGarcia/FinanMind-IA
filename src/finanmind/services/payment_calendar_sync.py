"""Keeps one Google Calendar recurring event per recurring payment."""

from __future__ import annotations

from dataclasses import dataclass

from finanmind.models.recurring_payment import RecurringPayment
from finanmind.services.external_sync_policy import ExternalSyncPolicy
from finanmind.services.google_calendar_auth import GoogleCalendarAuth, GoogleCalendarAuthError
from finanmind.services.google_calendar_client import GoogleCalendarApiError, GoogleCalendarClient
from finanmind.services.google_calendar_event_builder import GoogleCalendarEventBuilder
from finanmind.services.google_calendar_store import GoogleCalendarStore
from finanmind.services.recurring_payment_service import RecurringPaymentService


@dataclass
class CalendarSyncReport:
    """Outcome of a full synchronization."""

    synced: int = 0
    removed: int = 0
    errors: list[str] | None = None


class PaymentCalendarSync:
    """Best-effort mirror of the bills into Google Calendar.

    Saving a bill never fails because of Google: errors are returned as a warning
    text, and the next "Sincronizar" (or the next edit) retries. Events of bills
    deleted while Google was unreachable are queued in ``pending_deletes``.
    """

    _ERRORS = (GoogleCalendarAuthError, GoogleCalendarApiError)

    def __init__(self, service: RecurringPaymentService, enabled: bool = True) -> None:
        """``enabled=False`` (development) never calls Google nor touches the shared account file."""
        self._service = service
        self._enabled = enabled

    def status(self) -> dict:
        if not self._enabled:
            return {
                "has_client": False,
                "connected": False,
                "email": "",
                "pending_deletes": 0,
                "disabled": True,
                "disabled_label": ExternalSyncPolicy.DISABLED_LABEL,
                "disabled_detail": ExternalSyncPolicy.DISABLED_DETAIL,
            }
        account = GoogleCalendarStore.load_account()
        return {
            "has_client": GoogleCalendarAuth.has_client(),
            "connected": account["token"] != "",
            "email": account["email"],
            "pending_deletes": len(account["pending_deletes"]),
            "disabled": False,
        }

    def ensure_enabled(self) -> None:
        """Raise the user-facing reason when the mirror is disabled in this environment."""
        if not self._enabled:
            raise GoogleCalendarAuthError(f"Google Calendar: {ExternalSyncPolicy.DISABLED_DETAIL}")

    def is_connected(self) -> bool:
        return self._enabled and GoogleCalendarAuth.is_connected()

    def push(self, payment: RecurringPayment, label_caption: str) -> str | None:
        """Create/update (or remove, if reminders are off) the bill's event."""
        if not self.is_connected():
            return None
        try:
            client, tz = self._client()
            self._push_one(client, tz, payment, label_caption)
            return None
        except self._ERRORS as exc:
            return f"No se pudo actualizar Google Calendar: {exc}"

    def remove(self, payment: RecurringPayment) -> str | None:
        """Delete the event of a bill that is being deleted."""
        event_id = payment.google_event_id
        if not event_id or not self._enabled:
            return None
        if not self.is_connected():
            self._queue_delete(event_id)
            return None
        try:
            client, _tz = self._client()
            client.delete_event(event_id)
            return None
        except self._ERRORS as exc:
            self._queue_delete(event_id)
            return f"El evento se borrará de Google Calendar en la próxima sincronización ({exc})."

    def sync_all(self, labels: dict[str, str]) -> CalendarSyncReport:
        """Flush queued deletions and push every bill. ``labels`` maps label_id → caption."""
        self.ensure_enabled()
        report = CalendarSyncReport(errors=[])
        client, tz = self._client()
        account = GoogleCalendarStore.load_account()
        still_pending = []
        for event_id in account["pending_deletes"]:
            try:
                client.delete_event(event_id)
                report.removed += 1
            except GoogleCalendarApiError as exc:
                still_pending.append(event_id)
                report.errors.append(str(exc))
        account = GoogleCalendarStore.load_account()
        account["pending_deletes"] = still_pending
        GoogleCalendarStore.save_account(account)
        for pay in self._service.payments():
            try:
                self._push_one(client, tz, pay, labels.get(pay.label_id, ""))
                report.synced += 1 if pay.calendar_enabled else 0
            except GoogleCalendarApiError as exc:
                report.errors.append(f"{pay.name}: {exc}")
        return report

    def forget_event_ids(self) -> None:
        """After disconnecting, events stay in the old account: stop tracking them."""
        self.ensure_enabled()
        for pay in self._service.payments():
            if pay.google_event_id:
                self._service.set_google_event_id(pay.payment_id, "")

    def _push_one(self, client: GoogleCalendarClient, tz: str, pay: RecurringPayment, caption: str) -> None:
        wants_event = pay.calendar_enabled and len(pay.reminder_days) > 0
        if not wants_event:
            if pay.google_event_id:
                client.delete_event(pay.google_event_id)
                self._service.set_google_event_id(pay.payment_id, "")
            return
        body = GoogleCalendarEventBuilder.build(pay, caption, tz)
        event_id = client.update_event(pay.google_event_id, body) if pay.google_event_id else None
        if event_id is None:
            event_id = client.insert_event(body)
        if event_id != pay.google_event_id:
            self._service.set_google_event_id(pay.payment_id, event_id)

    def _client(self) -> tuple[GoogleCalendarClient, str]:
        client = GoogleCalendarClient(GoogleCalendarAuth.credentials())
        account = GoogleCalendarStore.load_account()
        if not account["time_zone"]:
            account["time_zone"] = client.time_zone()
            GoogleCalendarStore.save_account(account)
        return client, account["time_zone"]

    def _queue_delete(self, event_id: str) -> None:
        account = GoogleCalendarStore.load_account()
        if event_id not in account["pending_deletes"]:
            account["pending_deletes"].append(event_id)
            GoogleCalendarStore.save_account(account)
