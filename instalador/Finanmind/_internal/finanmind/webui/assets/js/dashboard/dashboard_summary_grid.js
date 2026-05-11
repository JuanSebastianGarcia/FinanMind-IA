import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";
import { UsdFormatter } from "../format/usd_formatter.js";

export class DashboardSummaryGrid {
  /** Five KPI cards: ingresos, saldo, deuda TC, inversión, superávit. */
  constructor(summary) {
    this._summary = summary || {};
  }

  build() {
    const grid = DomBuilder.el("div", "dash__summary");
    grid.appendChild(this._incomeCard());
    grid.appendChild(this._cashCard());
    grid.appendChild(this._debtCard());
    grid.appendChild(this._investmentCard());
    grid.appendChild(this._savingsCard());
    return grid;
  }

  _incomeCard() {
    return this._card(
      "Ingresos del mes",
      CurrencyFormatter.formatCop(this._summary.income_cop),
      "Ingresos registrados",
    );
  }

  _cashCard() {
    return this._card(
      "Saldo (asignaciones)",
      CurrencyFormatter.formatCop(this._summary.cash_remainder_cop),
      "Tras asignar presupuesto",
    );
  }

  _debtCard() {
    const usage = Number(this._summary.card_usage_pct) || 0;
    return this._card(
      "Deuda tarjetas",
      CurrencyFormatter.formatCop(this._summary.card_debt_total_cop),
      `Uso acumulado ~${Math.round(usage)}% del cupo`,
    );
  }

  _investmentCard() {
    return this._card(
      "Inversión",
      CurrencyFormatter.formatCop(this._summary.investment_cop),
      UsdFormatter.formatUsd(this._summary.investment_usd),
    );
  }

  _savingsCard() {
    return this._card(
      "Superávit estimado",
      CurrencyFormatter.formatCop(this._summary.savings_hint_cop),
      "Ingresos − asignaciones − TC",
    );
  }

  _card(caption, value, subtitle) {
    const card = DomBuilder.el("div", "dash__summary-card");
    card.appendChild(DomBuilder.el("div", "dash__summary-caption", caption));
    card.appendChild(DomBuilder.el("div", "dash__summary-value", value));
    card.appendChild(DomBuilder.el("div", "dash__summary-subtitle", subtitle));
    return card;
  }
}
