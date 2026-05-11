"""High-level adapter from JavaScript to the cross-domain dashboard service."""

from __future__ import annotations

from datetime import date

from finanmind.budget.book_service import BudgetBookService
from finanmind.services.credit_card_service import CreditCardService
from finanmind.services.financial_dashboard_service import FinancialDashboardService
from finanmind.services.investment_service import InvestmentService
from finanmind.services.monthly_distribution_service import MonthlyDistributionService
from finanmind.ui.web.bridges.dashboard_state_builder import DashboardStateBuilder


class DashboardBridge:
    """Translates JS dashboard requests into ``FinancialDashboardService`` calls."""

    def __init__(
        self,
        book: BudgetBookService,
        ledger: MonthlyDistributionService,
        cards: CreditCardService,
        investments: InvestmentService,
    ) -> None:
        self._service = FinancialDashboardService(book, ledger, cards, investments)

    def get_state(self, preferred_month: str = "") -> dict:
        """Return the full dashboard snapshot for the requested month."""
        return DashboardStateBuilder.build(self._service, self._resolve_month(preferred_month))

    @staticmethod
    def _resolve_month(preferred: str) -> str:
        token = (preferred or "").strip()
        if len(token) >= 7 and token[4] == "-":
            return token[:7]
        today = date.today()
        return f"{today.year:04d}-{today.month:02d}"
