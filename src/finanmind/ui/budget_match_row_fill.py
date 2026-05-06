"""Background tint for budget summary rows: white / amber / green by distribution state."""


class BudgetMatchRowFill:
    """White when nothing spent, yellow when under budget, green when budget met or exceeded."""

    _AMBER = (251, 191, 36)
    _GREEN = (74, 222, 128)
    _WHITE = "#FFFFFF"

    @classmethod
    def hex(cls, spent: float, budget: float) -> str:
        """Return ``#RRGGBB``: unfilled row, under budget, or budget reached."""
        if spent <= 0:
            return cls._WHITE
        if budget <= 0:
            return cls._WHITE
        if spent < budget:
            return cls._soften(cls._AMBER)
        return cls._soften(cls._GREEN)

    @classmethod
    def _soften(cls, rgb: tuple[int, int, int]) -> str:
        """Blend toward white so labels stay readable."""
        weight = 0.52
        white = (255, 255, 255)
        blended = tuple(int(rgb[i] * weight + white[i] * (1.0 - weight)) for i in range(3))
        return f"#{blended[0]:02x}{blended[1]:02x}{blended[2]:02x}"
