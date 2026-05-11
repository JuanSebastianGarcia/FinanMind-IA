import { CurrencyFormatter } from "../../format/currency_formatter.js";
import { DomBuilder } from "../../core/dom_builder.js";

export class BudgetReviewRecommendationRow {
  /** One AI recommendation: heading, delta badge, current vs suggested, reason. */
  constructor(rec) {
    this._rec = rec || {};
  }

  build() {
    const card = DomBuilder.el("div", "rev-rec");
    card.appendChild(this._buildHeading());
    card.appendChild(this._buildAmounts());
    card.appendChild(this._buildReason());
    return card;
  }

  _buildHeading() {
    const row = DomBuilder.el("div", "rev-rec__head");
    row.appendChild(DomBuilder.el("div", "rev-rec__title", this._titleText()));
    row.appendChild(this._buildDelta());
    return row;
  }

  _titleText() {
    const cat = this._rec.category_title || "";
    const lbl = this._rec.label_title || "";
    return `${cat} · ${lbl}`;
  }

  _buildDelta() {
    const delta = Number(this._rec.delta_cop) || 0;
    const sign = delta > 0 ? "+" : "";
    const text = `${sign}${CurrencyFormatter.formatCop(delta)}`;
    return DomBuilder.el("div", `rev-rec__delta ${BudgetReviewRecommendationRow._deltaClass(delta)}`, text);
  }

  static _deltaClass(delta) {
    if (delta < -0.5) return "rev-rec__delta--down";
    if (delta > 0.5) return "rev-rec__delta--up";
    return "rev-rec__delta--flat";
  }

  _buildAmounts() {
    const row = DomBuilder.el("div", "rev-rec__amounts");
    row.appendChild(this._amountBlock("Actual", this._rec.current_amount_cop, "rev-rec__current"));
    row.appendChild(this._amountBlock("Sugerido", this._rec.suggested_amount_cop, "rev-rec__suggested"));
    return row;
  }

  _amountBlock(caption, amount, valueClass) {
    const block = DomBuilder.el("div", "rev-rec__amount");
    block.appendChild(DomBuilder.el("div", "rev-rec__amount-caption", caption));
    block.appendChild(DomBuilder.el("div", `rev-rec__amount-value ${valueClass}`, CurrencyFormatter.formatCop(amount)));
    return block;
  }

  _buildReason() {
    const reason = (this._rec.reason || "").trim() || "Sin justificación adicional.";
    return DomBuilder.el("div", "rev-rec__reason", reason);
  }
}
