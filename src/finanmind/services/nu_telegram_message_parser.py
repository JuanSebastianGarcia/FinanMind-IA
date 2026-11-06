"""Turns the NU purchase notifications forwarded to Telegram into purchase dicts.

Every approved purchase arrives as three messages sent in the same second, e.g.:

    Compra aprobada por $10.000,00
    1700000000000
    Tu compra en COMERCIO EJEMPLO por $10.000,00 con tu tarjeta terminada en 0000 ha sido APROBADA.

The third message carries merchant, amount and card on its own, so it drives the
parsing; the second one (the phone notification's timestamp in milliseconds) only gives
the exact purchase date. The three are sent concurrently, so the timestamp may land
just before or just after the purchase message. Anything else in the chat (tests with
unreplaced ``{placeholders}``, manual messages) is ignored.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

_PURCHASE_PATTERN = re.compile(
    r"Tu compra en (?P<merchant>.+?) por \$?\s*(?P<amount>[\d.,]+) con tu tarjeta "
    r"terminada en (?P<last4>\d{4}) ha sido APROBADA",
    re.IGNORECASE | re.DOTALL,
)
_TIMESTAMP_PATTERN = re.compile(r"^\s*(\d{13})\s*$")

# Colombia has no DST, so a fixed offset avoids depending on the tzdata package.
_COLOMBIA_TZ = timezone(timedelta(hours=-5))

# The three messages of one notification are sent back to back; a timestamp
# farther than this many positions or seconds away belongs to another purchase.
_MAX_TIMESTAMP_DISTANCE = 2
_MAX_TIMESTAMP_GAP_SECONDS = 120


class NuTelegramMessageParser:
    """Groups the chat messages into purchases."""

    @classmethod
    def parse(cls, messages: list[dict]) -> list[dict]:
        """Parse ``{"id", "date" (aware datetime), "text"}`` messages, oldest first.

        Returns one dict per approved purchase with ``purchase_id``, ``message_id``,
        ``occurred_on`` (ISO date, Colombia time), ``merchant``, ``value`` (text as
        sent, e.g. ``"$15.500,00"``) and ``last4``.
        """
        purchases = []
        used_stamps: set[int] = set()
        for index, message in enumerate(messages):
            match = _PURCHASE_PATTERN.search(message.get("text") or "")
            if match is None:
                continue
            stamp_index = cls._nearest_timestamp(messages, index, used_stamps)
            stamp_ms = None
            if stamp_index is not None:
                used_stamps.add(stamp_index)
                stamp_ms = int(messages[stamp_index]["text"].strip())
            when = cls._purchase_moment(message["date"], stamp_ms)
            purchases.append({
                "purchase_id": f"tg-{message['id']}",
                "message_id": message["id"],
                "occurred_on": when.date().isoformat(),
                "merchant": " ".join(match.group("merchant").split()),
                "value": f"${match.group('amount')}",
                "last4": match.group("last4"),
            })
        return purchases

    @classmethod
    def _nearest_timestamp(cls, messages: list[dict], index: int, used: set[int]) -> int | None:
        """Index of the closest unused millisecond-timestamp message sent with this purchase."""
        body = messages[index]
        for distance in range(1, _MAX_TIMESTAMP_DISTANCE + 1):
            for candidate_index in (index - distance, index + distance):
                if candidate_index in used or not 0 <= candidate_index < len(messages):
                    continue
                match = _TIMESTAMP_PATTERN.match(messages[candidate_index].get("text") or "")
                if match is None:
                    continue
                stamp = datetime.fromtimestamp(int(match.group(1)) / 1000, timezone.utc)
                if abs((body["date"] - stamp).total_seconds()) <= _MAX_TIMESTAMP_GAP_SECONDS:
                    return candidate_index
        return None

    @classmethod
    def _purchase_moment(cls, sent_at: datetime, stamp_ms: int | None) -> datetime:
        if stamp_ms:
            return datetime.fromtimestamp(stamp_ms / 1000, _COLOMBIA_TZ)
        return sent_at.astimezone(_COLOMBIA_TZ)
