"""Persists the shared password used to open a card's NU statement PDFs.

Encrypted at rest via DPAPI (see ``DpapiSecretCodec``), same as the Gmail app
password, so it survives being remembered without sitting in plain text on disk.
"""

from __future__ import annotations

import json
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.services.dpapi_secret_codec import DpapiSecretCodec


class NuPdfPasswordStore:
    """Reads/writes one PDF password per ``card_id`` (NU reuses it across statements)."""

    FILENAME = "nu_pdf_passwords.json"

    @classmethod
    def get(cls, card_id: str) -> str | None:
        """Return the remembered, decrypted password for this card, if any."""
        encrypted = cls._read_all().get(card_id)
        if not encrypted:
            return None
        return DpapiSecretCodec.decrypt(encrypted)

    @classmethod
    def save(cls, card_id: str, password: str) -> None:
        """Remember (or replace) the password used for this card's statements."""
        cleaned = password.strip()
        if not cleaned:
            return
        data = cls._read_all()
        data[card_id] = DpapiSecretCodec.encrypt(cleaned)
        cls._write_all(data)

    @classmethod
    def clear(cls, card_id: str) -> None:
        """Forget the remembered password for this card, when present."""
        data = cls._read_all()
        if card_id in data:
            del data[card_id]
            cls._write_all(data)

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
