import { DomBuilder } from "../../core/dom_builder.js";

export class InvestmentReviewRuleEditorDialog {
  /** Collects a free-form personal rule (multi-line); returns the trimmed text. */
  constructor(modalHost, titleText, seedText) {
    this._host = modalHost;
    this._titleText = titleText;
    this._seed = seedText || "";
    this._resolver = null;
    this._textareaEl = null;
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
    const modal = DomBuilder.el("div", "modal modal--wide");
    modal.appendChild(DomBuilder.el("div", "modal__title", this._titleText));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildHint());
    body.appendChild(this._buildTextarea());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildHint() {
    return DomBuilder.el(
      "div",
      "modal__field-label",
      "Escribe una regla, preferencia o dato personal. La IA tendrá esto en cuenta al solicitar un análisis.",
    );
  }

  _buildTextarea() {
    this._textareaEl = DomBuilder.el("textarea", "field-textarea");
    this._textareaEl.value = this._seed;
    this._textareaEl.style.minHeight = "180px";
    return this._textareaEl;
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cancelar", () => this._settle(null)));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Guardar", () => this._confirm()));
    return actions;
  }

  _confirm() {
    const value = (this._textareaEl.value || "").trim();
    if (value === "") {
      this._errorEl.textContent = "La regla no puede estar vacía.";
      return;
    }
    this._settle(value);
  }

  _focusInput() {
    if (this._textareaEl) this._textareaEl.focus();
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
