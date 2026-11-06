"""Persists the Telegram reading checkpoint plus the purchases waiting to be registered."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from finanmind.config import AppConfig


class TelegramSyncStateStore:
    """Reads/writes ``telegram_sync_state.json`` under the workspace.

    Holds ``last_message_id`` / ``last_read_at`` (where the next read starts) and
    ``pending``: purchases already read from the chat but not yet registered or
    discarded as duplicates. New purchases are queued *in the same write* that
    advances the checkpoint, so a crash can never skip a purchase.

    Both the background reader thread and the JS bridge threads touch this file,
    hence the module-wide lock around every read-modify-write.
    """

    FILENAME = "telegram_sync_state.json"
    _LOCK = threading.Lock()

    @classmethod
    def checkpoint(cls) -> tuple[int, str]:
        """Return ``(last_message_id, last_read_at)``; ``(0, "")`` before the first read."""
        with cls._LOCK:
            data = cls._read()
        return int(data.get("last_message_id", 0)), data.get("last_read_at", "")

    @classmethod
    def pending(cls) -> list[dict]:
        """Return the purchases still waiting to be registered."""
        with cls._LOCK:
            return list(cls._read().get("pending", []))

    @classmethod
    def record_read(cls, last_message_id: int, read_at: str, purchases: list[dict]) -> int:
        """Queue new purchases and move the checkpoint; return how many were queued."""
        with cls._LOCK:
            data = cls._read()
            pending = data.get("pending", [])
            known_ids = {item["purchase_id"] for item in pending}
            fresh = [item for item in purchases if item["purchase_id"] not in known_ids]
            data["pending"] = pending + fresh
            data["last_message_id"] = max(last_message_id, int(data.get("last_message_id", 0)))
            data["last_read_at"] = read_at
            cls._write(data)
        return len(fresh)

    @classmethod
    def resolve(cls, purchase_id: str) -> None:
        """Drop one purchase from the queue once registered or found duplicated."""
        with cls._LOCK:
            data = cls._read()
            data["pending"] = [item for item in data.get("pending", []) if item["purchase_id"] != purchase_id]
            cls._write(data)

    @classmethod
    def _read(cls) -> dict:
        path = cls._path_or_none()
        if path is None or not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def _write(cls, data: dict) -> None:
        path = cls._path_or_none()
        if path is None:
            raise RuntimeError("Workspace folder not configured yet.")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)

    @classmethod
    def _path_or_none(cls) -> Path | None:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            return None
        return Path(root) / cls.FILENAME
