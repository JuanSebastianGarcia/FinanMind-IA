"""Validates that a Gmail account accepts IMAP login with an app password."""

from __future__ import annotations

import imaplib


class GmailConnectionValidator:
    """Attempts an IMAP login/logout round-trip against Gmail."""

    IMAP_HOST = "imap.gmail.com"

    @classmethod
    def validate(cls, email: str, app_password: str) -> None:
        """Raise ``ValueError`` with a human message when the connection fails."""
        try:
            connection = imaplib.IMAP4_SSL(cls.IMAP_HOST)
        except OSError as err:
            raise ValueError(f"No se pudo contactar Gmail: {err}") from err
        try:
            connection.login(email, app_password)
            connection.select("INBOX")
        except imaplib.IMAP4.error as err:
            raise ValueError(
                "No se pudo iniciar sesión. Verifica el correo y la clave de aplicación.",
            ) from err
        finally:
            try:
                connection.logout()
            except OSError:
                pass
