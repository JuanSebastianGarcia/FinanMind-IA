import { DomBuilder } from "../../core/dom_builder.js";

export class AutomationDialog {
  /** Collects the Gmail account + app password used to automate NU expense processing. */
  constructor(modalHost, state) {
    this._host = modalHost;
    this._state = state || { configured: false, email: "" };
    this._resolver = null;
    this._emailEl = null;
    this._passwordEl = null;
    this._errorEl = null;
    this._saveBtn = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      window.queueMicrotask(() => this._focusEmail());
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Automatizar procesamiento (NU)"));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(DomBuilder.el(
      "div",
      "modal__hint",
      "Se conecta por IMAP a tu correo de Gmail para leer las notificaciones de gastos de NU. "
        + "Usa una clave de aplicación de Google, no tu contraseña normal.",
    ));
    if (this._state.configured) {
      body.appendChild(DomBuilder.el("div", "modal__hint", `Actualmente conectado como ${this._state.email}.`));
    }
    body.appendChild(this._buildEmailField());
    body.appendChild(this._buildPasswordField());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildEmailField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Correo de Gmail"));
    this._emailEl = this._buildInput("email", this._state.email || "");
    wrap.appendChild(this._emailEl);
    return wrap;
  }

  _buildPasswordField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Clave de aplicación"));
    this._passwordEl = this._buildInput("password", "");
    wrap.appendChild(this._passwordEl);
    return wrap;
  }

  _buildInput(type, value) {
    const input = DomBuilder.el("input", "field-input");
    input.type = type;
    input.value = value;
    input.autocomplete = "off";
    input.addEventListener("keydown", (event) => this._maybeSubmitOnEnter(event));
    return input;
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    if (this._state.configured) {
      actions.appendChild(DomBuilder.button("btn btn--danger", "Desconectar", () => this._settle({ disconnect: true })));
    }
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cancelar", () => this._settle(null)));
    this._saveBtn = DomBuilder.button("btn btn--primary", "Conectar", () => this._confirm());
    actions.appendChild(this._saveBtn);
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
    const email = (this._emailEl.value || "").trim();
    if (email === "") throw new Error("El correo es obligatorio.");
    const appPassword = (this._passwordEl.value || "").trim();
    if (appPassword === "") throw new Error("La clave de aplicación es obligatoria.");
    return { email, appPassword };
  }

  _maybeSubmitOnEnter(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      this._confirm();
    }
  }

  _focusEmail() {
    if (this._emailEl) this._emailEl.focus();
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
