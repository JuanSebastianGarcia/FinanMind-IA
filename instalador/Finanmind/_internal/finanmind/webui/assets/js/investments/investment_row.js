import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";
import { PercentFormatter } from "../format/percent_formatter.js";
import { UsdFormatter } from "../format/usd_formatter.js";

export class InvestmentRow {
  /** Renders one holding card (header, currency badge, amount, date, optional note). */
  constructor(entry, handlers) {
    this._entry = entry;
    this._handlers = handlers || {};
  }

  build() {
    const card = DomBuilder.el("div", "invest-card");
    card.appendChild(this._buildHeader());
    card.appendChild(this._buildMeta());
    if ((this._entry.description || "").trim() !== "") {
      card.appendChild(this._buildNote());
    }
    card.appendChild(this._buildActions());
    return card;
  }

  _buildHeader() {
    const head = DomBuilder.el("div", "invest-card__head");
    head.appendChild(DomBuilder.el("div", "invest-card__title", this._entry.category_caption || "Sin categoría"));
    const sharePct = (this._entry.share_ratio || 0) * 100;
    head.appendChild(DomBuilder.el("div", "invest-card__share", PercentFormatter.formatPct(sharePct)));
    return head;
  }

  _buildMeta() {
    const meta = DomBuilder.el("div", "invest-card__meta");
    meta.appendChild(DomBuilder.el("div", "invest-card__currency", (this._entry.currency_code || "COP").toUpperCase()));
    meta.appendChild(DomBuilder.el("div", "invest-card__amount", this._formatAmount()));
    meta.appendChild(DomBuilder.el("div", "invest-card__date", this._entry.invested_date_iso || ""));
    return meta;
  }

  _formatAmount() {
    if ((this._entry.currency_code || "COP").toUpperCase() === "USD") {
      return UsdFormatter.formatUsd(this._entry.amount);
    }
    return CurrencyFormatter.formatCop(this._entry.amount);
  }

  _buildNote() {
    const raw = this._entry.description.trim();
    const clip = raw.length <= 220 ? raw : `${raw.slice(0, 217)}…`;
    return DomBuilder.el("div", "invest-card__note", clip);
  }

  _buildActions() {
    const wrap = DomBuilder.el("div", "invest-card__actions");
    wrap.appendChild(DomBuilder.button("invest-card__btn", "Editar", () => this._fire("onEdit")));
    wrap.appendChild(DomBuilder.button("invest-card__btn invest-card__btn--danger", "Eliminar", () => this._fire("onDelete")));
    return wrap;
  }

  _fire(name) {
    const handler = this._handlers[name];
    if (typeof handler === "function") handler(this._entry.investment_id);
  }
}
