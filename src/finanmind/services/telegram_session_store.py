"""Persists the Telegram user session used to read the NU purchase-notification chat."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.services.dpapi_secret_codec import DpapiSecretCodec


@dataclass(frozen=True)
class TelegramCredentials:
    """Everything needed to open the session and reach the notification chat."""

    api_id: int
    api_hash: str
    session: str
    peer_id: int
    peer_access_hash: int


class TelegramSessionStore:
    """Reads/writes ``telegram_automation.json`` under the workspace.

    The api hash and the Telethon ``StringSession`` are encrypted via DPAPI (see
    ``DpapiSecretCodec``): the session grants full access to the Telegram account,
    so a copied data folder must never expose it in plain text. The chat is stored
    as ``peer_id`` + ``peer_access_hash`` so it never has to be re-resolved by
    username (Telegram rate-limits username lookups heavily).
    """

    FILENAME = "telegram_automation.json"

    @classmethod
    def load(cls) -> TelegramCredentials | None:
        """Return the stored credentials, or ``None`` when Telegram is not set up."""
        path = cls._path_or_none()
        if path is None or not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return TelegramCredentials(
            api_id=int(data["api_id"]),
            api_hash=DpapiSecretCodec.decrypt(data["api_hash"]),
            session=DpapiSecretCodec.decrypt(data["session"]),
            peer_id=int(data["peer_id"]),
            peer_access_hash=int(data["peer_access_hash"]),
        )

    @classmethod
    def save(cls, credentials: TelegramCredentials) -> None:
        """Persist the credentials, encrypting the secret parts."""
        path = cls._path_or_none()
        if path is None:
            raise RuntimeError("Workspace folder not configured yet.")
        payload = {
            "api_id": credentials.api_id,
            "api_hash": DpapiSecretCodec.encrypt(credentials.api_hash),
            "session": DpapiSecretCodec.encrypt(credentials.session),
            "peer_id": credentials.peer_id,
            "peer_access_hash": credentials.peer_access_hash,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(path)

    @classmethod
    def _path_or_none(cls) -> Path | None:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            return None
        return Path(root) / cls.FILENAME
