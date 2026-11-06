"""Persists Gmail IMAP credentials used to automate expense processing per card."""

from __future__ import annotations

import json
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.services.dpapi_secret_codec import DpapiSecretCodec


class GmailAutomationStore:
    """Reads/writes one Gmail account (email + app password) per ``card_id``.

    The app password is encrypted at rest via DPAPI (see ``DpapiSecretCodec``) so a
    copied data folder does not leak it in plain text; only the current Windows
    user on this machine can decrypt it back.
    """

    FILENAME = "gmail_card_automations.json"

    @classmethod
    def get(cls, card_id: str) -> dict | None:
        """Return the stored ``{"email": ...}`` for a card, without the password."""
        entry = cls._read_all().get(card_id)
        if entry is None:
            return None
        return {"email": entry.get("email", "")}

    @classmethod
    def save(cls, card_id: str, email: str, app_password: str) -> None:
        """Persist the Gmail credentials linked to one card."""
        cleaned_email = email.strip()
        cleaned_password = app_password.strip()
        if not cleaned_email:
            raise ValueError("El correo es obligatorio.")
        if not cleaned_password:
            raise ValueError("La clave de aplicación es obligatoria.")
        data = cls._read_all()
        data[card_id] = {
            "email": cleaned_email,
            "app_password_enc": DpapiSecretCodec.encrypt(cleaned_password),
        }
        cls._write_all(data)

    @classmethod
    def clear(cls, card_id: str) -> None:
        """Remove the Gmail credentials linked to one card, when present."""
        data = cls._read_all()
        if card_id in data:
            del data[card_id]
            cls._write_all(data)

    @classmethod
    def credentials_for(cls, card_id: str) -> tuple[str, str] | None:
        """Return the decrypted ``(email, app_password)`` pair used to connect, if configured."""
        entry = cls._read_all().get(card_id)
        if entry is None:
            return None
        encrypted = entry.get("app_password_enc", "")
        password = DpapiSecretCodec.decrypt(encrypted) if encrypted else ""
        return entry.get("email", ""), password

    @classmethod
    def _read_all(cls) -> dict:
        try:
            path = cls._path_or_raise()
        except RuntimeError:
            return {}
        if not path.is_file():
            return {}
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        return json.loads(raw)

    @classmethod
    def _write_all(cls, data: dict) -> None:
        path = cls._path_or_raise()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def _path_or_raise(cls) -> Path:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace folder not configured yet.")
        return Path(root) / cls.FILENAME
