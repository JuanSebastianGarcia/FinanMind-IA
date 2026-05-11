import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";
import { PercentFormatter } from "../format/percent_formatter.js";

export class CardChart {
  /** Per-category bars with caption + amount + percent and a coloured fill. */
  constructor(rows) {
    this._rows = rows || [];
  }

  build() {
    const card = DomBuilder.el("div", "detail__card-static");
    if (this._rows.length === 0) {
      card.appendChild(DomBuilder.el("div", "detail__empty", "Sin gastos en el ciclo seleccionado."));
      return card;
    }
    const container = DomBuilder.el("div", "chart");
    for (const row of this._rows) container.appendChild(this._buildBar(row));
    card.appendChild(container);
    return card;
  }

  _buildBar(row) {
    const wrap = DomBuilder.el("div", "chart__bar-row");
    wrap.appendChild(this._buildHead(row));
    wrap.appendChild(this._buildTrack(row));
    return wrap;
  }

  _buildHead(row) {
    const head = DomBuilder.el("div", "chart__bar-head");
    head.appendChild(DomBuilder.el("div", "chart__bar-caption", row.caption));
    head.appendChild(DomBuilder.el("div", "chart__bar-meta", CardChart._metaFor(row)));
    return head;
  }

  _buildTrack(row) {
    const track = DomBuilder.el("div", "chart__bar");
    const fill = DomBuilder.el("div", "chart__bar-fill");
    fill.style.width = `${Math.round((row.ratio || 0) * 100)}%`;
    fill.style.background = row.color || "var(--accent)";
    track.appendChild(fill);
    return track;
  }

  static _metaFor(row) {
    const amount = CurrencyFormatter.formatCop(row.amount_cop);
    const pct = PercentFormatter.formatPct((row.ratio || 0) * 100);
    return `${amount} · ${pct}`;
  }
}
