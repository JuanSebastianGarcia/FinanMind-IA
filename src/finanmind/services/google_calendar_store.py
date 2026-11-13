"""Persists the Google Calendar OAuth client, the user token and sync bookkeeping."""

from __future__ import annotations

import json
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.services.dpapi_secret_codec import DpapiSecretCodec


class GoogleCalendarStore:
    """Reads/writes two JSON files under the workspace.

    - ``google_calendar_client.json``: the OAuth "desktop app" client downloaded
      from Google Cloud (encrypted with DPAPI).
    - ``google_calendar_account.json``: the authorized user token (encrypted with
      DPAPI: it grants access to the calendar), the account email, the calendar
      time zone and event ids still waiting to be deleted while offline.
    """

    CLIENT_FILENAME = "google_calendar_client.json"
    ACCOUNT_FILENAME = "google_calendar_account.json"

    @classmethod
    def load_client_config(cls) -> dict | None:
        data = cls._read(cls.CLIENT_FILENAME)
        if data is None or "client" not in data:
            return None
        return json.loads(DpapiSecretCodec.decrypt(data["client"]))

    @classmethod
    def save_client_config(cls, config: dict) -> None:
        cls._write(cls.CLIENT_FILENAME, {"client": DpapiSecretCodec.encrypt(json.dumps(config))})

    @classmethod
    def load_account(cls) -> dict:
        """Return ``{token, email, time_zone, pending_deletes}`` (token decrypted, may be empty)."""
        data = cls._read(cls.ACCOUNT_FILENAME) or {}
        token = data.get("token") or ""
        return {
            "token": DpapiSecretCodec.decrypt(token) if token else "",
            "email": data.get("email") or "",
            "time_zone": data.get("time_zone") or "",
            "pending_deletes": list(data.get("pending_deletes") or []),
        }

    @classmethod
    def save_account(cls, account: dict) -> None:
        token = account.get("token") or ""
        cls._write(cls.ACCOUNT_FILENAME, {
            "token": DpapiSecretCodec.encrypt(token) if token else "",
            "email": account.get("email") or "",
            "time_zone": account.get("time_zone") or "",
            "pending_deletes": list(account.get("pending_deletes") or []),
        })

    @classmethod
    def _read(cls, filename: str) -> dict | None:
        path = cls._path(filename)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def _write(cls, filename: str, payload: dict) -> None:
        path = cls._path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(path)

    @classmethod
    def _path(cls, filename: str) -> Path:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace folder not configured yet.")
        return Path(root) / filename
