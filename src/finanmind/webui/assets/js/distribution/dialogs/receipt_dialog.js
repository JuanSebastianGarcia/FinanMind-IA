import { DomBuilder } from "../../core/dom_builder.js";
import { AmountParser } from "../../format/amount_parser.js";

export class ReceiptDialog {
  /** Captures date + COP amount + memo for a new income receipt. */
  constructor(modalHost, defaultDay) {
    this._host = modalHost;
    this._defaultDay = defaultDay || ReceiptDialog._todayIso();
    this._resolver = null;
    this._dateEl = null;
    this._amountEl = null;
    this._memoEl = null;
    this._errorEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      window.queueMicrotask(() => this._focusAmount());
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Nuevo ingreso"));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildDateField());
    body.appendChild(this._buildAmountField());
    body.appendChild(this._buildMemoField());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildDateField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Fecha"));
    this._dateEl = this._buildInput("date", this._defaultDay);
    wrap.appendChild(this._dateEl);
    return wrap;
  }

  _buildAmountField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Importe COP"));
    this._amountEl = this._buildInput("text", "");
    wrap.appendChild(this._amountEl);
    return wrap;
  }

  _buildMemoField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Descripción (opcional)"));
    this._memoEl = this._buildInput("text", "");
    wrap.appendChild(this._memoEl);
    return wrap;
  }

  _buildInput(type, value) {
    const input = DomBuilder.el("input", "field-input");
    input.type = type;
    input.value = value;
    input.addEventListener("keydown", (event) => this._maybeSubmitOnEnter(event));
    return input;
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cancelar", () => this._settle(null)));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Guardar", () => this._confirm()));
    return actions;
  }

  _confirm() {
    try {
      this._settle(this._collectPayload());
    } catch (err) {
      this._errorEl.textContent = err.message;
    }
  }

  _collectPayload() {
    const day = (this._dateEl.value || "").trim();
    if (day === "") throw new Error("Selecciona una fecha.");
    const amount = AmountParser.parse(this._amountEl.value);
    const memo = (this._memoEl.value || "").trim();
    return { occurredOn: day, amount, memo };
  }

  _maybeSubmitOnEnter(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      this._confirm();
    }
  }

  _focusAmount() {
    if (this._amountEl) {
      this._amountEl.focus();
      this._amountEl.select();
    }
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }

  static _todayIso() {
    return new Date().toISOString().slice(0, 10);
  }
}
