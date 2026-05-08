"""User-defined investment bucket (name is what you invest in / “activo”)."""

from dataclasses import dataclass


@dataclass
class InvestmentCategory:
    """Named category reused when registering lines; same idea as “activo”."""

    category_id: str
    name: str
