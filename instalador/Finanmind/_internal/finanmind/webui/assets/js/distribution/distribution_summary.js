import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";

export class DistributionSummary {
  /** Renders one row per budget label with Ppto / Dist / Diff and tonal diff color. */
  constructor(host) {
    this._host = host;
    this._scroll = null;
  }

  mount() {
    const column = DomBuilder.el("div", "distribution__column");
    column.appendChild(DomBuilder.el("div", "distribution__column-title", "Resumen del mes vs presupuesto"));
    this._scroll = DomBuilder.el("div", "distribution__card-scroll");
    column.appendChild(this._scroll);
    this._host.appendChild(column);
  }

  update(rows) {
    this._scroll.innerHTML = "";
    const container = DomBuilder.el("div", "summary");
    container.appendChild(this._buildHeader());
    if (!rows || rows.length === 0) {
      container.appendChild(DomBuilder.el("div", "summary__empty", "Sin etiquetas en el presupuesto."));
    } else {
      for (const row of rows) container.appendChild(this._buildRow(row));
    }
    this._scroll.appendChild(container);
  }

  _buildHeader() {
    const head = DomBuilder.el("div", "summary__header");
    head.appendChild(DomBuilder.el("div", "summary__header-swatch-space"));
    head.appendChild(DomBuilder.el("div", "summary__header-title", "Etiqueta"));
    head.appendChild(DomBuilder.el("div", "summary__header-spacer"));
    head.appendChild(DomBuilder.el("div", "summary__header-money", "Ppto."));
    head.appendChild(DomBuilder.el("div", "summary__header-money", "Dist."));
    head.appendChild(DomBuilder.el("div", "summary__header-money", "Diff."));
    return head;
  }

  _buildRow(row) {
    const node = DomBuilder.el("div", "summary__row");
    node.appendChild(this._buildSwatch(row.color));
    node.appendChild(DomBuilder.el("div", "summary__title", row.title));
    node.appendChild(DomBuilder.el("div", "summary__spacer"));
    node.appendChild(this._moneyCell(row.budget_cop, "summary__money--budget"));
    node.appendChild(this._moneyCell(row.spent_cop, "summary__money--spent"));
    node.appendChild(this._diffCell(row.diff_cop, row.tone));
    return node;
  }

  _buildSwatch(color) {
    const swatch = DomBuilder.el("div", "summary__swatch");
    swatch.style.background = color || "var(--border)";
    return swatch;
  }

  _moneyCell(amount, modifier) {
    const cell = DomBuilder.el("div", `summary__money ${modifier}`, CurrencyFormatter.formatCop(amount));
    return cell;
  }

  _diffCell(amount, tone) {
    const cell = DomBuilder.el("div", `summary__money summary__money--diff tone-${tone || "neutral"}`,
      CurrencyFormatter.formatCop(amount));
    return cell;
  }
}
