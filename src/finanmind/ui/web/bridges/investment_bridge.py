"""High-level adapter from JavaScript to the investments CRUD service."""

from __future__ import annotations

from finanmind.services.investment_service import InvestmentService
from finanmind.ui.web.bridges.investment_state_builder import InvestmentStateBuilder


class InvestmentBridge:
    """Translates JS commands into ``InvestmentService`` calls."""

    def __init__(self, service: InvestmentService) -> None:
        self._service = service

    def get_state(self) -> dict:
        """Return the full Investments panel snapshot."""
        return InvestmentStateBuilder.build(self._service)

    def add_category(self, name: str) -> dict:
        """Persist a new category and return the refreshed state."""
        self._service.add_category(name)
        return self.get_state()

    def update_category(self, category_id: str, name: str) -> dict:
        """Rename an existing category and return the refreshed state."""
        self._service.update_category(category_id, name)
        return self.get_state()

    def delete_category(self, category_id: str) -> dict:
        """Remove a category and return the refreshed state."""
        self._service.delete_category(category_id)
        return self.get_state()

    def add_entry(
        self,
        category_id: str,
        amount: float,
        invested_date_iso: str,
        description: str,
        currency_code: str,
    ) -> dict:
        """Register a new holding and return the refreshed state."""
        self._service.add_entry(category_id, float(amount), invested_date_iso, description, currency_code)
        return self.get_state()

    def update_entry(
        self,
        investment_id: str,
        category_id: str,
        amount: float,
        invested_date_iso: str,
        description: str,
        currency_code: str,
    ) -> dict:
        """Edit one holding and return the refreshed state."""
        self._service.update_entry(
            investment_id, category_id, float(amount), invested_date_iso, description, currency_code,
        )
        return self.get_state()

    def delete_entry(self, investment_id: str) -> dict:
        """Drop one holding and return the refreshed state."""
        self._service.delete_entry(investment_id)
        return self.get_state()
