"""Investment portfolio persisted in Cloudflare D1 (production backend of ``InvestmentRepository``)."""

from __future__ import annotations

from finanmind.models.investment_category import InvestmentCategory
from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.models.investment_entry import InvestmentEntry
from finanmind.storage.d1_client import D1Client
from finanmind.storage.d1_table_sync import D1Table, D1TableSync, Row


class InvestmentD1Repository:
    """Same contract as ``InvestmentRepository`` (``load_all`` / ``save_all``).

    ``investment_entries.category_id`` is a plain NOT NULL foreign key: the service
    refuses to delete a category still in use, so an entry pointing to a missing
    category makes the batch fail instead of being dropped silently.
    """

    CATEGORIES = D1Table(
        "investment_categories",
        ("category_id",),
        ("category_id", "name"),
        order_by="lower(name), category_id",
    )
    ENTRIES = D1Table(
        "investment_entries",
        ("investment_id",),
        ("investment_id", "category_id", "amount", "currency_code", "invested_date_iso", "description"),
        order_by="invested_date_iso, category_id, investment_id",
    )

    def __init__(self, client: D1Client) -> None:
        self._client = client
        self._categories = D1TableSync(self.CATEGORIES)
        self._entries = D1TableSync(self.ENTRIES)

    def load_all(self) -> tuple[list[InvestmentCategory], list[InvestmentEntry]]:
        """Return categories and holdings in the order the CSV codec writes them."""
        category_rows, entry_rows = D1TableSync.read(self._client, [self._categories, self._entries])
        categories = [InvestmentCategory(category_id=r["category_id"], name=r["name"]) for r in category_rows]
        entries = [
            InvestmentEntry(
                investment_id=r["investment_id"],
                category_id=r["category_id"],
                amount=float(r["amount"]),
                currency_code=InvestmentCurrencyCode.from_storage_cell(r["currency_code"] or ""),
                invested_date_iso=r["invested_date_iso"],
                description=r["description"],
            )
            for r in entry_rows
        ]
        return categories, entries

    def save_all(self, categories: list[InvestmentCategory], entries: list[InvestmentEntry]) -> None:
        """Make both tables equal the given lists in one atomic batch."""
        category_rows: list[Row] = [{"category_id": c.category_id, "name": c.name} for c in categories]
        entry_rows: list[Row] = [self._entry_row(e) for e in entries]
        D1TableSync.write(self._client, [(self._categories, category_rows), (self._entries, entry_rows)])

    @staticmethod
    def _entry_row(entry: InvestmentEntry) -> Row:
        currency = InvestmentCurrencyCode.from_storage_cell(entry.currency_code)
        return {
            "investment_id": entry.investment_id,
            "category_id": entry.category_id,
            "amount": _amount(entry.amount, currency),
            "currency_code": currency,
            "invested_date_iso": entry.invested_date_iso,
            "description": entry.description,
        }


def _amount(amount: float, currency: str) -> int | float:
    """Round like the CSV codec: whole pesos for COP, cents for USD."""
    if currency == InvestmentCurrencyCode.USD:
        return round(float(amount), 2)
    return int(round(amount))
