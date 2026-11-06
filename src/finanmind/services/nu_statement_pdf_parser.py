"""Parses the expense table out of a password-protected NU credit-card statement PDF.

The statement is a JasperReports-generated PDF. From the second page onward it repeats
a table with a fixed column layout (same x-coordinates on every page):

    Fecha | Descripción | Valor | Cuotas | Valor del mes | Interés (%) | Interés (valor)
    | Total a pagar este mes | Restante por pagar

Each transaction spans two lines: the first carries the day+month, description and all
amount columns; the second carries only the year (plus, when the merchant name wraps,
extra description words). A few rows (e.g. "Gracias por tu pago") are followed by
"↪ ..." breakdown lines that add no column data and are ignored.
"""

from __future__ import annotations

import io
import re

import pdfplumber


class NuPdfWrongPasswordError(ValueError):
    """Raised when the supplied password fails to open a statement PDF."""


_MONTHS = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12,
}

_DAY_PATTERN = re.compile(r"^\d{1,2}$")
_YEAR_PATTERN = re.compile(r"^\d{4}$")

# Column x0 boundaries lifted from the statement's header row; a word belongs to the
# first column whose upper bound is greater than the word's x0.
_COLUMNS = [
    ("date", 79.0),
    ("description", 149.0),
    ("value", 209.0),
    ("installments", 257.0),
    ("monthly_value", 319.0),
    ("interest_pct", 352.0),
    ("interest_value", 421.0),
    ("total_this_month", 503.0),
    ("remaining", 10_000.0),
]

# Continuation lines belonging to the same transaction (year, wrapped merchant name,
# "Gracias por tu pago" breakdown) never sit farther than this from the row start;
# statement rows themselves are always spaced ~44pt+ apart.
_MAX_CONTINUATION_GAP = 35.0
_ROW_TOP_TOLERANCE = 1.5


class NuStatementPdfParser:
    """Extracts the transaction table from a NU statement PDF into plain dicts."""

    @classmethod
    def parse(cls, pdf_bytes: bytes, password: str) -> list[dict]:
        """Return one dict per transaction row, in the order printed in the PDF."""
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes), password=password) as pdf:
                rows: list[dict] = []
                for page in pdf.pages[1:]:
                    rows.extend(cls._parse_page(page))
                return rows
        except Exception as err:
            if cls._is_wrong_password(err):
                raise NuPdfWrongPasswordError("La contraseña del PDF no es correcta.") from err
            raise ValueError(
                "No se pudo leer el PDF del extracto.",
            ) from err

    @classmethod
    def _is_wrong_password(cls, err: Exception) -> bool:
        # pdfplumber wraps pdfminer's PDFPasswordIncorrect inside a generic
        # PdfminerException(original_error), so check the wrapped exception's name too.
        candidates = [err, *err.args]
        return any(type(candidate).__name__ == "PDFPasswordIncorrect" for candidate in candidates)

    @classmethod
    def _parse_page(cls, page) -> list[dict]:
        lines = cls._group_lines(page.extract_words())
        rows: list[dict] = []
        index = 0
        while index < len(lines):
            if cls._is_row_start(lines[index]):
                row, consumed = cls._build_row(lines, index)
                rows.append(row)
                index += consumed
            else:
                index += 1
        return rows

    @classmethod
    def _group_lines(cls, words: list[dict]) -> list[tuple[float, list[dict]]]:
        by_top: list[tuple[float, list[dict]]] = []
        for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
            if by_top and abs(by_top[-1][0] - word["top"]) <= _ROW_TOP_TOLERANCE:
                by_top[-1][1].append(word)
            else:
                by_top.append((word["top"], [word]))
        return by_top

    @classmethod
    def _is_row_start(cls, line: tuple[float, list[dict]]) -> bool:
        words = line[1]
        if len(words) < 2:
            return False
        return _DAY_PATTERN.match(words[0]["text"]) is not None and words[1]["text"] in _MONTHS

    @classmethod
    def _build_row(cls, lines: list[tuple[float, list[dict]]], index: int) -> tuple[dict, int]:
        start_top, words = lines[index]
        day = int(words[0]["text"])
        month = _MONTHS[words[1]["text"]]
        remainder = words[2:]
        year = None
        # Most rows wrap the year onto the next line, but some fit "DD MON YYYY" on
        # one line — handle both by checking the word right after the month first.
        if remainder and _YEAR_PATTERN.match(remainder[0]["text"]):
            year = int(remainder[0]["text"])
            remainder = remainder[1:]
        columns = cls._bucket_columns(remainder)
        if year is None:
            year, consumed = cls._consume_continuation(lines, index, start_top, columns)
        else:
            consumed = 1
        row = {
            "occurred_on": f"{year:04d}-{month:02d}-{day:02d}",
            "description": " ".join(columns["description"]).strip(),
            "value": " ".join(columns["value"]).strip(),
            "installments": " ".join(columns["installments"]).strip(),
            "monthly_value": " ".join(columns["monthly_value"]).strip(),
            "interest_pct": " ".join(columns["interest_pct"]).strip(),
            "interest_value": " ".join(columns["interest_value"]).strip(),
            "total_this_month": " ".join(columns["total_this_month"]).strip(),
            "remaining": " ".join(columns["remaining"]).strip(),
        }
        return row, consumed

    @classmethod
    def _consume_continuation(
        cls,
        lines: list[tuple[float, list[dict]]],
        index: int,
        start_top: float,
        columns: dict[str, list[str]],
    ) -> tuple[int, int]:
        year = None
        consumed = 1
        cursor = index + 1
        while cursor < len(lines):
            top, words = lines[cursor]
            if cls._is_row_start((top, words)) or (top - start_top) > _MAX_CONTINUATION_GAP:
                break
            if year is None and words and _YEAR_PATTERN.match(words[0]["text"]):
                year = int(words[0]["text"])
                extra = cls._bucket_columns(words[1:])
                columns["description"].extend(extra["description"])
            consumed += 1
            cursor += 1
        if year is None:
            raise ValueError("No se pudo determinar el año de una transacción del extracto.")
        return year, consumed

    @classmethod
    def _bucket_columns(cls, words: list[dict]) -> dict[str, list[str]]:
        buckets: dict[str, list[str]] = {name: [] for name, _ in _COLUMNS}
        for word in words:
            for name, upper_bound in _COLUMNS:
                if word["x0"] < upper_bound:
                    buckets[name].append(word["text"])
                    break
        return buckets
