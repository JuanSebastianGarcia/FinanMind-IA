"""Parse USD amounts typed by users (digits, optional decimal dot)."""

import re


class UsdAmountParser:
    """Converts human-entered USD strings into floats."""

    _NON_DIGIT_DOT = re.compile(r"[^\d.]")

    @classmethod
    def parse(cls, raw: str) -> float:
        """Strip grouping commas and symbols; accept one decimal dot."""
        trimmed = raw.strip()
        if trimmed == "":
            raise ValueError("Vacío")
        cleaned = cls._NON_DIGIT_DOT.sub("", trimmed.replace(",", ""))
        if cleaned == "" or cleaned == ".":
            raise ValueError("Sin dígitos")
        if cleaned.count(".") > 1:
            raise ValueError("Use un solo punto decimal")
        return float(cleaned)
