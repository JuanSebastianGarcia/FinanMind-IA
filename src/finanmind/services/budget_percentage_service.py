"""Derives category totals versus a salary baseline."""


class BudgetPercentageService:
    """Computes each budget group's share of a monthly salary reference."""

    def ratio(self, amounts: list[float], salary: float) -> float:
        """Return percent share for one list of COP amounts."""
        total = sum(amounts)
        return (total / salary * 100.0) if salary > 0 else 0.0

    def summarize(
        self,
        salary: float,
        groups: list[tuple[str, list[float]]],
    ) -> list[tuple[str, float]]:
        """Return ordered pairs of category title and percent of salary."""
        payload = []
        for title, amounts in groups:
            payload.append((title, self.ratio(amounts, salary)))
        return payload

    def map_by_category_id(
        self,
        salary: float,
        pairs: list[tuple[str, list[float]]],
    ) -> dict[str, float]:
        """Map category identifiers to percent shares."""
        mapping: dict[str, float] = {}
        for cid, amounts in pairs:
            mapping[cid] = self.ratio(amounts, salary)
        return mapping
