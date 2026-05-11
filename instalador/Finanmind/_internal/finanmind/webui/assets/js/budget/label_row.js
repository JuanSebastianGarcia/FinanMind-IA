import { DomBuilder } from "../core/dom_builder.js";
import { CurrencyFormatter } from "../format/currency_formatter.js";
import { PercentFormatter } from "../format/percent_formatter.js";

export class LabelRow {
  /** Renders one label inside a category card: name, mini-bar, amount, actions. */
  constructor(categoryId, label, salary, accent, handlers) {
    this._categoryId = categoryId;
    this._label = label;
    this._salary = salary;
    this._accent = accent;
    this._handlers = handlers;
  }

  build() {
    const row = DomBuilder.el("div", "label-row");
    row.appendChild(this._buildMiniBar());
    row.appendChild(this._buildNameBlock());
    row.appendChild(DomBuilder.el("div", "label-row__spacer"));
    row.appendChild(this._buildAmount());
    row.appendChild(this._buildActions());
    return row;
  }

  _buildNameBlock() {
    const block = DomBuilder.el("div", "label-row__name-block");
    block.appendChild(DomBuilder.el("div", "label-row__name", this._label.title));
    if (this._label.link_caption) {
      block.appendChild(DomBuilder.el("div", "label-row__link", this._label.link_caption));
    }
    return block;
  }

  _buildMiniBar() {
    const bar = DomBuilder.el("div", "label-row__bar");
    const fill = DomBuilder.el("div", "label-row__bar-fill");
    fill.style.width = `${LabelRow._fillPx(this._label.amount_cop, this._salary)}px`;
    fill.style.background = this._accent;
    bar.appendChild(fill);
    return bar;
  }

  _buildAmount() {
    const amount = CurrencyFormatter.formatCop(this._label.amount_cop);
    const share = PercentFormatter.formatPct(this._label.percent_of_salary);
    return DomBuilder.el("div", "label-row__amount", `${amount} · ${share}`);
  }

  _buildActions() {
    const strip = DomBuilder.el("div", "label-row__actions");
    strip.appendChild(DomBuilder.button("icon-btn", "✎", () => this._fireEdit()));
    strip.appendChild(DomBuilder.button("icon-btn icon-btn--danger", "✕", () => this._fireDelete()));
    return strip;
  }

  _fireEdit() {
    this._handlers.onEditLabel(this._categoryId, this._label);
  }

  _fireDelete() {
    this._handlers.onDeleteLabel(this._categoryId, this._label.id);
  }

  static _fillPx(amount, salary) {
    if (!salary || salary <= 0) return 4;
    const share = Math.min(1, (amount / salary) * 5);
    return Math.max(4, Math.round(32 * share));
  }
}
