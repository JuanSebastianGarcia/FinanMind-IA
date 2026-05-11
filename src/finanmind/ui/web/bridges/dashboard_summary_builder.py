"""Builds the 5 KPI tiles used at the top of the dashboard."""

from __future__ import annotations

from finanmind.models.financial_dashboard_snapshot import FinancialDashboardSnapshot


class DashboardSummaryBuilder:
    """Serialises the dashboard's primary numeric strip into a JSON payload."""

    @classmethod
    def build(cls, snap: FinancialDashboardSnapshot) -> dict:
        """Return the totals and computed ratios consumed by the front-end grid."""
        return {
            "income_cop": snap.income_cop,
            "cash_remainder_cop": snap.cash_remainder_cop,
            "card_debt_total_cop": snap.card_debt_total_cop,
            "card_limit_total_cop": snap.card_limit_total_cop,
            "card_usage_pct": cls._usage_pct(snap.card_debt_total_cop, snap.card_limit_total_cop),
            "investment_cop": snap.investment_cop,
            "investment_usd": snap.investment_usd,
            "savings_hint_cop": snap.savings_hint_cop,
        }

    @classmethod
    def _usage_pct(cls, debt: float, limit: float) -> float:
        if limit <= 0:
            return 0.0
        return debt / limit * 100.0
