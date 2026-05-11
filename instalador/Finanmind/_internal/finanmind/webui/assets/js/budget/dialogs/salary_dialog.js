import { DomBuilder } from "../../core/dom_builder.js";
import { AmountParser } from "../../format/amount_parser.js";

export class SalaryDialog {
  /** Single-field dialog capturing the monthly COP salary baseline. */
  constructor(modalHost, currentCop) {
    this._host = modalHost;
    this._currentCop = Number(currentCop) || 0;
    this._resolver = null;
    this._inputEl = null;
    this._errorEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      const node = this._build();
      this._host.open(node, () => this._settle(null));
      window.queueMicrotask(() => this._focusInput());
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Salario mensual"));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(DomBuilder.el("div", "modal__field-label", "Salario actual (COP, solo números)"));
    this._inputEl = this._buildInput();
    body.appendChild(this._inputEl);
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildInput() {
    const input = DomBuilder.el("input", "field-input");
    input.type = "text";
    input.value = String(Math.round(this._currentCop));
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
      const value = AmountParser.parse(this._inputEl.value);
      this._settle(value);
    } catch (err) {
      this._errorEl.textContent = err.message;
    }
  }

  _maybeSubmitOnEnter(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      this._confirm();
    }
  }

  _focusInput() {
    if (this._inputEl) {
      this._inputEl.focus();
      this._inputEl.select();
    }
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
