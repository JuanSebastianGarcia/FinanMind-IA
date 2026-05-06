"""Parse COP amounts typed by users."""

import re


class CopAmountParser:
    """Converts human-entered COP strings into floats."""

    _NON_DIGIT = re.compile(r"[^\d]")

    @classmethod
    def parse(cls, raw: str) -> float:
        """Strip symbols and grouping dots, then parse whole pesos."""
        trimmed = raw.strip()
        if trimmed == "":
            raise ValueError("Vacío")
        digits_only = cls._NON_DIGIT.sub("", trimmed)
        if digits_only == "":
            raise ValueError("Sin dígitos")
        return float(digits_only)
