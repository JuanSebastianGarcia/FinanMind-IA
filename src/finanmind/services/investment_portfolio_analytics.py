"""Pure summaries and distribution ratios for the investment portfolio."""

from __future__ import annotations

from finanmind.models.investment_category import InvestmentCategory
from finanmind.models.investment_entry import InvestmentEntry


class InvestmentPortfolioAnalytics:
    """Computes totals and per-category shares without mutating stored rows."""

    def __init__(self, entries: list[InvestmentEntry], categories: list[InvestmentCategory]) -> None:
        self._ents = entries
        self._cats = categories

    def entry_count(self) -> int:
        """Return how many individual holdings exist."""
        return len(self._ents)

    def defined_category_count(self) -> int:
        """Return how many category rows are defined."""
        return len(self._cats)

    def total_for_currency(self, currency_code: str) -> float:
        """Return the sum of amounts stored in the given currency."""
        return sum(e.amount for e in self._entries_for_currency(currency_code))

    def category_distribution_for(self, currency_code: str) -> list[tuple[str, float, float]]:
        """Return merged ``(categoría, amount, share)`` rows for one currency."""
        buckets = self._bucket_categories(self._entries_for_currency(currency_code))
        return self._shares_from_buckets(buckets)

    def share_for_entry(self, entry: InvestmentEntry) -> float:
        """Return this line's share of totals in the same currency only."""
        peers = self._entries_for_currency(entry.currency_code)
        total = sum(e.amount for e in peers)
        if total <= 0:
            return 0.0
        return entry.amount / total

    def category_label_for(self, category_id: str) -> str:
        """Resolve a category title or a fallback label."""
        for cat in self._cats:
            if cat.category_id == category_id:
                return cat.name
        return "Sin categoría"

    def _entries_for_currency(self, currency_code: str) -> list[InvestmentEntry]:
        want = currency_code.strip().upper()
        return [e for e in self._ents if e.currency_code.upper() == want]

    def _bucket_categories(self, entries: list[InvestmentEntry]) -> dict[str, float]:
        out: dict[str, float] = {}
        for ent in entries:
            raw = self.category_label_for(ent.category_id)
            label = self._merge_case_insensitive_key(out, raw)
            out[label] = out.get(label, 0.0) + ent.amount
        return out

    def _merge_case_insensitive_key(self, buckets: dict[str, float], raw: str) -> str:
        for existing in buckets:
            if existing.lower() == raw.lower():
                return existing
        return raw

    def _shares_from_buckets(self, buckets: dict[str, float]) -> list[tuple[str, float, float]]:
        total = sum(buckets.values())
        if total <= 0:
            return []
        rows = []
        for label in sorted(buckets.keys(), key=str.lower):
            amt = buckets[label]
            rows.append((label, amt, amt / total))
        return rows
