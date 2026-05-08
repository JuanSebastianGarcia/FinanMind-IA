"""Compose cross-domain metrics for the financial dashboard."""

from __future__ import annotations

from datetime import date

from finanmind.budget.book_service import BudgetBookService
from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.models.credit_card_expense import CreditCardExpense
from finanmind.models.financial_dashboard_snapshot import FinancialDashboardSnapshot
from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.models.investment_entry import InvestmentEntry
from finanmind.services.credit_card_balance import CreditCardBalance
from finanmind.services.credit_card_service import CreditCardService
from finanmind.services.investment_portfolio_analytics import InvestmentPortfolioAnalytics
from finanmind.services.investment_service import InvestmentService
from finanmind.services.month_label_formatter import MonthLabelFormatter
from finanmind.services.monthly_distribution_service import MonthlyDistributionService


class FinancialDashboardService:
    """Builds one ``FinancialDashboardSnapshot`` per requested calendar month."""

    def __init__(
        self,
        book: BudgetBookService,
        ledger: MonthlyDistributionService,
        cards: CreditCardService,
        investments: InvestmentService,
    ) -> None:
        self._book = book
        self._ledger = ledger
        self._cards = cards
        self._invest = investments

    def build_snapshot(self, month_key: str) -> FinancialDashboardSnapshot:
        """Aggregate every dashboard block for ``yyyy-mm``."""
        mk = self._coerce_month(month_key)
        ws = self._book.peek()
        return self._snapshot_for(mk, ws)

    def _snapshot_for(self, mk: str, ws: BudgetWorkspace) -> FinancialDashboardSnapshot:
        inc, dist, rem = self._income_dist_rem(mk)
        cs, cd, cl = self._card_block(mk)
        ic, iu, mc, mu = self._investment_block(mk)
        ic_rows, iu_rows = self._investment_distribution_rows()
        hint = self._savings_hint(inc, dist, cs)
        bud = self._budget_category_rows(ws, mk)
        cc = self._credit_category_rows(mk)
        fl = self._flow_points(mk)
        keys = self._month_picker_keys(mk)
        lab = MonthLabelFormatter.spanish_month_year(mk)
        ins, heal = self._insight_health_bundle(mk, inc, dist, rem, cs, cd, cl, bud, cc)
        money = self._money_dict(mk, lab, inc, dist, rem, cs, cd, cl, hint)
        inv = self._invest_dict(ic, iu, mc, mu, ic_rows, iu_rows)
        tail = self._kw_tail(bud, cc, fl, ins, heal, keys)
        return FinancialDashboardSnapshot(**money, **inv, **tail)

    def _money_dict(
        self,
        mk: str,
        lab: str,
        inc: float,
        dist: float,
        rem: float,
        cs: float,
        cd: float,
        cl: float,
        hint: float,
    ) -> dict[str, object]:
        return {
            "month_key": mk,
            "month_label": lab,
            "income_cop": inc,
            "distribution_spent_cop": dist,
            "cash_remainder_cop": rem,
            "card_spent_month_cop": cs,
            "card_debt_total_cop": cd,
            "card_limit_total_cop": cl,
            "savings_hint_cop": hint,
        }

    def _invest_dict(
        self,
        ic: float,
        iu: float,
        mc: float,
        mu: float,
        ic_rows: list[tuple[str, float, float]],
        iu_rows: list[tuple[str, float, float]],
    ) -> dict[str, object]:
        return {
            "investment_cop": ic,
            "investment_usd": iu,
            "investment_month_cop": mc,
            "investment_month_usd": mu,
            "investment_rows_cop": ic_rows,
            "investment_rows_usd": iu_rows,
        }

    def _insight_health_bundle(
        self,
        mk: str,
        inc: float,
        dist: float,
        rem: float,
        cs: float,
        cd: float,
        cl: float,
        bud: list[tuple[str, float, float]],
        cc: list[tuple[str, float, float]],
    ) -> tuple[list[str], list[tuple[str, str]]]:
        ins = self._insights(mk, dist, cs, cd, bud, cc)
        heal = self._health(inc, dist, rem, cd, cl, cs)
        return ins, heal

    def _kw_tail(
        self,
        bud: list[tuple[str, float, float]],
        cc: list[tuple[str, float, float]],
        fl: list[tuple[str, float, float]],
        ins: list[str],
        heal: list[tuple[str, str]],
        keys: list[str],
    ) -> dict[str, object]:
        return {
            "budget_distribution_rows": bud,
            "credit_category_rows": cc,
            "flow_points": fl,
            "insights": ins,
            "health_rows": heal,
            "month_picker_keys": keys,
        }

    def _income_dist_rem(self, mk: str) -> tuple[float, float, float]:
        inc = self._month_income(mk)
        dist = self._month_distribution_total(mk)
        return inc, dist, inc - dist

    def _coerce_month(self, raw: str) -> str:
        token = raw.strip()
        if len(token) >= 7 and token[4] == "-":
            return token[:7]
        opts = self._ledger.known_month_prefixes()
        if opts:
            return opts[0]
        return self._today_ym()

    def _today_ym(self) -> str:
        today = date.today()
        return f"{today.year:04d}-{today.month:02d}"

    def _month_income(self, mk: str) -> float:
        return sum(r.amount_cop for r in self._ledger.receipts_in_month(mk))

    def _month_distribution_total(self, mk: str) -> float:
        return sum(self._ledger.monthly_spent_by_label(mk).values())

    def _card_block(self, mk: str) -> tuple[float, float, float]:
        spend = self._card_month_spend(mk)
        debt, lim = self._card_debt_and_limits()
        return spend, debt, lim

    def _card_month_spend(self, mk: str) -> float:
        total = 0.0
        for ex in self._cards.expenses_snapshot():
            if self._starts_month(ex.occurred_on, mk):
                total += ex.amount_cop
        return total

    def _starts_month(self, iso_day: str, mk: str) -> bool:
        return len(iso_day) >= 7 and iso_day[:7] == mk

    def _card_debt_and_limits(self) -> tuple[float, float]:
        debt = 0.0
        lim = 0.0
        for card in self._cards.cards_snapshot():
            exps = self._cards.expenses_for_card(card.card_id)
            pays = self._cards.payments_for_card(card.card_id)
            debt += CreditCardBalance.outstanding(exps, pays)
            lim += card.limit_cop
        return debt, lim

    def _investment_block(self, mk: str) -> tuple[float, float, float, float]:
        cats = self._invest.categories_snapshot()
        ents = self._invest.entries_snapshot()
        an = InvestmentPortfolioAnalytics(ents, cats)
        cop = an.total_for_currency(InvestmentCurrencyCode.COP)
        usd = an.total_for_currency(InvestmentCurrencyCode.USD)
        mc = self._entries_month_total(ents, mk, InvestmentCurrencyCode.COP)
        mu = self._entries_month_total(ents, mk, InvestmentCurrencyCode.USD)
        return cop, usd, mc, mu

    def _investment_distribution_rows(
        self,
    ) -> tuple[list[tuple[str, float, float]], list[tuple[str, float, float]]]:
        cats = self._invest.categories_snapshot()
        ents = self._invest.entries_snapshot()
        an = InvestmentPortfolioAnalytics(ents, cats)
        cop = an.category_distribution_for(InvestmentCurrencyCode.COP)
        usd = an.category_distribution_for(InvestmentCurrencyCode.USD)
        return cop, usd

    def _entries_month_total(self, ents: list[InvestmentEntry], mk: str, ccy: str) -> float:
        want = ccy.upper()
        total = 0.0
        for ent in ents:
            if len(ent.invested_date_iso) < 7:
                continue
            if ent.invested_date_iso[:7] != mk:
                continue
            if ent.currency_code.upper() == want:
                total += ent.amount
        return total

    def _savings_hint(self, inc: float, dist: float, card_spend: float) -> float:
        return inc - dist - card_spend

    def _budget_category_rows(self, ws: BudgetWorkspace, mk: str) -> list[tuple[str, float, float]]:
        by_label = self._ledger.monthly_spent_by_label(mk)
        buckets: dict[str, float] = {}
        for cat in ws.categories:
            part = 0.0
            for lbl in cat.labels:
                part += by_label.get(lbl.label_id, 0.0)
            if part > 0:
                buckets[cat.title] = part
        return self._rows_from_buckets(buckets)

    def _rows_from_buckets(self, buckets: dict[str, float]) -> list[tuple[str, float, float]]:
        total = sum(buckets.values())
        if total <= 0:
            return []
        rows: list[tuple[str, float, float]] = []
        for name in sorted(buckets.keys(), key=str.lower):
            amt = buckets[name]
            rows.append((name, amt, amt / total))
        return rows

    def _credit_category_rows(self, mk: str) -> list[tuple[str, float, float]]:
        buckets: dict[str, float] = {}
        for ex in self._cards.expenses_snapshot():
            if not self._starts_month(ex.occurred_on, mk):
                continue
            title = self._card_cat_title(ex)
            buckets[title] = buckets.get(title, 0.0) + ex.amount_cop
        return self._rows_from_buckets(buckets)

    def _card_cat_title(self, ex: CreditCardExpense) -> str:
        token = ex.category_id.strip()
        if token == "":
            return "Sin categoría"
        try:
            return self._cards.category_by_id(token).title
        except KeyError:
            return "Sin categoría"

    def _flow_points(self, anchor: str) -> list[tuple[str, float, float]]:
        keys = self._sorted_month_union(anchor)
        tail = keys[-6:] if len(keys) > 6 else keys
        pts: list[tuple[str, float, float]] = []
        for mk in tail:
            pts.append((mk, self._month_income(mk), self._month_distribution_total(mk)))
        return pts

    def _sorted_month_union(self, anchor: str) -> list[str]:
        bag: set[str] = set(self._ledger.known_month_prefixes())
        for ex in self._cards.expenses_snapshot():
            if len(ex.occurred_on) >= 7:
                bag.add(ex.occurred_on[:7])
        bag.add(anchor)
        return sorted(bag)

    def _month_picker_keys(self, selected: str) -> list[str]:
        keys = self._sorted_month_union(selected)
        return sorted(keys, reverse=True)

    def _prev_month(self, mk: str) -> str | None:
        y = int(mk[:4])
        m = int(mk[5:7])
        if m == 1:
            return f"{y - 1:04d}-12"
        return f"{y:04d}-{m - 1:02d}"

    def _insights(
        self,
        mk: str,
        dist: float,
        card_spend: float,
        debt: float,
        bud: list[tuple[str, float, float]],
        cc: list[tuple[str, float, float]],
    ) -> list[str]:
        lines: list[str] = []
        prev = self._prev_month(mk)
        if prev:
            self._append_dist_insight(lines, prev, dist)
            self._append_card_insight(lines, prev, card_spend)
        self._append_top_bucket(lines, bud, "presupuesto")
        self._append_top_bucket(lines, cc, "tarjeta")
        self._append_debt_insight(lines, debt)
        return lines[:6]

    def _append_dist_insight(self, lines: list[str], prev: str, dist: float) -> None:
        prior = self._month_distribution_total(prev)
        if prior <= 0:
            return
        delta = (dist - prior) / prior * 100.0
        if abs(delta) < 3:
            return
        verb = "subieron" if delta > 0 else "bajaron"
        prev_lab = MonthLabelFormatter.spanish_month_year(prev)
        lines.append(f"Tus asignaciones de presupuesto {verb} {abs(delta):.0f}% vs {prev_lab}.")

    def _append_card_insight(self, lines: list[str], prev: str, spend: float) -> None:
        prior = self._card_month_spend(prev)
        if prior <= 0:
            return
        delta = (spend - prior) / prior * 100.0
        if abs(delta) < 3:
            return
        verb = "aumentó" if delta > 0 else "bajó"
        lines.append(f"El gasto en tarjetas {verb} {abs(delta):.0f}% respecto al mes anterior.")

    def _append_top_bucket(self, lines: list[str], rows: list[tuple[str, float, float]], kind: str) -> None:
        if not rows:
            return
        top = max(rows, key=lambda r: r[1])
        share = top[2] * 100.0
        lines.append(f"En {kind}, «{top[0]}» concentra ~{share:.0f}% del gasto del mes.")

    def _append_debt_insight(self, lines: list[str], debt: float) -> None:
        if debt <= 0:
            lines.append("Sin saldo deudor acumulado en tarjetas registrado.")
            return
        rounded = int(round(debt))
        lines.append(f"Deuda acumulada en tarjetas: aprox. {rounded} COP.")

    def _health(
        self,
        inc: float,
        dist: float,
        rem: float,
        debt: float,
        lim: float,
        card_spend: float,
    ) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        rows.append(self._flow_health(rem, inc))
        rows.append(self._usage_health(debt, lim))
        rows.append(self._savings_health(inc, dist, card_spend))
        return rows

    def _flow_health(self, rem: float, inc: float) -> tuple[str, str]:
        if inc <= 0 and rem <= 0:
            return "Flujo del mes", "warn"
        if rem < 0:
            return "Flujo del mes", "bad"
        return "Flujo del mes", "ok"

    def _usage_health(self, debt: float, lim: float) -> tuple[str, str]:
        if lim <= 0:
            return "Uso de cupo", "ok"
        ratio = debt / lim
        if ratio >= 0.85:
            return "Uso de cupo", "bad"
        if ratio >= 0.55:
            return "Uso de cupo", "warn"
        return "Uso de cupo", "ok"

    def _savings_health(self, inc: float, dist: float, card_spend: float) -> tuple[str, str]:
        hint = self._savings_hint(inc, dist, card_spend)
        if hint >= 0:
            return "Superávit estimado", "ok"
        return "Superávit estimado", "warn"
