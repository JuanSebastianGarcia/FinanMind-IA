import { DomBuilder } from "../core/dom_builder.js";
import { CurrencyFormatter } from "../format/currency_formatter.js";
import { PaymentsDates } from "./payments_dates.js";

export class PaymentsUpcoming {
  /** Right-hand list: unpaid bills overdue this month or due in the next 15 days. */
  constructor(host) {
    this._host = host;
    this._listEl = null;
  }

  mount() {
    const box = DomBuilder.el("div", "pay-box");
    const head = DomBuilder.el("div", "pay-box__head");
    head.appendChild(DomBuilder.el("div", "pay-box__title", "Próximos pagos"));
    head.appendChild(DomBuilder.el("span", "pay-box__hint", "Próximos 15 días"));
    box.appendChild(head);
    this._listEl = DomBuilder.el("div", "pay-next");
    box.appendChild(this._listEl);
    this._host.appendChild(box);
  }

  update(state) {
    this._listEl.innerHTML = "";
    if (!state.upcoming.length) {
      this._listEl.appendChild(DomBuilder.el("div", "pay-empty", "No hay pagos pendientes en los próximos 15 días."));
      return;
    }
    for (const row of state.upcoming) this._listEl.appendChild(this._buildItem(row));
  }

  _buildItem(row) {
    const item = DomBuilder.el("div", "pay-next__item");
    item.style.borderLeftColor = row.color;
    const date = DomBuilder.el("div", "pay-next__date");
    date.appendChild(DomBuilder.el("div", "pay-next__d", String(row.day)));
    date.appendChild(DomBuilder.el("div", "pay-next__m", PaymentsDates.shortMonth(row.due_on)));
    item.appendChild(date);
    const body = DomBuilder.el("div", "pay-next__body");
    body.appendChild(DomBuilder.el("div", "pay-next__name", row.name));
    const kind = row.value_kind === "variable" ? "Variable" : "Constante";
    body.appendChild(DomBuilder.el("div", "pay-next__meta", `${row.frequency_label} · ${kind}`));
    item.appendChild(body);
    item.appendChild(this._buildRight(row));
    return item;
  }

  _buildRight(row) {
    const right = DomBuilder.el("div");
    if (row.amount_cop === null || row.amount_cop === undefined) {
      const amt = DomBuilder.el("div", "pay-next__amt");
      amt.appendChild(DomBuilder.el("span", "pay-missing", "Sin valor"));
      right.appendChild(amt);
    } else {
      const prefix = row.amount_is_estimate ? "≈ " : "";
      right.appendChild(DomBuilder.el("div", "pay-next__amt", `${prefix}${CurrencyFormatter.formatCop(row.amount_cop)}`));
    }
    right.appendChild(this._buildWhen(row.days_left));
    return right;
  }

  _buildWhen(daysLeft) {
    if (daysLeft < 0) {
      const n = -daysLeft;
      return DomBuilder.el("div", "pay-next__when pay-next__when--late", `Vencido hace ${n} d`);
    }
    return DomBuilder.el("div", "pay-next__when", daysLeft === 0 ? "Hoy" : `En ${daysLeft} d`);
  }
}
