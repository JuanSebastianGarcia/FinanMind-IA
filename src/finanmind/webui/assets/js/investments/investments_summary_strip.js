import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";
import { UsdFormatter } from "../format/usd_formatter.js";

export class InvestmentsSummaryStrip {
  /** Renders 4 chips: total COP, total USD, count, category count. */
  constructor(summary) {
    this._summary = summary || {};
  }

  build() {
    const row = DomBuilder.el("div", "invest-summary");
    row.appendChild(this._buildCard("Total en COP", CurrencyFormatter.formatCop(this._summary.total_cop || 0)));
    row.appendChild(this._buildCard("Total en USD", UsdFormatter.formatUsd(this._summary.total_usd || 0)));
    row.appendChild(this._buildCard("Inversiones", String(this._summary.entry_count || 0)));
    row.appendChild(this._buildCard("Categorías", String(this._summary.category_count || 0)));
    return row;
  }

  _buildCard(caption, value) {
    const card = DomBuilder.el("div", "invest-summary__card");
    card.appendChild(DomBuilder.el("div", "invest-summary__caption", caption));
    card.appendChild(DomBuilder.el("div", "invest-summary__value", value));
    return card;
  }
}
