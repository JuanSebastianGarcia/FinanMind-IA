"""Colombian peso (COP) formatting for on-screen labels."""


class CurrencyPresenter:
    """Builds COP strings: peso symbol and dot-separated thousands."""

    @classmethod
    def format_cop(cls, amount: float) -> str:
        """Format whole pesos with dot grouping (locale habit in Colombia)."""
        pesos = int(round(amount))
        body = cls._dot_group(abs(pesos))
        signed = f"-{body}" if pesos < 0 else body
        return f"$ {signed}"

    @classmethod
    def _dot_group(cls, value: int) -> str:
        text = str(value)
        blocks = []
        while text:
            blocks.append(text[-3:])
            text = text[:-3]
        return ".".join(reversed(blocks))
