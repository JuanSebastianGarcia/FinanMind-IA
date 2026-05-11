import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";
import { PercentFormatter } from "../format/percent_formatter.js";

export class CardTile {
  /** Renders a single dashboard tile with debt/available/usage bar and Abrir button. */
  constructor(tile, onOpen) {
    this._tile = tile;
    this._onOpen = onOpen;
  }

  build() {
    const node = DomBuilder.el("div", "tile");
    if (this._tile.color) node.style.borderColor = this._tile.color;
    node.appendChild(this._buildHead());
    node.appendChild(this._buildAmountRow("Deuda actual", this._tile.debt_cop, "tile__value--primary"));
    node.appendChild(this._buildAmountRow("Cupo disponible", this._tile.available_cop, "tile__value--muted"));
    node.appendChild(this._buildBar());
    node.appendChild(this._buildUsageCaption());
    node.appendChild(this._buildFooter());
    node.appendChild(this._buildAction());
    return node;
  }

  _buildHead() {
    const head = DomBuilder.el("div", "tile__head");
    head.appendChild(DomBuilder.el("div", "tile__name", this._tile.name));
    head.appendChild(DomBuilder.el("div", "tile__cut", `Cierre día ${this._tile.cut_day}`));
    return head;
  }

  _buildAmountRow(caption, amount, valueModifier) {
    const row = DomBuilder.el("div", "tile__row");
    row.appendChild(DomBuilder.el("div", "tile__caption", caption));
    row.appendChild(DomBuilder.el(
      "div",
      `tile__value ${valueModifier}`,
      CurrencyFormatter.formatCop(amount),
    ));
    return row;
  }

  _buildBar() {
    const wrap = DomBuilder.el("div", "tile__bar");
    const fill = DomBuilder.el("div", `tile__bar-fill tone-${this._tile.usage_tone || "ok"}`);
    fill.style.width = `${Math.round((this._tile.usage_ratio || 0) * 100)}%`;
    wrap.appendChild(fill);
    return wrap;
  }

  _buildUsageCaption() {
    const pct = (this._tile.usage_ratio || 0) * 100;
    const text = `${PercentFormatter.formatPct(pct)} del cupo usado`;
    return DomBuilder.el("div", "tile__usage-caption", text);
  }

  _buildFooter() {
    const limit = CurrencyFormatter.formatCop(this._tile.limit_cop);
    const text = `Pago día ${this._tile.payment_due_day}  ·  Cupo ${limit}`;
    return DomBuilder.el("div", "tile__footer", text);
  }

  _buildAction() {
    const wrap = DomBuilder.el("div", "tile__action");
    wrap.appendChild(DomBuilder.button("btn btn--primary", "Abrir tarjeta", () => this._onOpen(this._tile.card_id)));
    return wrap;
  }
}
