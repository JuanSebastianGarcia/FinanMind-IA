"""Aggregates the full Dashboard snapshot in a single JSON dict."""

from __future__ import annotations

from finanmind.models.financial_dashboard_snapshot import FinancialDashboardSnapshot
from finanmind.services.financial_dashboard_service import FinancialDashboardService
from finanmind.ui.web.bridges.dashboard_distribution_rows_builder import (
    DashboardDistributionRowsBuilder,
)
from finanmind.ui.web.bridges.dashboard_health_rows_builder import (
    DashboardHealthRowsBuilder,
)
from finanmind.ui.web.bridges.dashboard_linked_series_builder import (
    DashboardLinkedSeriesBuilder,
)
from finanmind.ui.web.bridges.dashboard_month_options_builder import (
    DashboardMonthOptionsBuilder,
)
from finanmind.ui.web.bridges.dashboard_summary_builder import DashboardSummaryBuilder


class DashboardStateBuilder:
    """Builds the cross-domain dashboard payload consumed by the web UI."""

    @classmethod
    def build(cls, service: FinancialDashboardService, month_key: str) -> dict:
        """Return the dashboard snapshot serialised for the requested month."""
        snap = service.build_snapshot(month_key)
        return cls._serialize(snap)

    @classmethod
    def _serialize(cls, snap: FinancialDashboardSnapshot) -> dict:
        return {
            "month_key": snap.month_key,
            "month_label": snap.month_label,
            "month_options": DashboardMonthOptionsBuilder.build(snap.month_picker_keys),
            "summary": DashboardSummaryBuilder.build(snap),
            "card_spent_month_cop": snap.card_spent_month_cop,
            **cls._chart_blocks(snap),
            "health_rows": DashboardHealthRowsBuilder.build(snap.health_rows),
        }

    @classmethod
    def _chart_blocks(cls, snap: FinancialDashboardSnapshot) -> dict:
        return {
            "budget_distribution_rows": DashboardDistributionRowsBuilder.build(snap.budget_distribution_rows),
            "credit_category_rows": DashboardDistributionRowsBuilder.build(snap.credit_category_rows),
            "linked_pair_series": DashboardLinkedSeriesBuilder.build(snap.linked_pair_series),
        }
