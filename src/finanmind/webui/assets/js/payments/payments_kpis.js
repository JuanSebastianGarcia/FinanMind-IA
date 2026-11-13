import { DomBuilder } from "../core/dom_builder.js";
import { CurrencyFormatter } from "../format/currency_formatter.js";
import { PaymentsDates } from "./payments_dates.js";

export class PaymentsKpis {
  /** Four tiles: month total, paid, pending and next payment. */
  constructor(host) {
    this._host = host;
    this._root = null;
  }

  mount() {
    this._root = DomBuilder.el("div", "pay-kpis");
    this._host.appendChild(this._root);
  }

  update(state) {
    const s = state.summary;
    this._root.innerHTML = "";
    this._root.appendChild(this._tile("Total del mes", CurrencyFormatter.formatCop(s.total_cop), this._totalSub(s)));
    this._root.appendChild(this._paidTile(s));
    this._root.appendChild(this._pendingTile(s));
    this._root.appendChild(this._nextTile(s.next_payment));
  }

  _totalSub(s) {
    const base = `${s.count} pago${s.count === 1 ? "" : "s"}`;
    if (!s.missing_count) return base;
    return `${base} · ${s.missing_count} variable${s.missing_count === 1 ? "" : "s"} sin valor`;
  }

  _paidTile(s) {
    const tile = this._tile("Pagado", CurrencyFormatter.formatCop(s.paid_cop));
    const bar = DomBuilder.el("div", "pay-kpi__bar");
    const fill = DomBuilder.el("div", "pay-kpi__bar-fill");
    fill.style.width = `${Math.round((s.paid_ratio || 0) * 100)}%`;
    bar.appendChild(fill);
    tile.appendChild(bar);
    return tile;
  }

  _pendingTile(s) {
    const late = s.overdue_count;
    const text = late ? `${late} vencido${late === 1 ? "" : "s"}` : "Nada vencido";
    const tile = this._tile("Pendiente", CurrencyFormatter.formatCop(s.pending_cop), text);
    if (late) tile.lastChild.classList.add("pay-kpi__sub--alert");
    return tile;
  }

  _nextTile(next) {
    if (!next) return this._tile("Próximo pago", "—", "Nada pendiente en 15 días");
    const when = next.days_left === 0 ? "Hoy" : `En ${next.days_left} día${next.days_left === 1 ? "" : "s"}`;
    return this._tile("Próximo pago", next.name, `${when} · ${PaymentsDates.shortDay(next.due_on)}`);
  }

  _tile(label, value, sub) {
    const tile = DomBuilder.el("div", "pay-kpi");
    tile.appendChild(DomBuilder.el("div", "pay-kpi__label", label));
    const v = DomBuilder.el("div", "pay-kpi__value", value);
    v.title = value;
    tile.appendChild(v);
    if (sub) tile.appendChild(DomBuilder.el("div", "pay-kpi__sub", sub));
    return tile;
  }
}
