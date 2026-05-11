import { DomBuilder } from "../../core/dom_builder.js";

export class InvestmentCategoryEditorDialog {
  /** Collects a single category name (trimmed) and resolves to the string. */
  constructor(modalHost, titleText, seedName) {
    this._host = modalHost;
    this._titleText = titleText;
    this._seed = seedName || "";
    this._resolver = null;
    this._inputEl = null;
    this._errorEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      window.queueMicrotask(() => this._focusInput());
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", this._titleText));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Nombre"));
    this._inputEl = this._buildInput();
    wrap.appendChild(this._inputEl);
    body.appendChild(wrap);
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildInput() {
    const input = DomBuilder.el("input", "field-input");
    input.type = "text";
    input.value = this._seed;
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
    const value = (this._inputEl.value || "").trim();
    if (value === "") {
      this._errorEl.textContent = "El nombre es obligatorio.";
      return;
    }
    this._settle(value);
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
