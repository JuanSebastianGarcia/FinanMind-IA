"""Background reader that pulls new NU purchase notifications from Telegram."""

from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import InputPeerUser

from finanmind.services.nu_telegram_message_parser import NuTelegramMessageParser
from finanmind.services.telegram_session_store import TelegramCredentials, TelegramSessionStore
from finanmind.services.telegram_sync_state_store import TelegramSyncStateStore

_LOGGER = logging.getLogger(__name__)

# Messages re-read before the checkpoint so a purchase whose timestamp message
# landed just before the previous read still gets its exact date.
_CONTEXT_OVERLAP = 2


class TelegramExpenseSync:
    """Owns a daemon thread that reads the notification chat every ``POLL_SECONDS``.

    It only *queues* purchases (see ``TelegramSyncStateStore``); classifying and
    registering them happens from the UI, through the same path as the statement
    PDF import, so the user can be asked about merchants it has never seen.
    """

    POLL_SECONDS = 60

    def __init__(self, enabled: bool = True) -> None:
        self._thread: threading.Thread | None = None
        self._wake = threading.Event()
        self._enabled = enabled
        self._state = "not_configured" if enabled else "disabled"
        self._error = ""

    def start(self) -> None:
        """Start reading in the background; no-op when disabled or Telegram is not set up."""
        if self._thread is not None or not self._enabled:
            return
        try:
            credentials = TelegramSessionStore.load()
        except Exception as err:  # corrupt file or DPAPI blob from another user
            self._set_error(f"No se pudo leer la configuración de Telegram: {err}")
            return
        if credentials is None:
            return
        self._state = "starting"
        self._thread = threading.Thread(
            target=lambda: asyncio.run(self._loop(credentials)),
            name="telegram-expense-sync",
            daemon=True,
        )
        self._thread.start()

    def request_sync(self) -> None:
        """Read right away instead of waiting for the next poll."""
        self._wake.set()

    def status(self) -> dict:
        """Snapshot for the UI: reader state, last read time and queued purchases.

        When disabled the shared queue is hidden, so the UI never drains it.
        """
        if not self._enabled:
            return {"state": "disabled", "error": "", "last_read_at": "", "pending": []}
        _last_id, last_read_at = TelegramSyncStateStore.checkpoint()
        return {
            "state": self._state,
            "error": self._error,
            "last_read_at": last_read_at,
            "pending": TelegramSyncStateStore.pending(),
        }

    async def _loop(self, credentials: TelegramCredentials) -> None:
        client = TelegramClient(StringSession(credentials.session), credentials.api_id, credentials.api_hash)
        peer = InputPeerUser(credentials.peer_id, credentials.peer_access_hash)
        while True:
            try:
                if not client.is_connected():
                    await client.connect()
                if not await client.is_user_authorized():
                    self._set_error("La sesión de Telegram expiró o fue cerrada. Hay que volver a iniciar sesión.")
                    return
                await self._read_once(client, peer)
                self._state, self._error = "ok", ""
            except Exception as err:  # network drops etc.: report and retry next poll
                self._set_error(f"No se pudo leer Telegram: {err}")
            await asyncio.to_thread(self._wake.wait, self.POLL_SECONDS)
            self._wake.clear()

    async def _read_once(self, client: TelegramClient, peer: InputPeerUser) -> None:
        last_id, _last_read_at = TelegramSyncStateStore.checkpoint()
        messages = [
            {"id": message.id, "date": message.date, "text": message.message or ""}
            async for message in client.iter_messages(
                peer, min_id=max(0, last_id - _CONTEXT_OVERLAP - 1), reverse=True,
            )
        ]
        purchases = [
            purchase for purchase in NuTelegramMessageParser.parse(messages)
            if purchase["message_id"] > last_id
        ]
        newest_id = max([last_id] + [message["id"] for message in messages])
        read_at = datetime.now().isoformat(timespec="seconds")
        queued = TelegramSyncStateStore.record_read(newest_id, read_at, purchases)
        if queued:
            _LOGGER.info("Telegram: %s compra(s) nuevas en cola", queued)

    def _set_error(self, message: str) -> None:
        _LOGGER.warning(message)
        self._state, self._error = "error", message
