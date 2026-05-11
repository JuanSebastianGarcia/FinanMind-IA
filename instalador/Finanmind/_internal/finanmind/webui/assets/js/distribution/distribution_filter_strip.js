import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";

export class DistributionFilterStrip {
  /** Month + receipt selectors, remainder badge, and Registrar distribución button. */
  constructor(host, handlers) {
    this._host = host;
    this._handlers = handlers;
    this._monthSelect = null;
    this._receiptSelect = null;
    this._remainder = null;
  }

  mount() {
    const bar = DomBuilder.el("div", "filter-strip");
    bar.appendChild(DomBuilder.el("span", "filter-strip__caption", "Mes"));
    bar.appendChild(this._buildMonthSelect());
    bar.appendChild(DomBuilder.el("span", "filter-strip__caption", "Ingreso"));
    bar.appendChild(this._buildReceiptSelect());
    bar.appendChild(this._buildRemainder());
    bar.appendChild(DomBuilder.el("div", "filter-strip__spacer"));
    bar.appendChild(this._registerButton());
    this._host.appendChild(bar);
  }

  update(state) {
    this._refreshMonths(state.months, state.active_month);
    this._refreshReceipts(state.receipts, state.active_receipt_id);
    this._refreshRemainder(state.active_receipt_id, state.remainder_cop);
  }

  _buildMonthSelect() {
    const sel = DomBuilder.el("select", "filter-strip__select");
    sel.addEventListener("change", () => this._handlers.onMonthChange(sel.value));
    this._monthSelect = sel;
    return sel;
  }

  _buildReceiptSelect() {
    const sel = DomBuilder.el("select", "filter-strip__select");
    sel.addEventListener("change", () => this._handlers.onReceiptChange(sel.value));
    this._receiptSelect = sel;
    return sel;
  }

  _buildRemainder() {
    this._remainder = DomBuilder.el("span", "filter-strip__remainder", "Selecciona un ingreso");
    return this._remainder;
  }

  _registerButton() {
    return DomBuilder.button("btn btn--primary", "Registrar distribución", () => this._handlers.onNewLine());
  }

  _refreshMonths(months, activeMonth) {
    this._fillSelectWithStrings(this._monthSelect, months, activeMonth);
  }

  _refreshReceipts(receipts, activeReceiptId) {
    this._receiptSelect.innerHTML = "";
    if (!receipts || receipts.length === 0) {
      this._appendPlaceholderOption(this._receiptSelect, "Sin ingresos este mes");
      this._receiptSelect.disabled = true;
      return;
    }
    this._receiptSelect.disabled = false;
    for (const rec of receipts) {
      this._receiptSelect.appendChild(this._buildReceiptOption(rec, activeReceiptId));
    }
  }

  _buildReceiptOption(receipt, activeReceiptId) {
    const opt = DomBuilder.el("option", null, DistributionFilterStrip._receiptCaption(receipt));
    opt.value = receipt.receipt_id;
    if (receipt.receipt_id === activeReceiptId) opt.selected = true;
    return opt;
  }

  _refreshRemainder(activeReceiptId, remainderCop) {
    this._remainder.classList.remove("filter-strip__remainder--negative", "filter-strip__remainder--positive");
    if (!activeReceiptId || remainderCop === null || remainderCop === undefined) {
      this._remainder.textContent = "Selecciona un ingreso";
      return;
    }
    const label = `Por distribuir: ${CurrencyFormatter.formatCop(remainderCop)}`;
    this._remainder.textContent = label;
    const klass = remainderCop < 0 ? "filter-strip__remainder--negative" : "filter-strip__remainder--positive";
    this._remainder.classList.add(klass);
  }

  _fillSelectWithStrings(select, values, active) {
    select.innerHTML = "";
    for (const value of values) {
      const opt = DomBuilder.el("option", null, value);
      opt.value = value;
      if (value === active) opt.selected = true;
      select.appendChild(opt);
    }
  }

  _appendPlaceholderOption(select, text) {
    const opt = DomBuilder.el("option", null, text);
    opt.value = "";
    select.appendChild(opt);
  }

  static _receiptCaption(receipt) {
    const memo = (receipt.memo || "").trim();
    const suffix = memo ? ` · ${memo}` : "";
    return `${receipt.occurred_on}${suffix} · ${CurrencyFormatter.formatCop(receipt.amount_cop)}`;
  }
}
