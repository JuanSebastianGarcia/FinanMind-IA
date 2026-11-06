"""Finds NU credit-card statement emails via IMAP and extracts the billing period."""

from __future__ import annotations

import email
import imaplib
import re
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime

_PERIOD_PATTERN = re.compile(
    r"Per[íi]odo facturado</strong>.*?<strong>([^<]+)</strong>",
    re.IGNORECASE | re.DOTALL,
)

_WHITESPACE_PATTERN = re.compile(r"\s+")


class NuStatementEmailScanner:
    """Scans a Gmail inbox for NU statement-arrival emails."""

    HOST = "imap.gmail.com"
    SENDER = "nu@nu.com.co"
    SUBJECT_NEEDLE = "extracto de tu tarjeta de crédito nu"
    MAX_LOOKBACK_DAYS = 365

    @classmethod
    def scan(cls, email_address: str, app_password: str, limit: int = 25) -> list[dict]:
        """Return the most recent matching statement emails, newest first."""
        connection = imaplib.IMAP4_SSL(cls.HOST)
        try:
            connection.login(email_address, app_password)
        except imaplib.IMAP4.error as err:
            raise ValueError(
                "No se pudo iniciar sesión en Gmail. Reconecta la cuenta en la tarjeta.",
            ) from err
        try:
            return cls._scan_with_connection(connection, limit)
        finally:
            try:
                connection.logout()
            except OSError:
                pass

    @classmethod
    def _scan_with_connection(cls, connection: imaplib.IMAP4_SSL, limit: int) -> list[dict]:
        connection.select("INBOX", readonly=True)
        since_date = (datetime.now(timezone.utc) - timedelta(days=cls.MAX_LOOKBACK_DAYS)).strftime("%d-%b-%Y")
        status, data = connection.search(None, "FROM", cls.SENDER, "SINCE", since_date)
        if status != "OK":
            raise ValueError("No se pudo buscar correos de NU en la bandeja de entrada.")
        message_ids = data[0].split()
        results: list[dict] = []
        for message_id in reversed(message_ids):
            entry = cls._process_message(connection, message_id)
            if entry is not None:
                results.append(entry)
            if len(results) >= limit:
                break
        return results

    @classmethod
    def _process_message(cls, connection: imaplib.IMAP4_SSL, message_id: bytes) -> dict | None:
        status, data = connection.fetch(message_id, "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            return None
        raw = data[0][1]
        message = email.message_from_bytes(raw)
        subject = cls._decode_header(message.get("Subject", ""))
        if not cls._matches_subject(subject):
            return None
        html = cls._extract_html(message)
        return {
            "message_id": message_id.decode("ascii", errors="replace"),
            "subject": subject,
            "received_at": message.get("Date", ""),
            "received_year": cls._extract_year(message.get("Date", "")),
            "period_label": cls._extract_period(html) if html else "",
        }

    @classmethod
    def _extract_year(cls, date_header: str) -> int | None:
        if not date_header:
            return None
        try:
            return parsedate_to_datetime(date_header).year
        except (TypeError, ValueError):
            return None

    @classmethod
    def fetch_pdf_attachments(
        cls,
        email_address: str,
        app_password: str,
        message_ids: list[str],
    ) -> dict[str, bytes]:
        """Return ``{message_id: pdf_bytes}`` for the statement PDF attached to each email."""
        connection = imaplib.IMAP4_SSL(cls.HOST)
        try:
            connection.login(email_address, app_password)
        except imaplib.IMAP4.error as err:
            raise ValueError(
                "No se pudo iniciar sesión en Gmail. Reconecta la cuenta en la tarjeta.",
            ) from err
        try:
            connection.select("INBOX", readonly=True)
            return {
                message_id: cls._fetch_one_pdf(connection, message_id)
                for message_id in message_ids
            }
        finally:
            try:
                connection.logout()
            except OSError:
                pass

    @classmethod
    def _fetch_one_pdf(cls, connection: imaplib.IMAP4_SSL, message_id: str) -> bytes:
        status, data = connection.fetch(message_id.encode("ascii"), "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            raise ValueError("No se pudo descargar uno de los correos seleccionados.")
        message = email.message_from_bytes(data[0][1])
        for part in message.walk():
            if part.get_content_type() == "application/pdf":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload
        raise ValueError("Uno de los correos seleccionados no trae el PDF del extracto adjunto.")

    @classmethod
    def _matches_subject(cls, subject: str) -> bool:
        # RFC 2047 line-folding between an encoded word and a plain-text word can drop
        # the space between them (e.g. "tarjeta de" + "crédito" -> "tarjeta decrédito"),
        # so compare with whitespace stripped out entirely instead of an exact substring.
        normalized_subject = _WHITESPACE_PATTERN.sub("", subject.lower())
        normalized_needle = _WHITESPACE_PATTERN.sub("", cls.SUBJECT_NEEDLE)
        return normalized_needle in normalized_subject

    @classmethod
    def _decode_header(cls, raw_header: str) -> str:
        decoded = ""
        for text, encoding in decode_header(raw_header):
            if isinstance(text, bytes):
                decoded += text.decode(encoding or "utf-8", errors="replace")
            else:
                decoded += text
        return decoded

    @classmethod
    def _extract_html(cls, message: Message) -> str:
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/html":
                    return cls._decode_payload(part)
            return ""
        if message.get_content_type() == "text/html":
            return cls._decode_payload(message)
        return ""

    @classmethod
    def _decode_payload(cls, part: Message) -> str:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ""
        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")

    @classmethod
    def _extract_period(cls, html: str) -> str:
        match = _PERIOD_PATTERN.search(html)
        return match.group(1).strip() if match else ""
