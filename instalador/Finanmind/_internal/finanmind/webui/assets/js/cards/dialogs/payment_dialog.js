import { AmountParser } from "../../format/amount_parser.js";
import { DomBuilder } from "../../core/dom_builder.js";

export class PaymentDialog {
  /** Collects date, amount and optional notes for a credit-card payment. */
  constructor(modalHost) {
    this._host = modalHost;
    this._resolver = null;
    this._dayEl = null;
    this._amountEl = null;
    this._notesEl = null;
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
    modal.appendChild(DomBuilder.el("div", "modal__title", "Registrar pago"));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildDateField());
    body.appendChild(this._buildAmountField());
    body.appendChild(this._buildNotesField());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildDateField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Fecha del pago"));
    this._dayEl = this._buildInput("date", PaymentDialog._todayIso());
    wrap.appendChild(this._dayEl);
    return wrap;
  }

  _buildAmountField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Valor pagado (COP)"));
    this._amountEl = this._buildInput("text", "");
    wrap.appendChild(this._amountEl);
    return wrap;
  }

  _buildNotesField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Observaciones (opcional)"));
    this._notesEl = this._buildInput("text", "");
    wrap.appendChild(this._notesEl);
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
    const day = (this._dayEl.value || "").trim();
    if (day === "") throw new Error("Selecciona una fecha.");
    const amount = AmountParser.parse(this._amountEl.value);
    const notes = (this._notesEl.value || "").trim();
    return { day, amount, notes };
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
