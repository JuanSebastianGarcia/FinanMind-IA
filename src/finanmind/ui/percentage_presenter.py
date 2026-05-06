"""Percentage formatting for on-screen labels."""


class PercentagePresenter:
    """Builds Spanish-style percentage strings."""

    @classmethod
    def format_pct(cls, ratio: float) -> str:
        """Format ratio with one decimal place and comma separator."""
        body = f"{ratio:.1f}".replace(".", ",")
        return f"{body} %"
