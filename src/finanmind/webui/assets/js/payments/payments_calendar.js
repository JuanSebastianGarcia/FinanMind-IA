import { DomBuilder } from "../core/dom_builder.js";

export class PaymentsCalendar {
  /** Monday-first month grid with one chip per bill, plus month navigation. */
  constructor(host, handlers) {
    this._host = host;
    this._handlers = handlers;
    this._titleEl = null;
    this._gridEl = null;
  }

  mount() {
    const box = DomBuilder.el("div", "pay-box");
    box.appendChild(this._buildHead());
    this._gridEl = DomBuilder.el("div", "pay-grid");
    box.appendChild(this._gridEl);
    this._host.appendChild(box);
  }

  update(state) {
    this._titleEl.textContent = state.month_title;
    this._gridEl.innerHTML = "";
    for (const dow of ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]) {
      this._gridEl.appendChild(DomBuilder.el("div", "pay-grid__dow", dow));
    }
    for (const week of state.weeks) {
      for (const cell of week) this._gridEl.appendChild(this._buildDay(cell));
    }
  }

  _buildHead() {
    const head = DomBuilder.el("div", "pay-box__head");
    const nav = DomBuilder.el("div", "pay-month");
    nav.appendChild(DomBuilder.button("icon-btn", "‹", () => this._handlers.onShift(-1)));
    this._titleEl = DomBuilder.el("div", "pay-month__name", "");
    nav.appendChild(this._titleEl);
    nav.appendChild(DomBuilder.button("icon-btn", "›", () => this._handlers.onShift(1)));
    head.appendChild(nav);
    head.appendChild(DomBuilder.button("btn btn--outline pay-today-btn", "Hoy", () => this._handlers.onToday()));
    return head;
  }

  _buildDay(cell) {
    let cls = "pay-day";
    if (!cell.in_month) cls += " pay-day--out";
    if (cell.is_today) cls += " pay-day--today";
    const day = DomBuilder.el("div", cls);
    day.appendChild(DomBuilder.el("div", "pay-day__num", String(cell.day)));
    for (const item of cell.items) day.appendChild(this._buildChip(item));
    return day;
  }

  _buildChip(item) {
    let cls = "pay-chip";
    if (item.status === "paid") cls += " pay-chip--paid";
    if (item.status === "late") cls += " pay-chip--late";
    const prefix = item.status === "paid" ? "✓ " : "";
    const chip = DomBuilder.el("div", cls, `${prefix}${item.name}`);
    chip.style.borderLeftColor = item.color;
    chip.title = item.name;
    return chip;
  }
}
