"""Human-readable month captions for dashboard copy."""


class MonthLabelFormatter:
    """Maps ``yyyy-mm`` strings to short Spanish titles."""

    _MONTHS = (
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    )

    @classmethod
    def spanish_month_year(cls, ym: str) -> str:
        """Return ``Mes AAAA`` when the key is well-formed."""
        if len(ym) < 7 or ym[4] != "-":
            return ym
        year = ym[:4]
        idx = int(ym[5:7], 10) - 1
        if not 0 <= idx < 12:
            return ym
        return f"{cls._MONTHS[idx].title()} {year}"
