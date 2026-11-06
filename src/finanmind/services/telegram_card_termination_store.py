"""Remembers which app card each NU card termination (last 4 digits) belongs to."""

from __future__ import annotations

import json
from pathlib import Path

from finanmind.config import AppConfig


class TelegramCardTerminationStore:
    """JSON-backed ``last4 -> card_id`` lookup used to route Telegram purchases."""

    FILENAME = "telegram_card_terminations.json"

    @classmethod
    def lookup(cls, last4: str) -> str | None:
        """Return the card id assigned to this termination, if any."""
        return cls._read_all().get(last4)

    @classmethod
    def assign(cls, last4: str, card_id: str) -> None:
        """Link (or re-link) a termination to a card."""
        if not card_id.strip():
            raise ValueError("Selecciona la tarjeta a la que pertenece esta terminación.")
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
