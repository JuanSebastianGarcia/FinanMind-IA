"""Serialises ``(label, amount, share)`` donut rows adding a palette colour."""

from __future__ import annotations

from finanmind.ui.investment_chart_palette import InvestmentChartPalette


class DashboardDistributionRowsBuilder:
    """Maps each tuple from the snapshot to a colour-tagged JSON dict."""

    @classmethod
    def build(cls, rows: list[tuple[str, float, float]]) -> list[dict]:
        """Return one dict per slice in the same order, with a stable colour."""
        return [cls._row_to_dict(index, row) for index, row in enumerate(rows or [])]

    @classmethod
    def _row_to_dict(cls, index: int, row: tuple[str, float, float]) -> dict:
        label, amount, share = row
        return {
            "caption": label,
            "amount": amount,
            "share_ratio": share,
            "color": InvestmentChartPalette.color_at(index),
        }
