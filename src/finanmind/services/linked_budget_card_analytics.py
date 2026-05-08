"""Build trailing-month series for budget-label ↔ credit-card-category links."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

from finanmind.budget.book_service import BudgetBookService
from finanmind.models.budget_label import BudgetLabel
from finanmind.models.credit_card_category import CreditCardCategory
from finanmind.models.linked_pair_series import LinkedPairSeries
from finanmind.services.credit_card_service import CreditCardService


class LinkedBudgetCardAnalytics:
    """Collect monthly CC spending against expected budget per linked pair."""

    _FALLBACK_COLOR = "#4f8ef7"

    def __init__(self, book: BudgetBookService, cards: CreditCardService) -> None:
        self._book = book
        self._cards = cards

    def build_series(self, anchor_month: str, span_months: int = 12) -> list[LinkedPairSeries]:
        """Return one ``LinkedPairSeries`` per active label↔CC link."""
        months = self._month_window(anchor_month, span_months)
        out: list[LinkedPairSeries] = []
        for label, cat_path, cc_cat in self._iter_pairs():
            points = self._build_points(cc_cat.category_id, months)
            out.append(self._series_for(label, cat_path, cc_cat, points))
        out.sort(key=lambda s: s.label_path.lower())
        return out

    def _iter_pairs(self) -> Iterator[tuple[BudgetLabel, str, CreditCardCategory]]:
        ws = self._book.peek()
        for cat in ws.categories:
            for lbl in cat.labels:
                cc = self._cards.category_for_label(lbl.label_id)
                if cc is not None:
                    yield lbl, cat.title, cc

    def _series_for(
        self,
        lbl: BudgetLabel,
        cat_title: str,
        cc: CreditCardCategory,
        points: list[tuple[str, float]],
    ) -> LinkedPairSeries:
        card = self._cards.card_for_category(cc.category_id)
        card_name = card.name if card is not None else "Tarjeta"
        return LinkedPairSeries(
            pair_id=lbl.label_id,
            label_path=f"{cat_title} → {lbl.title}",
            card_category_path=f"{card_name} · {cc.title}",
            color=cc.color or self._FALLBACK_COLOR,
            expected_cop=lbl.amount_cop,
            points=points,
        )

    def _build_points(self, cc_category_id: str, months: list[str]) -> list[tuple[str, float]]:
        bucket = {m: 0.0 for m in months}
        for ex in self._cards.expenses_snapshot():
            if ex.category_id != cc_category_id:
                continue
            mk = ex.occurred_on[:7] if len(ex.occurred_on) >= 7 else ""
            if mk in bucket:
                bucket[mk] += ex.amount_cop
        return [(m, bucket[m]) for m in months]

    def _month_window(self, anchor: str, span: int) -> list[str]:
        year, month = self._parse_anchor(anchor)
        keys: list[str] = []
        for delta in range(span - 1, -1, -1):
            yy, mm = self._shift_months(year, month, -delta)
            keys.append(f"{yy:04d}-{mm:02d}")
        return keys

    def _parse_anchor(self, anchor: str) -> tuple[int, int]:
        try:
            return int(anchor[:4]), int(anchor[5:7])
        except (ValueError, TypeError):
            today = date.today()
            return today.year, today.month

    def _shift_months(self, year: int, month: int, delta: int) -> tuple[int, int]:
        idx = year * 12 + (month - 1) + delta
        return idx // 12, (idx % 12) + 1
