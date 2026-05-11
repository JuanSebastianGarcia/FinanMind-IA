import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";

export class CardSummaryStrip {
  /** Four-card strip with Deuda, Total abonado, Gasto del ciclo and Próxima cuota. */
  constructor(summary) {
    this._summary = summary || {};
  }

  build() {
    const strip = DomBuilder.el("div", "summary-strip");
    strip.appendChild(this._card("Deuda total", CurrencyFormatter.formatCop(this._summary.debt_cop), "primary"));
    strip.appendChild(this._card("Total abonado", CurrencyFormatter.formatCop(this._summary.paid_cop), "green"));
    strip.appendChild(this._card(
      "Gasto del ciclo",
      CurrencyFormatter.formatCop(this._summary.cycle_spend_cop),
      "amber",
    ));
    strip.appendChild(this._card("Próxima cuota", `Día ${this._summary.payment_due_day || "—"}`, "accent"));
    return strip;
  }

  _card(caption, value, tone) {
    const card = DomBuilder.el("div", "summary-strip__card");
    card.appendChild(DomBuilder.el("div", "summary-strip__caption", caption));
    card.appendChild(DomBuilder.el("div", `summary-strip__value summary-strip__value--${tone}`, value));
    return card;
  }
}
