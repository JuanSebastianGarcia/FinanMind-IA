import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";
import { PercentFormatter } from "../format/percent_formatter.js";
import { UsdFormatter } from "../format/usd_formatter.js";

export class InvestmentsLegendPanel {
  /** Color-keyed legend rows aligned with the donut slices. */
  constructor(rows, currencyCode) {
    this._rows = Array.isArray(rows) ? rows : [];
    this._currency = (currencyCode || "COP").toUpperCase();
  }

  build() {
    const legend = DomBuilder.el("div", "invest-legend");
    if (this._rows.length === 0) {
      legend.appendChild(this._buildEmpty());
      return legend;
    }
    for (const row of this._rows) legend.appendChild(this._buildRow(row));
    return legend;
  }

  _buildEmpty() {
    return DomBuilder.el("div", "invest-donut__hint", "Sin datos para esta moneda");
  }

  _buildRow(row) {
    const line = DomBuilder.el("div", "invest-legend__row");
    line.appendChild(this._buildDot(row.color));
    line.appendChild(DomBuilder.el("div", "invest-legend__label", row.caption || ""));
    line.appendChild(this._buildValues(row));
    return line;
  }

  _buildDot(color) {
    const dot = DomBuilder.el("div", "invest-legend__dot");
    dot.style.background = color || "var(--accent)";
    return dot;
  }

  _buildValues(row) {
    const col = DomBuilder.el("div", "invest-legend__values");
    const pct = (row.share_ratio || 0) * 100;
    col.appendChild(DomBuilder.el("div", "invest-legend__pct", PercentFormatter.formatPct(pct)));
    col.appendChild(DomBuilder.el("div", "invest-legend__amount", this._formatAmount(row.amount)));
    return col;
  }

  _formatAmount(amount) {
    if (this._currency === "USD") return UsdFormatter.formatUsd(amount);
    return CurrencyFormatter.formatCop(amount);
  }
}
