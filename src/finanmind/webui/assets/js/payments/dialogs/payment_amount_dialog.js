import { DomBuilder } from "../../core/dom_builder.js";
import { AmountParser } from "../../format/amount_parser.js";
import { CurrencyFormatter } from "../../format/currency_formatter.js";
import { PaymentsDates } from "../payments_dates.js";

export class PaymentAmountDialog {
  /** Registers the real value of a variable bill for one month. */
  constructor(modalHost, row) {
    this._host = modalHost;
    this._row = row;
    this._resolver = null;
    this._amountEl = null;
    this._paidEl = null;
    this._errorEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      window.queueMicrotask(() => this._amountEl.focus());
    });
  }

  _build() {
    const row = this._row;
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", `Registrar valor · ${row.name}`));
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(DomBuilder.el(
      "div", "modal__hint",
      `Factura de ${PaymentsDates.monthTitle(row.month).toLowerCase()} · vence el ${PaymentsDates.shortDay(row.due_on)}`,
    ));
    body.appendChild(this._buildAmountField());
    body.appendChild(this._buildPaidCheck());
    if (row.last_recorded) {
      body.appendChild(DomBuilder.el(
        "div", "modal__hint",
        `Último valor registrado: ${CurrencyFormatter.formatCop(row.last_recorded.amount_cop)} (${row.last_recorded.month_title.toLowerCase()}).`,
      ));
    }
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    modal.appendChild(body);
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cancelar", () => this._settle(null)));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Guardar", () => this._confirm()));
    modal.appendChild(actions);
    return modal;
  }

  _buildAmountField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Valor de la factura COP"));
    this._amountEl = DomBuilder.el("input", "field-input");
    this._amountEl.type = "text";
    this._amountEl.placeholder = "$ 0";
    const current = this._row.amount_is_estimate ? null : this._row.amount_cop;
    if (current) this._amountEl.value = CurrencyFormatter.formatCop(current);
    this._amountEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); this._confirm(); }
    });
    wrap.appendChild(this._amountEl);
    return wrap;
  }

  _buildPaidCheck() {
    const label = DomBuilder.el("label", "modal__checkbox-row");
    this._paidEl = DomBuilder.el("input");
    this._paidEl.type = "checkbox";
    this._paidEl.checked = this._row.status === "paid";
    this._paidEl.disabled = this._row.status === "paid";
    label.appendChild(this._paidEl);
    label.appendChild(DomBuilder.el("span", "", "Marcar también como pagado"));
    return label;
  }

  _confirm() {
    try {
      const amount = AmountParser.parse(this._amountEl.value);
      if (amount <= 0) throw new Error("El valor debe ser mayor que cero.");
      this._settle({ amount, markPaid: this._paidEl.checked && !this._paidEl.disabled });
    } catch (err) {
      this._errorEl.textContent = err.message === "Vacío" || err.message === "Sin dígitos"
        ? "Escribe el valor de la factura."
        : err.message;
    }
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
