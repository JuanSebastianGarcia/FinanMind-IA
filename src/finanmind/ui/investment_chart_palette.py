"""Stable accent sequence for investment donut slices."""


class InvestmentChartPalette:
    """Provides distinct colors that align with the Finanmind accent family."""

    _COLORS = (
        "#4f8ef7",
        "#22c55e",
        "#f59e0b",
        "#a855f7",
        "#ec4899",
        "#14b8a6",
        "#6366f1",
        "#eab308",
        "#0ea5e9",
        "#f97316",
    )

    @classmethod
    def color_at(cls, index: int) -> str:
        """Return a hex color for the slice index (wraps when needed)."""
        return cls._COLORS[index % len(cls._COLORS)]
