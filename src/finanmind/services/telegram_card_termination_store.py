"""Remembers which app card each NU card termination (last 4 digits) belongs to."""

from __future__ import annotations

import json
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.storage.d1_client import D1ClientProvider
from finanmind.storage.runtime_environment import RuntimeEnvironment


class TelegramCardTerminationStore:
    """``last4 -> card_id`` lookup used to route Telegram purchases.

    Backed by a workspace JSON file in development and by the D1 table
    ``telegram_card_terminations`` in production.
    """

    FILENAME = "telegram_card_terminations.json"

    @classmethod
    def lookup(cls, last4: str) -> str | None:
        """Return the card id assigned to this termination, if any."""
        if RuntimeEnvironment.uses_cloud_storage():
            return _D1CardTerminations.lookup(last4)
        return cls._read_all().get(last4)

    @classmethod
    def assign(cls, last4: str, card_id: str) -> None:
        """Link (or re-link) a termination to a card."""
        if not card_id.strip():
            raise ValueError("Selecciona la tarjeta a la que pertenece esta terminación.")
        if RuntimeEnvironment.uses_cloud_storage():
            _D1CardTerminations.assign(last4, card_id)
            return
        data = cls._read_all()
        data[last4] = card_id
        path = cls._path_or_raise()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def _read_all(cls) -> dict[str, str]:
        try:
            path = cls._path_or_raise()
        except RuntimeError:
            return {}
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def _path_or_raise(cls) -> Path:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace folder not configured yet.")
        return Path(root) / cls.FILENAME


class _D1CardTerminations:
    """Production backend; a termination cascades away when its card is deleted."""

    @staticmethod
    def lookup(last4: str) -> str | None:
        rows = D1ClientProvider.shared().query(
            "SELECT card_id FROM telegram_card_terminations WHERE last4 = ?", last4
        )
        return rows[0]["card_id"] if rows else None

    @staticmethod
    def assign(last4: str, card_id: str) -> None:
        # The user picked this card explicitly, so a missing card is reported, not skipped.
        written = D1ClientProvider.shared().query(
            "INSERT INTO telegram_card_terminations (last4, card_id) "
            "SELECT ?, ? WHERE EXISTS (SELECT 1 FROM credit_cards WHERE card_id = ?) "
            "ON CONFLICT (last4) DO UPDATE SET card_id = excluded.card_id RETURNING last4",
            last4,
            card_id,
            card_id,
        )
        if not written:
            raise ValueError("La tarjeta seleccionada ya no existe. Actualiza la lista y elige otra.")
