"""USD formatting for on-screen labels."""


class UsdAmountPresenter:
    """Builds USD strings with comma thousands and dot decimals."""

    @classmethod
    def format_usd(cls, amount: float) -> str:
        """Format positive amounts with two decimal places."""
        return f"USD {amount:,.2f}"
