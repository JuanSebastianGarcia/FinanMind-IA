import { DomBuilder } from "../../core/dom_builder.js";

export class PdfPasswordDialog {
  /** Asks once for the password shared by all NU statement PDFs. */
  constructor(modalHost) {
    this._host = modalHost;
    this._resolver = null;
    this._passwordEl = null;
    this._errorEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      window.queueMicrotask(() => this._focusPassword());
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Contraseña de los extractos"));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(DomBuilder.el(
      "div",
      "modal__hint",
      "NU protege el PDF de cada extracto con la misma contraseña. Ingrésala una vez; "
        + "se guardará de forma cifrada en este equipo para que no tengas que volver a escribirla.",
    ));
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Contraseña del PDF"));
    this._passwordEl = DomBuilder.el("input", "field-input");
    this._passwordEl.type = "password";
    this._passwordEl.autocomplete = "off";
    this._passwordEl.addEventListener("keydown", (event) => this._maybeSubmitOnEnter(event));
    wrap.appendChild(this._passwordEl);
    body.appendChild(wrap);
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cancelar", () => this._settle(null)));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Continuar", () => this._confirm()));
    return actions;
  }

  _confirm() {
    const password = (this._passwordEl.value || "").trim();
    if (password === "") {
      this._errorEl.textContent = "La contraseña es obligatoria.";
      return;
    }
    this._settle(password);
  }

  _maybeSubmitOnEnter(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      this._confirm();
    }
  }

  _focusPassword() {
    if (this._passwordEl) this._passwordEl.focus();
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
