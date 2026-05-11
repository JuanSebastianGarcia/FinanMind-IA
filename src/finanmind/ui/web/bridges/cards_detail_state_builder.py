"""Composes the entire detail snapshot for a single credit card view."""

from __future__ import annotations

from finanmind.budget.book_service import BudgetBookService
from finanmind.services.credit_card_service import CreditCardService
from finanmind.ui.web.bridges.cards_categories_builder import CardsCategoriesBuilder
from finanmind.ui.web.bridges.cards_chart_builder import CardsChartBuilder
from finanmind.ui.web.bridges.cards_cycles_resolver import CardsCyclesResolver
from finanmind.ui.web.bridges.cards_expenses_builder import CardsExpensesBuilder
from finanmind.ui.web.bridges.cards_payments_builder import CardsPaymentsBuilder
from finanmind.ui.web.bridges.cards_summary_builder import CardsSummaryBuilder


class CardsDetailStateBuilder:
    """Aggregates card header, summary, cycles, expenses, categories, payments and chart."""

    @classmethod
    def build(
        cls,
        service: CreditCardService,
        book: BudgetBookService | None,
        card_id: str,
        preferred_cycle: str,
    ) -> dict:
        """Return the full detail snapshot honoring the JS-provided cycle hint."""
        card = service.card_by_id(card_id)
        cycle_keys = CardsCyclesResolver.list_cycle_keys(service, card)
        active_cycle = CardsCyclesResolver.coerce_active(cycle_keys, preferred_cycle)
        start, end = CardsCyclesResolver.range_for(card, active_cycle)
        cycle_expenses = service.expenses_in_range(card_id, start, end)
        return cls._assemble(service, book, card, cycle_keys, active_cycle, start, end, cycle_expenses)

    @classmethod
    def _assemble(cls, service, book, card, cycle_keys, active_cycle, start, end, cycle_expenses):
        return {
            "card": cls._card_payload(card),
            "cycles": cycle_keys,
            "active_cycle": active_cycle,
            "cycle_range": {"start": start, "end": end},
            "summary": CardsSummaryBuilder.build(service, card, cycle_expenses),
            "expenses": CardsExpensesBuilder.build(service, card.card_id, cycle_expenses),
            "categories": CardsCategoriesBuilder.build(service, card.card_id, book),
            "payments": CardsPaymentsBuilder.build(service, card.card_id),
            "chart": CardsChartBuilder.build(service, card.card_id, cycle_expenses),
        }

    @classmethod
    def _card_payload(cls, card) -> dict:
        return {
            "card_id": card.card_id,
            "name": card.name,
            "color": card.color,
            "limit_cop": card.limit_cop,
            "cut_day": card.cut_day,
            "payment_due_day": card.payment_due_day,
        }
