"""Encrypts small secrets at rest using the Windows Data Protection API (DPAPI).

Ciphertext is bound to the current Windows user account: it can only be decrypted
by the same user on the same machine, which is what keeps a copied data folder
from leaking plaintext secrets (e.g. the Gmail app password).
"""

from __future__ import annotations

import base64

import win32crypt


class DpapiSecretCodec:
    """Wraps ``CryptProtectData``/``CryptUnprotectData`` for storing text secrets."""

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """Return a base64 string safe to embed in JSON/CSV."""
        blob = win32crypt.CryptProtectData(plaintext.encode("utf-8"), None, None, None, None, 0)
        return base64.b64encode(blob).decode("ascii")

    @classmethod
    def decrypt(cls, encoded: str) -> str:
        """Reverse :meth:`encrypt`; raises if the blob is corrupt or from another user/machine."""
        blob = base64.b64decode(encoded.encode("ascii"))
        _description, decrypted = win32crypt.CryptUnprotectData(blob, None, None, None, 0)
        return decrypted.decode("utf-8")
